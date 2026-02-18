# -*- coding: utf-8 -*-
"""
Planarization of Geometry
"""


from abc import ABCMeta, abstractmethod
from collections import defaultdict
from functools import cache, cached_property
from typing import Optional, TYPE_CHECKING

from fudgeo import MemoryGeoPackage
from fudgeo.constant import COMMA_SPACE, FETCH_SIZE
from fudgeo.context import ExecuteMany
from fudgeo.enumeration import ShapeType
from numpy import array, concatenate
from shapely import GeometryCollection
from shapely.constructive import point_on_surface
from shapely.linear import line_interpolate_point
from shapely.strtree import STRtree
from shapely.set_operations import union_all

from spyops.environment.core import zm_config
from spyops.environment.util import tolerance_scale_factor
from spyops.geometry.config import geometry_config
from spyops.geometry.util import get_geoms_iter, to_shapely
from spyops.geometry.wa import polygonize
from spyops.query.base import AbstractSpatialAttribute
from spyops.shared.constant import EMPTY
from spyops.shared.element import create_feature_class
from spyops.shared.enumeration import AttributeOption
from spyops.shared.field import (
    get_geometry_column_name, make_field_names, validate_fields)
from spyops.shared.hint import ELEMENT, FIELDS, XY_TOL
from spyops.shared.util import element_names, make_unique_name
from spyops.shared.records import extend_records


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, Field
    from numpy import ndarray
    from shapely import LineString, Polygon


def planarize_factory(source: 'FeatureClass', operator: 'FeatureClass',
                      use_full_extent: bool, xy_tolerance: XY_TOL) \
        -> tuple['FeatureClass', 'Field', 'FeatureClass', 'Field']:
    """
    Planarize Feature Class Factory
    """
    polygons = ShapeType.polygon, ShapeType.multi_polygon
    if source.shape_type in polygons:
        src_cls = PlanarizePolygonSource
    else:
        src_cls = PlanarizeGeneralSource
    if operator.shape_type in polygons:
        op_cls = PlanarizePolygonOperator
    else:
        op_cls = PlanarizeGeneralOperator
    source, source_fid = src_cls(
        source, operator=operator, use_full_extent=use_full_extent,
        xy_tolerance=xy_tolerance)()
    operator, operator_fid = op_cls(
        source, operator=operator, use_full_extent=use_full_extent,
        xy_tolerance=xy_tolerance)()
    return source, source_fid, operator, operator_fid
# End planarize_factory function


def clean_factory(source: 'FeatureClass', operator: 'FeatureClass',
                  use_full_extent: bool, xy_tolerance: XY_TOL) \
        -> tuple['FeatureClass', 'Field', 'FeatureClass', 'Field']:
    """
    Coverage-like Clean and Build Planarization Factory
    """
    polygons = ShapeType.polygon, ShapeType.multi_polygon
    lines = ShapeType.linestring, ShapeType.multi_linestring
    if source.shape_type in polygons:
        src_cls = PlanarizePolygonSource
    elif source.shape_type in lines:
        src_cls = PlanarizeLineStringSource
    else:
        src_cls = PlanarizePointSource
    if operator.shape_type in polygons:
        op_cls = PlanarizePolygonOperator
    elif operator.shape_type in lines:
        op_cls = PlanarizeLineStringOperator
    else:
        op_cls = PlanarizePointOperator
    source, source_fid = src_cls(
        source, operator=operator, use_full_extent=use_full_extent,
        xy_tolerance=xy_tolerance)()
    operator, operator_fid = op_cls(
        source, operator=operator, use_full_extent=use_full_extent,
        xy_tolerance=xy_tolerance)()
    return source, source_fid, operator, operator_fid
# End clean_factory function


