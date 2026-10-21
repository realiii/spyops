# -*- coding: utf-8 -*-
"""
Type stubs for query.analysis.overlay module
"""


from abc import abstractmethod
from collections import defaultdict
from typing import Any

from fudgeo import FeatureClass, Field, MemoryGeoPackage, Table
from shapely import LineString, Point
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

from spyops.query.analysis.extract import QueryClip
from spyops.query.base import (
    AbstractQueryFeatureClasses, AbstractQueryFeatureClassesPolygon,
    AbstractSpatialAttribute)
from spyops.query.mixin import CountOverlapMixin
from spyops.shared.base import QueryConfig
from spyops.shared.enumeration import AttributeOption, OutputTypeOption
from spyops.shared.hint import (
    ELEMENT, FEATURE_CLASSES, FIELDS, GRID_SIZE, XY_TOL)


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


class QueryCountOverlappingFeaturesPolygon(CountOverlapMixin, AbstractQueryFeatureClassesPolygon):

    _min_count: int
    _overlap: Table | None

    def __init__(self, source: FEATURE_CLASSES, target: FeatureClass, min_count: int, overlap: Table | None, xy_tolerance: XY_TOL) -> None: ...
    @staticmethod
    def _make_tree(self, planarized: list) -> STRtree: ...


class AbstractQueryFeatureClassesGeneral(CountOverlapMixin, AbstractQueryFeatureClasses): 

    _min_count: int
    _overlap: Table | None

    def __init__(self, source: FEATURE_CLASSES, target: FeatureClass, min_count: int, overlap: Table | None, xy_tolerance: XY_TOL) -> None: ...
    @staticmethod
    @abstractmethod
    def _make_tree(planarized: list) -> STRtree: ...
    @staticmethod
    def _close_scratch(scratch: MemoryGeoPackage) -> None: ...
    def build_features(self) -> list[tuple[BaseGeometry, tuple]]: ...
    def _index_overlay(self, tree: STRtree, geoms: list, grid_size: GRID_SIZE) -> defaultdict[int, list[int]]: ...
    def _get_within_distance(self, tree: STRtree, grid_size: GRID_SIZE) -> float: ...
    def _build_features(self, geoms: list[BaseGeometry]) -> list[BaseGeometry]: ...


class QueryCountOverlappingFeaturesLine(AbstractQueryFeatureClassesGeneral):
    @staticmethod
    def _make_tree(planarized: list) -> STRtree: ...
    def _build_features(self, geoms: list[LineString]) -> list[LineString]: ...


class QueryCountOverlappingFeaturesPoint(AbstractQueryFeatureClassesGeneral):
    @staticmethod
    def _make_tree(planarized: list) -> STRtree: ...
    def _build_features(self, geoms: list[Point]) -> list[Point]: ...
