# -*- coding: utf-8 -*-
"""
Query Classes for analysis.overlay module
"""


from abc import ABCMeta, abstractmethod
from collections import defaultdict
from functools import cache, cached_property
from typing import TYPE_CHECKING

from fudgeo import MemoryGeoPackage
from fudgeo.constant import COMMA_SPACE, FETCH_SIZE
from fudgeo.context import ExecuteMany
from fudgeo.enumeration import ShapeType
from numpy import concat
from shapely import GeometryCollection
from shapely.strtree import STRtree
from shapely.set_operations import union_all

from spyops.environment.core import zm_config
from spyops.geometry.config import geometry_config
from spyops.geometry.util import get_geoms_iter, keep_valid, to_shapely
from spyops.geometry.wa import polygonize
from spyops.query.base import AbstractSpatialAttribute
from spyops.query.analysis.extract import QueryClip
from spyops.shared.base import QueryConfig
from spyops.shared.constant import EMPTY
from spyops.shared.element import create_feature_class
from spyops.shared.enumeration import AttributeOption, OutputTypeOption
from spyops.shared.field import (
    get_geometry_column_name, make_field_names, make_unique_fields,
    validate_fields)
from spyops.shared.hint import ELEMENT, FIELDS, POLYGONS, XY_TOL
from spyops.shared.util import element_names, make_unique_name
from spyops.shared.records import extend_records, process_disjoint


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, Field
    from numpy import ndarray
    from shapely import Polygon


class QueryErase(QueryClip):
    """
    Queries for Erase
    """
    def process_disjoint(self, xy_tolerance: XY_TOL) -> None:
        """
        Process Disjoint
        """
        query = QueryConfig(
            source=self.source, target=self.target,
            disjoint=self.select_disjoint, insert=self.insert,
            config=self.geometry_config, transformer=self.source_transformer)
        process_disjoint(query=query, xy_tolerance=xy_tolerance)
    # End process_disjoint method
# End QueryErase class


