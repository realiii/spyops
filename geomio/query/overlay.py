# -*- coding: utf-8 -*-
"""
Query Classes for analysis.overlay module
"""


from abc import ABCMeta, abstractmethod
from collections import defaultdict
from functools import cache, cached_property

from fudgeo import FeatureClass, Field, MemoryGeoPackage
from fudgeo.constant import COMMA_SPACE, FETCH_SIZE
from fudgeo.enumeration import GeometryType

from shapely import GeometryCollection, Polygon as ShapelyPolygon, STRtree
from shapely.constructive import polygonize
from shapely.io import from_wkb
from shapely.set_operations import union_all

from geomio.query.base import AbstractSpatialAttribute
from geomio.query.extract import QueryClip
from geomio.shared.constant import EMPTY, GEOMS_ATTR
from geomio.shared.field import (
    get_geometry_column_name, make_field_names, validate_fields)
from geomio.shared.geometry import overlay_config
from geomio.shared.hint import ELEMENT, FIELDS, POLYGONS
from geomio.shared.element import create_feature_class
from geomio.shared.enumeration import AttributeOption
from geomio.shared.util import element_names, extend_records, make_unique_name


class QueryErase(QueryClip):
    """
    Queries for Erase
    """
# End QueryErase class


class QueryIntersectPairwise(AbstractSpatialAttribute):
    """
    Queries for Intersect (Pairwise)
    """
# End QueryIntersectPairwise class


class AbstractPlanarizeFeatureClass(AbstractSpatialAttribute, metaclass=ABCMeta):
    """
    Base Class for Planarizing Feature Class
    """
    def __init__(self, source: FeatureClass, operator: FeatureClass) -> None:
        """
        Initialize the BasePlanarizeFeatureClass class
        """
        super().__init__(source=source, operator=operator, target=None,
                         attribute_option=AttributeOption.ALL)
    # End init built-in

    @abstractmethod
    def __call__(self) -> FeatureClass:
        """
        Make Class Callable
        """
        pass
    # End call built-in

    @cached_property
    def scratch(self) -> MemoryGeoPackage:
        """
        Scratch GeoPackage
        """
        return MemoryGeoPackage.create()
    # End scratch property

    def _planarize(self, feature_class: FeatureClass, sql: str) -> FeatureClass:
        """
        Planarized Feature Class
        """
        geoms, attributes = self._fetch_features(feature_class, sql=sql)
        planarized = self._make_planarized_geometry(geoms)
        results = self._build_planar_results(
            planarized, geoms=geoms, attributes=attributes)
        return self._save_planarized(feature_class, results=results)
    # End _planarize method

    @staticmethod
    def _build_planar_results(planarized: list[ShapelyPolygon], geoms: POLYGONS,
                              attributes: list[tuple]) -> list[tuple]:
        """
        Build Planar Results
        """
        tree = STRtree(geoms)
        points = [p.representative_point() for p in planarized]
        intersects = tree.query(points, predicate='intersects')
        grouper = defaultdict(list)
        for plan_idx, orig_idx in intersects.T.tolist():
            grouper[orig_idx].append(plan_idx)
        results = []
        for orig_idx, indexes in grouper.items():
            attrs = attributes[orig_idx]
            results.extend([(planarized[idx], attrs) for idx in indexes])
        return results
    # End _build_planar_results method

    def _make_insert_sql(self, planar: FeatureClass, fields: FIELDS) -> str:
        """
        Make Insert SQL for the Planar Feature Class
        """
        field_names = make_field_names(fields)
        geom_name = get_geometry_column_name(planar)
        field_names = f'{geom_name}{COMMA_SPACE}{field_names}'
        return self._make_insert(
            planar.escaped_name, field_names=field_names,
            field_count=len(fields) + 1)
    # End _make_insert_sql method

    @property
    @abstractmethod
    def temporary_fid_field(self) -> Field:
        """
        Temporary FID Field
        """
        pass
    # End temporary_fid_field property

    def _save_planarized(self, feature_class: FeatureClass,
                         results: list[tuple]) -> FeatureClass:
        """
        Save Planarized Feature Class
        """
        records = []
        fields = [self.temporary_fid_field, *self._get_fields(feature_class)]
        planar = self._make_planar_feature_class(feature_class, fields)
        config = overlay_config(planar, target=planar, operator=None)
        extend_records(results=results, records=records, config=config)
        sql = self._make_insert_sql(planar, fields=fields)
        with planar.geopackage.connection as cout:
            cout.executemany(sql, records)
        return planar
    # End _save_planarized method

    def _get_fields(self, element: ELEMENT) -> FIELDS:
        """
        Get Fields from Element based on Attribute Option
        """
        return validate_fields(element, fields=element.fields)
    # End _get_fields method

    @staticmethod
    def _make_planarized_geometry(geoms: POLYGONS) -> list[ShapelyPolygon]:
        """
        Make Planarized Geometry
        """
        rings = []
        for geom in geoms:
            polygons = getattr(geom, GEOMS_ATTR, [geom])
            for polygon in polygons:
                rings.append(polygon.exterior)
                rings.extend(polygon.interiors)
        lines = union_all(rings)
        lines = getattr(lines, GEOMS_ATTR, [lines])
        collections = polygonize(lines)
        if isinstance(collections, GeometryCollection):
            collections = [collections]
        planarized = []
        for collection in collections:
            planarized.extend(getattr(collection, GEOMS_ATTR, [collection]))
        return planarized
    # End _make_planarized_geometry method

    @staticmethod
    def _fetch_features(feature_class: FeatureClass, sql: str) \
            -> tuple[POLYGONS, list[tuple]]:
        """
        Fetch Features, return shapely geometries and attributes
        """
        geoms = []
        attributes = []
        with feature_class.geopackage.connection as cin:
            cursor = cin.execute(sql)
            while features := cursor.fetchmany(FETCH_SIZE):
                attributes.extend([feature[1:] for feature in features])
                geoms.extend([from_wkb(g.wkb) for g, *_ in features])
        return geoms, attributes
    # End _fetch_features method

    def _make_planar_feature_class(self, feature_class: FeatureClass,
                                   fields: FIELDS) -> FeatureClass:
        """
        Make Planar Feature Class
        """
        names = element_names(self.scratch)
        name = make_unique_name(feature_class.name, names)
        return create_feature_class(
            geopackage=self.scratch, name=name, shape_type=GeometryType.polygon,
            srs=feature_class.spatial_reference_system, fields=fields,
            z_enabled=feature_class.has_z, m_enabled=feature_class.has_m)
    # End _make_planar_feature_class method

    @cache
    def _field_names_and_count(self, element: ELEMENT) -> tuple[int, str, str]:
        """
        Override field names for Selection -- ignore insert names and count
        """
        fields = self._get_fields(element)
        geom_type = get_geometry_column_name(element, include_geom_type=True)
        select_field_names = make_field_names(fields)
        alias = self.temporary_fid_field.escaped_name
        primary = f'{element.primary_key_field.escaped_name} AS {alias}'
        primary = f'{COMMA_SPACE}{primary}'
        return 0, EMPTY, f'{geom_type}{primary}{COMMA_SPACE}{select_field_names}'
    # End _field_names_and_count method
