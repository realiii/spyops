# -*- coding: utf-8 -*-
"""
Query Classes for analysis.overlay module
"""


from collections import defaultdict
from functools import cache, cached_property
from operator import itemgetter
from typing import Optional, TYPE_CHECKING

from fudgeo.constant import FETCH_SIZE
from fudgeo.enumeration import ShapeType
from shapely.constructive import point_on_surface
from shapely.strtree import STRtree

from spyops.environment import ANALYSIS_SETTINGS
from spyops.geometry.config import geometry_config
from spyops.geometry.enumeration import DimensionOption
from spyops.geometry.util import filter_features, to_shapely
from spyops.query.analysis.extract import QueryClip
from spyops.query.base import (
    AbstractQueryFeatureClassesPolygon, AbstractSpatialAttribute,
    QueryFeatureIntermediate)
from spyops.query.planar import planarize_factory
from spyops.shared.base import QueryConfig
from spyops.shared.constant import EMPTY
from spyops.shared.enumeration import AttributeOption, OutputTypeOption
from spyops.shared.field import (
    FC_COUNT, FEAT_COUNT, ORIG_FID, ORIG_NAME, OVERLAP_FID,
    get_geometry_column_name, make_field_names, make_unique_fields,
    validate_fields)
from spyops.shared.hint import ELEMENT, FEATURE_CLASSES, FIELDS, XY_TOL
from spyops.shared.records import process_disjoint


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, Field, Table
    from shapely import Polygon


class QueryErase(QueryClip):
    """
    Queries for Erase
    """
    def process_disjoint(self) -> None:
        """
        Process Disjoint
        """
        query = QueryConfig(
            source=self.source, target=self.target,
            disjoint=self.select_disjoint, insert=self.insert,
            config=self.geometry_config, transformer=self.source_transformer)
        process_disjoint(query=query, grid_size=self.grid_size)
    # End process_disjoint method
# End QueryErase class


class ClassicMixin:
    """
    Mixin for Shared Classic Capabilities
    """
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
        element: 'FeatureClass'
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
        # noinspection PyTypeChecker
        return fields
    # End _get_fields method

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
# End ClassicMixin class


class QueryIntersectPairwise(AbstractSpatialAttribute):
    """
    Queries for Intersect (Pairwise)
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass',
                 operator: 'FeatureClass', *, attribute_option: AttributeOption,
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
                 operator: 'FeatureClass', *,
                 attribute_option: AttributeOption,
                 output_type_option: OutputTypeOption,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QueryIntersectClassic class
        """
        source, source_fid, operator, operator_fid = planarize_factory(
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
                 target: 'FeatureClass', *,
                 attribute_option: AttributeOption,
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
                 target: 'FeatureClass', *,
                 attribute_option: AttributeOption,
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
        process_disjoint(self.source_config, grid_size=self.grid_size)
        process_disjoint(self.operator_config, grid_size=self.grid_size)
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
                 operator: 'FeatureClass', *,
                 attribute_option: AttributeOption,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QuerySymmetricalDifferenceClassic class
        """
        source, source_fid, operator, operator_fid = planarize_factory(
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


class QueryCountOverlappingFeaturesPolygon(AbstractQueryFeatureClassesPolygon):
    """
    Query Count Overlapping Features - Polygon
    """
    def __init__(self, source: FEATURE_CLASSES, target: 'FeatureClass',
                 min_count: int, overlap: Optional['Table'],
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QueryCountOverlappingFeaturesPolygon class
        """
        super().__init__(source, target=target, xy_tolerance=xy_tolerance)
        self._min_count: int = min_count
        self._overlap: Optional['Table'] = overlap
    # End init built-in

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        return FEAT_COUNT, FC_COUNT
    # End _get_unique_fields method

    def _add_attributes(self, polygons: list['Polygon'],
                        queries: list[QueryFeatureIntermediate]) \
            -> list[tuple['Polygon', tuple]]:
        """
        Add Attributes, keeping all matches between planarized polygons
        (using representative point) and source geometries.
        """
        tree = STRtree(point_on_surface(polygons))
        grouped = self._build_attribute_groups(tree, queries)
        self._build_overlaps_table(grouped)
        return self._summarize_by_polygon(polygons, grouped)
    # End _add_attributes method

    def _build_attribute_groups(self, tree: STRtree,
                                queries: list[QueryFeatureIntermediate]) \
            -> defaultdict[int, list[tuple]]:
        """
        Build Attributes Groups where key is polygon index and values
        are the list of intersecting (fid, fc_name)
        """
        grouped = defaultdict(list)
        for query in queries:
            geoms, fids = self._get_geoms_attributes(query.target)
            if not geoms:
                continue
            if not (grouper := self._index_overlay(tree, geoms)):
                continue
            name = query.source.name
            attributes = [(fid, name) for fid in fids]
            for i, indexes in grouper.items():
                grouped[i].extend([attributes[idx] for idx in indexes])
        return grouped
    # End _build_attribute_groups method

    def _summarize_by_polygon(self, polygons: list['Polygon'],
                              grouped: defaultdict[int, list[tuple]]) \
            -> list[tuple['Polygon', tuple]]:
        """
        Summarize grouped attributes on a per polygon basis keeping only
        the polygons that have at least the minimum number of intersecting
        features.
        """
        results = []
        threshold = self._min_count
        for i, polygon in enumerate(polygons):
            if i not in grouped:
                continue
            _, names = zip(*grouped[i])
            feature_count = len(names)
            if feature_count < threshold:
                continue
            fc_count = len(set(names))
            results.append((polygon, (feature_count, fc_count)))
        return results
    # End _summarize_by_polygon method

    def _build_overlaps_table(self, grouped: defaultdict[int, list[tuple]]) -> None:
        """
        Build Overlaps table
        """
        if not grouped or not self.overlap_table:
            return
        records = []
        threshold = self._min_count
        for i, values in grouped.items():
            if len(values) < threshold:
                continue
            records.extend([(i, fid, name) for fid, name in values])
        tbl = self.overlap_table
        names = [f.escaped_name for f in self._get_overlap_fields()]
        sql_insert = f"""
            INSERT INTO {tbl.escaped_name} ({', '.join(names)}) 
            VALUES (?, ?, ?)
        """
        with tbl.geopackage.connection as cout:
            cout.executemany(sql_insert, sorted(records, key=itemgetter(0, 2)))
    # End _build_overlaps_table method

    @cached_property
    def overlap_table(self) -> Optional['Table']:
        """
        Optional Overlap Table
        """
        if self._overlap is None:
            return None
        return self._overlap.geopackage.create_table(
            self._overlap.name, fields=self._get_overlap_fields(),
            overwrite=ANALYSIS_SETTINGS.overwrite)
    # End overlap_table property

    @staticmethod
    def _get_overlap_fields() -> FIELDS:
        """
        Get Overlap Fields
        """
        return OVERLAP_FID, ORIG_FID, ORIG_NAME
    # End _get_overlap_fields method

    def _get_geoms_attributes(self, feature_class: Optional['FeatureClass']) \
            -> tuple[list['Polygon'], list]:
        """
        Get Geometries and Attributes
        """
        geometries = []
        fids = []
        if not feature_class:
            return geometries, fids
        cursor = feature_class.select(include_primary=True)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            features, geoms = to_shapely(
                features, transformer=None, option=DimensionOption.TWO_D)
            fids.extend([fid for _, fid in features])
            geometries.extend(geoms)
        return geometries, fids
    # End _get_geoms_attributes method
# End QueryCountOverlappingFeaturesPolygon class


if __name__ == '__main__':  # pragma: no cover
    pass