def _planarize_factory(source: 'FeatureClass', operator: 'FeatureClass',
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
# End _planarize_factory function


class AbstractPlanarize(AbstractSpatialAttribute, metaclass=ABCMeta):
    """
    Abstract Base Class for Planarizing Feature Classes
    """
    def __init__(self, source: 'FeatureClass', operator: 'FeatureClass',
                 *, use_full_extent: bool, xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractPlanarize class
        """
        super().__init__(
            source=source, operator=operator, target=None,
            attribute_option=AttributeOption.ALL, xy_tolerance=xy_tolerance)
        self._use_full_extent: bool = use_full_extent
    # End init built-in

    @abstractmethod
    def __call__(self) -> tuple['FeatureClass', 'Field']:  # pragma: no cover
        """
        Make Class Callable
        """
        pass
    # End call built-in

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

    @abstractmethod
    def _planarize(self, feature_class: 'FeatureClass', sql: str) -> 'FeatureClass':  # pragma: no cover
        """
        Planarized Feature Class
        """
        pass
    # End _planarize method

    @cached_property
    def scratch(self) -> MemoryGeoPackage:
        """
        Scratch GeoPackage
        """
        return MemoryGeoPackage.create()
    # End scratch property

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
        Fetch Features, return shapely geometries and attributes
        """
        geoms = []
        attributes = []
        with feature_class.geopackage.connection as cin:
            cursor = cin.execute(sql)
            while features := cursor.fetchmany(FETCH_SIZE):
                geometries, validity = to_shapely(features)
                features, geometries = keep_valid(
                    features, geometries=geometries, validity=validity)
                attributes.extend([feature[1:] for feature in features])
                geoms.append(geometries)
        return concat(geoms), attributes
    # End _fetch_features method

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
    @property
    def _shape_type(self) -> str:
        """
        Shape Type
        """
        return ShapeType.polygon
    # End _shape_type property

    def _planarize(self, feature_class: 'FeatureClass', sql: str) -> 'FeatureClass':
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
    def _build_planar_results(planarized: list['Polygon'], geoms: POLYGONS,
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

    @staticmethod
    def _make_planarized_geometry(geoms: POLYGONS) -> list['Polygon']:
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


class PlanarizePolygonSource(AbstractPlanarizePolygon):
    """
    Planarize a source polygon feature class
    """
    def __call__(self) -> tuple['FeatureClass', 'Field']:
        """
        Make Class Callable
        """
        fid = self.source.primary_key_field
        return self._planarize(self.source, sql=self.select), fid
    # End call built-in

    @property
    def temporary_fid_field(self) -> 'Field':
        """
        Temporary FID Field
        """
        return self.output_fid_source
    # End temporary_fid_field property
# End PlanarizePolygonSource class


class PlanarizePolygonOperator(AbstractPlanarizePolygon):
    """
    Planarize an operator polygon feature class
    """
    def __call__(self) -> tuple['FeatureClass', 'Field']:
        """
        Make Class Callable
        """
        fid = self.operator.primary_key_field
        return self._planarize(self.operator, sql=self.select_operator), fid
    # End call built-in

    @property
    def temporary_fid_field(self) -> 'Field':
        """
        Temporary FID Field
        """
        return self.output_fid_operator
    # End temporary_fid_field property
# End PlanarizePolygonOperator class


class AbstractPlanarizeGeneral(AbstractPlanarize, metaclass=ABCMeta):
    """
    Abstract Class for Planarizing a LineString or Point Feature Class
    """
    def _planarize(self, feature_class: 'FeatureClass', sql: str) -> 'FeatureClass':
        """
        Planarized Feature Class
        """
        geoms, attributes = self._fetch_features(feature_class, sql=sql)
        results = list(zip(geoms, attributes))
        return self._save_planarized(feature_class, results=results)
    # End _planarize method
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


class ClassicMixin:
    """
    Mixin for Shared Classic Capabilities
    """
    # noinspection PyUnresolvedReferences
    @property
    def input_fid_source(self) -> 'Field':
        """
        Input FID for Source
        """
        return self._input_fid_source
    # End input_fid_source property

    # noinspection PyUnresolvedReferences
    @property
    def input_fid_operator(self) -> 'Field':
        """
        Input FID for Operator
        """
        return self._input_fid_operator
    # End input_fid_operator property

    # noinspection PyUnresolvedReferences
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields and Rename Primary Key Columns if included
        """
        if self._attr_option == AttributeOption.ALL:
            src_fields = self._get_fields(self.source)[1:]
            op_fields = self._get_fields(self.operator)[1:]
            op_fields = make_unique_fields(src_fields, op_fields)
            return [*src_fields, *op_fields]
        elif self._attr_option == AttributeOption.ONLY_FID:
            return self.output_fid_source, self.output_fid_operator
        else:
            src_fields = self._get_fields(self.source)[1:]
            op_fields = self._get_fields(self.operator)[1:]
            op_fields = make_unique_fields(src_fields, op_fields)
            return [*src_fields, *op_fields]
    # End _get_unique_fields method

    # noinspection PyUnresolvedReferences
    @cache
    def _field_names_and_count(self, element: ELEMENT) -> tuple[int, str, str]:
        """
        Override field names for Selection -- ignore insert names and count
        """
        fields = self._get_fields(element)[1:]
        select_names = make_field_names(fields)
        geom_type = get_geometry_column_name(element, include_geom_type=True)
        return 0, EMPTY, self._concatenate(geom_type, select_names)
    # End _field_names_and_count method

    # noinspection PyUnresolvedReferences
    def _get_fields(self, element: ELEMENT) -> FIELDS:
        """
        Get Fields from Element based on Attribute Option
        """
        if self._attr_option in (AttributeOption.ALL, AttributeOption.SANS_FID):
            fields = validate_fields(element, fields=element.fields)
        else:
            if element is self.source:
                fields = [self.output_fid_source]
            else:
                fields = [self.output_fid_operator]
        if self._attr_option in (AttributeOption.ALL, AttributeOption.ONLY_FID):
            fields = [element.primary_key_field, *fields]
        return fields
    # End _get_fields method
# End ClassicMixin class


class QueryIntersectPairwise(AbstractSpatialAttribute):
    """
    Queries for Intersect (Pairwise)
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass',
                 operator: 'FeatureClass', attribute_option: AttributeOption,
                 output_type_option: OutputTypeOption,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QueryIntersectPairwise class
        """
        super().__init__(
            source=source, target=target, operator=operator,
            attribute_option=attribute_option, xy_tolerance=xy_tolerance)
        self._output_type_option: OutputTypeOption = output_type_option
    # End init built-in

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type based on Output Type Option and Source Shape Type
        """
        if self._output_type_option == OutputTypeOption.LINE:
            if self.source.is_multi_part:
                return ShapeType.multi_linestring
            return ShapeType.linestring
        elif self._output_type_option == OutputTypeOption.POINT:
            if self.source.is_multi_part:
                return ShapeType.multi_point
            return ShapeType.point
        return self.source.shape_type
    # End _get_target_shape_type method
# End QueryIntersectPairwise class


class QueryIntersectClassic(ClassicMixin, QueryIntersectPairwise):
    """
    Queries for Intersect (Classic)
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass',
                 operator: 'FeatureClass', attribute_option: AttributeOption,
                 output_type_option: OutputTypeOption,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QueryIntersectClassic class
        """
        source, source_fid, operator, operator_fid = _planarize_factory(
            source, operator=operator, use_full_extent=False,
            xy_tolerance=xy_tolerance)
        super().__init__(
            source=source, target=target, operator=operator,
            attribute_option=attribute_option, xy_tolerance=xy_tolerance,
            output_type_option=output_type_option)
        self._input_fid_source: 'Field' = source_fid
        self._input_fid_operator: 'Field' = operator_fid
    # End init built-in
# End QueryIntersectClassic class


class QueryUnionPairwise(QueryIntersectPairwise):
    """
    Queries for the intersection portion of Union (Pairwise).  The target
    feature class should already exist and may or may not have features
    depending on the results of symmetrical difference.
    """
    def __init__(self, source: 'FeatureClass', operator: 'FeatureClass',
                 target: 'FeatureClass', attribute_option: AttributeOption,
                 xy_tolerance: XY_TOL, **kwargs) -> None:
        """
        Initialize the QueryUnionPairwise class
        """
        super().__init__(
            source=source, target=target, operator=operator,
            attribute_option=attribute_option, xy_tolerance=xy_tolerance,
            output_type_option=OutputTypeOption.SAME)
    # End init built-in

    @property
    def target(self) -> 'FeatureClass':
        """
        Target
        """
        return self.target_full
    # End target property

    @property
    def target_full(self) -> 'FeatureClass':
        """
        Target Full
        """
        return self._target
    # End target_full property

    @property
    def target_empty(self) -> 'FeatureClass':
        """
        Target Empty
        """
        return self._target
    # End target_empty property
# End QueryUnionPairwise class


class QueryUnionClassic(ClassicMixin, QueryUnionPairwise):
    """
    Queries for the intersection portion of Union (Classic). The source and
    operator feature classes must already be planarized and coming from
    symmetrical difference, need to do it in this order since the
    symmetrical difference planarizing process retains the full extent of
    the source and operator feature classes.
    """
    def __init__(self, source: 'FeatureClass', source_fid: 'Field',
                 operator: 'FeatureClass', operator_fid: 'Field',
                 target: 'FeatureClass', attribute_option: AttributeOption,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QueryUnionClassic class
        """
        super().__init__(
            source=source, target=target, operator=operator,
            attribute_option=attribute_option, xy_tolerance=xy_tolerance)
        self._input_fid_source: 'Field' = source_fid
        self._input_fid_operator: 'Field' = operator_fid
    # End init built-in
# End QueryUnionClassic class


class BaseQuerySymmetricalDifference(AbstractSpatialAttribute):
    """
    Base Query Symmetrical Difference
    """
    @property
    def _disjoint_source(self) -> str:
        """
        Select Disjoint Features from Source (already available, this is
        just an alias)
        """
        return self.select_disjoint
    # End _disjoint_source property

    @property
    def _disjoint_operator(self) -> str:
        """
        Select Disjoint Features from Operator
        """
        return self._make_disjoint_select(self.operator)
    # End _disjoint_operator property

    def _get_insert_fields(self, element: 'FeatureClass') -> FIELDS:
        """
        Get Fields for Disjoint Insert Statements
        """
        is_source = element is self.source
        if self._attr_option == AttributeOption.ALL:
            _, *src_fields = self._get_fields(self.source)
            _, *op_fields = self._get_fields(self.operator)
            src_fields = [self.output_fid_source, *src_fields]
            if is_source:
                return src_fields
            else:
                op_fields = make_unique_fields(src_fields, op_fields)
                return [self.output_fid_operator, *op_fields]
        elif self._attr_option == AttributeOption.ONLY_FID:
            if is_source:
                return self.output_fid_source,
            else:
                return self.output_fid_operator,
        else:
            src_fields = self._get_fields(self.source)
            if is_source:
                return src_fields
            else:
                op_fields = self._get_fields(self.operator)
                return make_unique_fields(src_fields, op_fields)
    # End _get_insert_fields method

    @property
    def _insert_source(self) -> str:
        """
        Insert statement for use with Disjoint Source Features and Target
        """
        return self._build_insert(
            self.target_empty, fields=self._get_insert_fields(self.source))
    # End _insert_source property

    @property
    def _insert_operator(self) -> str:
        """
        Insert statement for use with Disjoint Operator Features and Target
        """
        return self._build_insert(
            self.target_empty, fields=self._get_insert_fields(self.operator))
    # End _insert_operator property

    @property
    def target(self) -> 'FeatureClass':
        """
        Target
        """
        return self.target_full
    # End target property

    @cached_property
    def target_full(self) -> 'FeatureClass':
        """
        Target Full
        """
        process_disjoint(self.source_config, xy_tolerance=self._xy_tolerance)
        process_disjoint(self.operator_config, xy_tolerance=self._xy_tolerance)
        return self.target_empty
    # End target_full property

    @property
    def source_config(self) -> QueryConfig:
        """
        Source Query Configuration
        """
        target = self.target_empty
        config = geometry_config(target, cast_geom=self.zm_config.is_different)
        return QueryConfig(
            source=self.source, target=target, config=config,
            disjoint=self._disjoint_source, insert=self._insert_source,
            transformer=self.source_transformer)
    # End source_config property

    @property
    def operator_config(self) -> QueryConfig:
        """
        Operator Query Configuration
        """
        target = self.target_empty
        config = geometry_config(target, cast_geom=self.zm_config.is_different)
        return QueryConfig(
            source=self.operator, target=target, config=config,
            disjoint=self._disjoint_operator, insert=self._insert_operator,
            transformer=self.operator_transformer)
    # End operator_config property
# End BaseQuerySymmetricalDifference class


class QuerySymmetricalDifferencePairwise(BaseQuerySymmetricalDifference):
    """
    Query Symmetrical Difference Pairwise
    """
# End QuerySymmetricalDifferencePairwise class


class QuerySymmetricalDifferenceClassic(
        ClassicMixin, BaseQuerySymmetricalDifference):
    """
    Query Symmetrical Difference Classic
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass',
                 operator: 'FeatureClass', attribute_option: AttributeOption,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QuerySymmetricalDifferenceClassic class
        """
        source, source_fid, operator, operator_fid = _planarize_factory(
            source, operator=operator, use_full_extent=True,
            xy_tolerance=xy_tolerance)
        super().__init__(
            source=source, target=target, operator=operator,
            attribute_option=attribute_option, xy_tolerance=xy_tolerance)
        self._input_fid_source: 'Field' = source_fid
        self._input_fid_operator: 'Field' = operator_fid
    # End init built-in

    def _get_insert_fields(self, element: 'FeatureClass') -> FIELDS:
        """
        Get Fields for Disjoint Insert Statements
        """
        fields = super()._get_insert_fields(element)
        if len(fields) == 1:
            return fields
        return fields[1:]
    # End _get_insert_fields method
# End QuerySymmetricalDifferenceClassic class


if __name__ == '__main__':  # pragma: no cover
    pass
