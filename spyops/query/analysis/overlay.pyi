# -*- coding: utf-8 -*-
"""
Type stubs for query.analysis.overlay module
"""

from typing import Any

from fudgeo import FeatureClass, Field

from spyops.query.analysis.extract import QueryClip
from spyops.query.base import AbstractSpatialAttribute
from spyops.shared.base import QueryConfig
from spyops.shared.enumeration import AttributeOption, OutputTypeOption
from spyops.shared.hint import ELEMENT, FIELDS, XY_TOL


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
    def __init__(
        self,
        source: FeatureClass,
        target: FeatureClass,
        operator: FeatureClass,
        *,
        attribute_option: AttributeOption,
        output_type_option: OutputTypeOption,
        xy_tolerance: XY_TOL,
    ) -> None: ...

    def _get_target_shape_type(self) -> str: ...


class QueryIntersectClassic(ClassicMixin, QueryIntersectPairwise):
    def __init__(
        self,
        source: FeatureClass,
        target: FeatureClass,
        operator: FeatureClass,
        *,
        attribute_option: AttributeOption,
        output_type_option: OutputTypeOption,
        xy_tolerance: XY_TOL,
    ) -> None: ...


class QueryUnionPairwise(QueryIntersectPairwise):
    def __init__(
        self,
        source: FeatureClass,
        operator: FeatureClass,
        target: FeatureClass,
        *,
        attribute_option: AttributeOption,
        xy_tolerance: XY_TOL,
        **kwargs: Any,
    ) -> None: ...

    @property
    def target(self) -> FeatureClass: ...
    @property
    def target_full(self) -> FeatureClass: ...
    @property
    def target_empty(self) -> FeatureClass: ...


class QueryUnionClassic(ClassicMixin, QueryUnionPairwise):
    def __init__(
        self,
        source: FeatureClass,
        source_fid: Field,
        operator: FeatureClass,
        operator_fid: Field,
        target: FeatureClass,
        *,
        attribute_option: AttributeOption,
        xy_tolerance: XY_TOL,
    ) -> None: ...


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


class QuerySymmetricalDifferencePairwise(BaseQuerySymmetricalDifference):
    @property
    def source(self) -> FeatureClass: ...


class QuerySymmetricalDifferenceClassic(ClassicMixin, BaseQuerySymmetricalDifference):
    def __init__(
        self,
        source: FeatureClass,
        target: FeatureClass,
        operator: FeatureClass,
        *,
        attribute_option: AttributeOption,
        xy_tolerance: XY_TOL,
    ) -> None: ...

    def _get_insert_fields(self, element: FeatureClass) -> FIELDS: ...
    @property
    def source(self) -> FeatureClass: ...
