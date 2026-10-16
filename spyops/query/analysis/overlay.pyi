# -*- coding: utf-8 -*-
"""
Type stubs for query.analysis.overlay module
"""


from collections import defaultdict
from functools import cached_property
from typing import Any

from fudgeo import FeatureClass, Field, Table
from shapely import Polygon
from shapely.strtree import STRtree

from spyops.query.analysis.extract import QueryClip
from spyops.query.base import (
    AbstractQueryFeatureClassesPolygon,
    AbstractSpatialAttribute, QueryFeatureIntermediate)
from spyops.shared.base import QueryConfig
from spyops.shared.enumeration import AttributeOption, OutputTypeOption
from spyops.shared.hint import ELEMENT, FEATURE_CLASSES, FIELDS, XY_TOL


class QueryErase(QueryClip):
    def process_disjoint(self) -> None: ...
    @property
    def source(self) -> FeatureClass: ...


class ClassicMixin:
    def _get_unique_fields(self) -> FIELDS: ...
    def _field_names_and_count(self, element: ELEMENT) -> tuple[int, str, str]: ...
    def _get_fields(self, element: ELEMENT) -> FIELDS: ...
    @property
    def input_fid_source(self) -> Field: ...
    @property
    def input_fid_operator(self) -> Field: ...


class QueryIntersectPairwise(AbstractSpatialAttribute):

    _output_type_option: OutputTypeOption

    def __init__(self, source: FeatureClass, target: FeatureClass,
                 operator: FeatureClass, *, attribute_option: AttributeOption,
                 output_type_option: OutputTypeOption,
                 xy_tolerance: XY_TOL, ) -> None: ...
    def _get_target_shape_type(self) -> str: ...
    @property
    def source(self) -> FeatureClass: ...


class QueryIntersectClassic(ClassicMixin, QueryIntersectPairwise):

    _input_fid_source: 'Field'
    _input_fid_operator: 'Field'

    def __init__(self, source: FeatureClass, target: FeatureClass,
                 operator: FeatureClass, *, attribute_option: AttributeOption,
                 output_type_option: OutputTypeOption,
                 xy_tolerance: XY_TOL, ) -> None: ...


class QueryUnionPairwise(QueryIntersectPairwise):
    def __init__(self, source: FeatureClass, operator: FeatureClass,
                 target: FeatureClass, *, attribute_option: AttributeOption,
                 xy_tolerance: XY_TOL, **kwargs: Any, ) -> None: ...
    @property
    def target(self) -> FeatureClass: ...
    @property
    def target_full(self) -> FeatureClass: ...
    @property
    def target_empty(self) -> FeatureClass: ...


class QueryUnionClassic(ClassicMixin, QueryUnionPairwise):

    _input_fid_source: 'Field'
    _input_fid_operator: 'Field'

    def __init__(self, source: FeatureClass, source_fid: Field,
                 operator: FeatureClass, operator_fid: Field,
                 target: FeatureClass, *, attribute_option: AttributeOption,
                 xy_tolerance: XY_TOL, ) -> None: ...


class BaseQuerySymmetricalDifference(AbstractSpatialAttribute):
    @property
    def _disjoint_source(self) -> str: ...
    @property
    def _disjoint_operator(self) -> str: ...
    def _get_insert_fields(self, element: FeatureClass) -> FIELDS: ...
    @property
    def _insert_source(self) -> str: ...
    @property
    def _insert_operator(self) -> str: ...
    @property
    def target(self) -> FeatureClass: ...
    @property
    def target_full(self) -> FeatureClass: ...
    @property
    def source_config(self) -> QueryConfig: ...
    @property
    def operator_config(self) -> QueryConfig: ...
    @property
    def source(self) -> FeatureClass: ...


class QuerySymmetricalDifferencePairwise(BaseQuerySymmetricalDifference):
    @property
    def source(self) -> FeatureClass: ...


class QuerySymmetricalDifferenceClassic(ClassicMixin, BaseQuerySymmetricalDifference):

    _input_fid_source: 'Field'
    _input_fid_operator: 'Field'

    def __init__(self, source: FeatureClass, target: FeatureClass,
                 operator: FeatureClass, *, attribute_option: AttributeOption,
                 xy_tolerance: XY_TOL, ) -> None: ...
    def _get_insert_fields(self, element: FeatureClass) -> FIELDS: ...
    @property
    def source(self) -> FeatureClass: ...


class QueryCountOverlappingFeaturesPolygon(AbstractQueryFeatureClassesPolygon):

    _min_count: int
    _overlap: Table | None

    def __init__(self, source: FEATURE_CLASSES, target: FeatureClass, min_count: int, overlap: Table | None, xy_tolerance: XY_TOL) -> None: ...
    def _add_attributes(self, polygons: list[Polygon], queries: list[QueryFeatureIntermediate]) -> list[tuple[Polygon, tuple]]: ...
    def _get_unique_fields(self) -> FIELDS: ...
    def _build_attribute_groups(self, tree: STRtree, queries: list[QueryFeatureIntermediate]) -> defaultdict[int, list[tuple]]: ...
    def _summarize_by_polygon(self, polygons: list[Polygon], grouped: defaultdict[int, list[tuple]]) -> list[tuple[Polygon, tuple]]: ...
    def _build_overlaps_table(self, grouped: defaultdict[int, list[tuple]]) -> None: ...
    @cached_property
    def overlap_table(self) -> Table | None: ...
    @staticmethod
    def _get_overlap_fields() -> FIELDS: ...
    def _get_geoms_attributes(self, feature_class: FeatureClass | None) -> tuple[list[Polygon], list[tuple]]: ...