# End AbstractPlanarizeFeatureClass class


class PlanarizeSource(AbstractPlanarizeFeatureClass):
    """
    Planarize a source feature class
    """
    def __call__(self) -> FeatureClass:
        """
        Make Class Callable
        """
        return self._planarize(self.source, sql=self.select)
    # End call built-in

    @property
    def temporary_fid_field(self) -> Field:
        """
        Temporary FID Field
        """
        return self.output_fid_source
    # End temporary_fid_field property
# End PlanarizeSource class


class PlanarizeOperator(AbstractPlanarizeFeatureClass):
    """
    Planarize an operator feature class
    """
    def __call__(self) -> FeatureClass:
        """
        Make Class Callable
        """
        return self._planarize(self.operator, sql=self.select_operator)
    # End call built-in

    @property
    def temporary_fid_field(self) -> Field:
        """
        Temporary FID Field
        """
        return self.output_fid_operator
    # End temporary_fid_field property
# End PlanarizeOperator class


class QueryIntersectClassic(AbstractSpatialAttribute):
    """
    Queries for Intersect (Classic)
    """
    def __init__(self, source: FeatureClass, target: FeatureClass,
                 operator: FeatureClass,
                 attribute_option: AttributeOption) -> None:
        """
        Initialize the AbstractSpatialAttribute class
        """
        super().__init__(source=source, target=target, operator=operator,
                         attribute_option=attribute_option)
        self._source_planar = PlanarizeSource(source, operator=operator)
        self._operator_planar = PlanarizeOperator(source, operator=operator)
        self._element = self._source_planar()
        self._operator = self._operator_planar()
    # End init built-in

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields and Rename Primary Key Columns if included
        """
        if self._attr_option == AttributeOption.ALL:
            _, *src_fields = self._get_fields(self.source)
            _, *op_fields = self._get_fields(self.operator)
            op_fields = self._make_unique_fields(src_fields, op_fields)
            return [*src_fields, *op_fields]
        elif self._attr_option == AttributeOption.ONLY_FID:
            return self.output_fid_source, self.output_fid_operator
        else:
            _, *src_fields = self._get_fields(self.source)
            _, *op_fields = self._get_fields(self.operator)
            op_fields = self._make_unique_fields(src_fields, op_fields)
            return [*src_fields, *op_fields]
    # End _get_unique_fields method

    @cache
    def _field_names_and_count(self, element: ELEMENT) -> tuple[int, str, str]:
        """
        Override field names for Selection -- ignore insert names and count
        """
        fields = self._get_fields(element)
        if self._attr_option in (AttributeOption.ALL, AttributeOption.SANS_FID):
            _, *fields = fields
        geom_type = get_geometry_column_name(element, include_geom_type=True)
        select_field_names = make_field_names(fields)
        return 0, EMPTY, f'{geom_type}{COMMA_SPACE}{select_field_names}'
    # End _field_names_and_count method
# End QueryIntersectClassic class


if __name__ == '__main__':  # pragma: no cover
    pass