class AbstractPlanarize(AbstractSpatialAttribute, metaclass=ABCMeta):
    """
    Abstract Base Class for Planarizing Feature Classes
    """
    def __init__(self, source: 'FeatureClass', operator: 'FeatureClass', *,
                 use_full_extent: bool, xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractPlanarize class
        """
        super().__init__(
            source=source, operator=operator, target=None,
            attribute_option=AttributeOption.ALL, xy_tolerance=xy_tolerance)
        self._use_full_extent: bool = use_full_extent
        self._distance_element: Optional['FeatureClass'] = None
    # End init built-in

    @abstractmethod
    def __call__(self) -> tuple['FeatureClass', 'Field']:  # pragma: no cover
        """
        Make Class Callable
        """
        pass
    # End call built-in

    @staticmethod
    @abstractmethod
    def _make_planarized_geometry(geoms: 'ndarray') -> list:
        """
        Make Planarized Geometry
        """
        pass
    # End _make_planarized_geometry method

    @property
    @abstractmethod
    def _shape_type(self) -> str:  # pragma: no cover
        """
        Shape Type
        """
        pass
    # End _shape_type property

    @property
    @abstractmethod
    def temporary_fid_field(self) -> 'Field':  # pragma: no cover
        """
        Temporary FID Field
        """
        pass
    # End temporary_fid_field property

    def _make_insert_sql(self, planar: 'FeatureClass', fields: FIELDS) -> str:
        """
        Make Insert SQL for the Planar Feature Class
        """
        field_names = make_field_names(fields)
        geom_name = get_geometry_column_name(planar)
        field_names = self._concatenate(geom_name, field_names)
        return self._make_insert(
            planar.escaped_name, field_names=field_names,
            field_count=len(fields) + 1)
    # End _make_insert_sql method

    def _save_planarized(self, feature_class: 'FeatureClass',
                         results: list[tuple]) -> 'FeatureClass':
        """
        Save Planarized Feature Class
        """
        records = []
        zm = zm_config(self.source, self.operator)
        fields = [self.temporary_fid_field, *self._get_fields(feature_class)]
        planar = self._make_planar_feature_class(feature_class, fields=fields)
        config = geometry_config(planar, cast_geom=zm.is_different)
        extend_records(results=results, records=records, config=config)
        insert_sql = self._make_insert_sql(planar, fields=fields)
        with (planar.geopackage.connection as cout,
              ExecuteMany(connection=cout, table=planar) as executor):
            executor(sql=insert_sql, data=records)
        return planar
    # End _save_planarized method

    def _get_fields(self, element: ELEMENT) -> FIELDS:
        """
        Get Fields from Element based on Attribute Option
        """
        return validate_fields(element, fields=element.fields)
    # End _get_fields method

    @staticmethod
    def _fetch_features(feature_class: 'FeatureClass', sql: str) \
            -> tuple['ndarray', list[tuple]]:
        """
        Fetch Features, return shapely geometries and attributes, stay in
        the original spatial reference system.
        """
        geoms = []
        attributes = []
        with feature_class.geopackage.connection as cin:
            cursor = cin.execute(sql)
            while features := cursor.fetchmany(FETCH_SIZE):
                features, geometries = to_shapely(features, transformer=None)
                attributes.extend([feature[1:] for feature in features])
                geoms.append(geometries)
        return concatenate(geoms), attributes
    # End _fetch_features method

    def _planarize(self, feature_class: 'FeatureClass',
                   sql: str) -> 'FeatureClass':
        """
        Planarized Feature Class
        """
        geoms, attributes = self._fetch_features(feature_class, sql=sql)
        planarized = self._make_planarized_geometry(geoms)
        results = self._build_planar_results(
            planarized, geoms=geoms, attributes=attributes)
        return self._save_planarized(feature_class, results=results)
    # End _planarize method

    def _build_planar_results(self, planarized: list, geoms: 'ndarray',
                              attributes: list[tuple]) -> list[tuple]:
        """
        Build Planar Results
        """
        grouper = self._index_overlay(geoms, planarized)
        results = []
        for orig_idx, indexes in grouper.items():
            attrs = attributes[orig_idx]
            results.extend([(planarized[idx], attrs) for idx in indexes])
        return results
    # End _build_planar_results method

    def _index_overlay(self, geoms: 'ndarray', planarized: list) \
            -> defaultdict[int, list[int]]:
        """
        Index Based Overlay returning dictionary of intersected features
        grouped by index of original geometries.
        """
        tree = STRtree(geoms)
        intersects = self._get_intersections(tree, planarized)
        grouper = defaultdict(list)
        for plan_idx, orig_idx in intersects.T.tolist():
            grouper[orig_idx].append(plan_idx)
        return grouper
    # End _index_overlay method

    @abstractmethod
    def _get_intersections(self, tree: STRtree, planarized: list) -> 'ndarray':
        """
        Get Intersections
        """
        pass
    # End _get_intersections method

    def _make_planar_feature_class(self, feature_class: 'FeatureClass',
                                   fields: FIELDS) -> 'FeatureClass':
        """
        Make Planar Feature Class
        """
        names = element_names(self.scratch)
        name = make_unique_name(feature_class.name, names)
        return create_feature_class(
            geopackage=self.scratch, name=name, shape_type=self._shape_type,
            srs=feature_class.spatial_reference_system, fields=fields,
            z_enabled=feature_class.has_z, m_enabled=feature_class.has_m,
            override_zm=True)
    # End _make_planar_feature_class method

    @cache
    def _field_names_and_count(self, element: ELEMENT) -> tuple[int, str, str]:
        """
        Override field names for Selection -- ignore insert names and count
        """
        fields = self._get_fields(element)
        select_names = make_field_names(fields)
        geom_type = get_geometry_column_name(element, include_geom_type=True)
        alias = self.temporary_fid_field.escaped_name
        primary = f'{element.primary_key_field.escaped_name} AS {alias}'
        geom_primary = f'{geom_type}{COMMA_SPACE}{primary}'
        return 0, EMPTY, self._concatenate(geom_primary, select_names)
    # End _field_names_and_count method

    @cached_property
    def scratch(self) -> MemoryGeoPackage:
        """
        Scratch GeoPackage
        """
        return MemoryGeoPackage.create()
    # End scratch property

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        if self._use_full_extent:
            return self._make_full_query(self.source)
        return super().select
    # End select property

    @property
    def select_operator(self) -> str:
        """
        Selection Query for Operator
        """
        if self._use_full_extent:
            return self._make_full_query(self.operator)
        return super().select_operator
    # End select_operator property
# End AbstractPlanarize class


class AbstractPlanarizePolygon(AbstractPlanarize, metaclass=ABCMeta):
    """
    Abstract Class for Planarizing a Polygon Feature Class
    """
    def _get_intersections(self, tree: STRtree, planarized: list) -> 'ndarray':
        """
        Get Intersections
        """
        points = point_on_surface(planarized)
        return tree.query(points, predicate='intersects')
    # End _get_intersections method

    @property
    def _shape_type(self) -> str:
        """
        Shape Type
        """
        return ShapeType.polygon
    # End _shape_type property

    @staticmethod
    def _make_planarized_geometry(geoms: 'ndarray') -> list['Polygon']:
        """
        Make Planarized Geometry
        """
        lines = union_all([geom.boundary for geom in geoms])
        lines = get_geoms_iter(lines)
        collections = polygonize(lines)
        if isinstance(collections, GeometryCollection):
            collections = [collections]
        planarized = []
        for collection in collections:
            planarized.extend(get_geoms_iter(collection))
        return planarized
    # End _make_planarized_geometry method
# End AbstractPlanarizePolygon class


class PlanarizeSourceMixin:
    """
    Planarize Source Mixin
    """
    def __call__(self) -> tuple['FeatureClass', 'Field']:
        """
        Make Class Callable
        """
        # noinspection PyUnresolvedReferences
        element = self.source
        self._distance_element = element
        fid = element.primary_key_field
        # noinspection PyUnresolvedReferences
        return self._planarize(element, sql=self.select), fid
    # End call built-in

    @property
    def temporary_fid_field(self) -> 'Field':
        """
        Temporary FID Field
        """
        # noinspection PyUnresolvedReferences
        return self.output_fid_source
    # End temporary_fid_field property
# End PlanarizeSourceMixin class


class PlanarizeOperatorMixin:
    """
    Planarize Operator Mixin
    """
    def __call__(self) -> tuple['FeatureClass', 'Field']:
        """
        Make Class Callable
        """
        # noinspection PyUnresolvedReferences
        element = self.operator
        self._distance_element = element
        fid = element.primary_key_field
        # noinspection PyUnresolvedReferences
        return self._planarize(element, sql=self.select_operator), fid
    # End call built-in

    @property
    def temporary_fid_field(self) -> 'Field':
        """
        Temporary FID Field
        """
        # noinspection PyUnresolvedReferences
        return self.output_fid_operator
    # End temporary_fid_field property
# End PlanarizeOperatorMixin class


class PlanarizePolygonSource(PlanarizeSourceMixin, AbstractPlanarizePolygon):
    """
    Planarize a source polygon feature class
    """
# End PlanarizePolygonSource class


class PlanarizePolygonOperator(PlanarizeOperatorMixin,
                               AbstractPlanarizePolygon):
    """
    Planarize an operator polygon feature class
    """
# End PlanarizePolygonOperator class


class AbstractPlanarizeLineString(AbstractPlanarize, metaclass=ABCMeta):
    """
    Abstract Class for Planarizing a LineString Feature Class
    """
    def _get_intersections(self, tree: STRtree, planarized: list) -> 'ndarray':
        """
        Get Intersections
        """
        micro = 10 ** -6
        distance = tolerance_scale_factor(self._element) * micro
        points = line_interpolate_point(
            planarized, distance=0.5, normalized=True)
        return tree.query(points, predicate='dwithin', distance=distance)
    # End _get_intersections method

    @property
    def _shape_type(self) -> str:
        """
        Shape Type
        """
        return ShapeType.linestring
    # End _shape_type property

    @staticmethod
    def _make_planarized_geometry(geoms: 'ndarray') -> list['LineString']:
        """
        Make Planarized Geometry
        """
        return list(get_geoms_iter(union_all(geoms)))
    # End _make_planarized_geometry method
# End AbstractPlanarizeLineString class


class PlanarizeLineStringSource(PlanarizeSourceMixin,
                                AbstractPlanarizeLineString):
    """
    Planarize a source LineString feature class
    """
# End PlanarizeLineStringSource class


class PlanarizeLineStringOperator(PlanarizeOperatorMixin,
                                  AbstractPlanarizeLineString):
    """
    Planarize an operator LineString feature class
    """
# End PlanarizeLineStringOperator class


class AbstractPlanarizeGeneral(AbstractPlanarize, metaclass=ABCMeta):
    """
    Abstract Class for Planarizing a Point Feature Class
    """
    def _planarize(self, feature_class: 'FeatureClass',
                   sql: str) -> 'FeatureClass':
        """
        Planarized Feature Class
        """
        geoms, attributes = self._fetch_features(feature_class, sql=sql)
        results = list(zip(geoms, attributes))
        return self._save_planarized(feature_class, results=results)
    # End _planarize method

    def _get_intersections(self, tree: STRtree, planarized: list) -> 'ndarray':
        """
        Get Intersections
        """
        return array([], dtype=int)
    # End _get_intersections method

    @staticmethod
    def _make_planarized_geometry(geoms: 'ndarray') -> list:
        """
        Make Planarized Geometry
        """
        return []
    # End _make_planarized_geometry method
# End AbstractPlanarizeGeneral class


class PlanarizeGeneralSource(AbstractPlanarizeGeneral):
    """
    Planarize a source feature class -- handling for FID
    """
    def __call__(self) -> tuple['FeatureClass', 'Field']:
        """
        Make Class Callable
        """
        fid = self.source.primary_key_field
        return self._planarize(self.source, sql=self.select), fid
    # End call built-in

    @property
    def _shape_type(self) -> str:
        """
        Shape Type
        """
        return self.source.shape_type
    # End _shape_type property

    @property
    def temporary_fid_field(self) -> 'Field':
        """
        Temporary FID Field
        """
        return self.output_fid_source
    # End temporary_fid_field property
# End PlanarizeGeneralSource class


class PlanarizeGeneralOperator(AbstractPlanarizeGeneral):
    """
    Planarize an operator feature class -- handling for FID
    """
    def __call__(self) -> tuple['FeatureClass', 'Field']:
        """
        Make Class Callable
        """
        fid = self.operator.primary_key_field
        return self._planarize(self.operator, sql=self.select_operator), fid
    # End call built-in

    @property
    def _shape_type(self) -> str:
        """
        Shape Type
        """
        return self.operator.shape_type
    # End _shape_type property

    @property
    def temporary_fid_field(self) -> 'Field':
        """
        Temporary FID Field
        """
        return self.output_fid_operator
    # End temporary_fid_field property
# End PlanarizeGeneralOperator class


class PlanarizePointSource(PlanarizeGeneralSource):
    """
    Planarize a source Point feature class -- handling for FID
    """
# End PlanarizePointSource class


class PlanarizePointOperator(PlanarizeGeneralOperator):
    """
    Planarize a operator Point feature class -- handling for FID
    """
# End PlanarizePointOperator class


if __name__ == '__main__':  # pragma: no cover
    pass
