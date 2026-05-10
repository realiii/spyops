# -*- coding: utf-8 -*-
"""
Type stubs for query.management.generalization module
"""

from concurrent.futures.thread import ThreadPoolExecutor as PoolExecutor
from functools import cached_property
from typing import Generator

from fudgeo import FeatureClass
from shapely.geometry.base import BaseMultipartGeometry

from spyops.query.base import AbstractQueryDissolve
from spyops.query.mixin import StatisticsMixin
from spyops.shared.hint import FIELDS, STATS_FIELDS, XY_TOL


class QueryDissolve(StatisticsMixin, AbstractQueryDissolve):

    _statistics: STATS_FIELDS

    def __init__(self, source: FeatureClass, target: FeatureClass, *,
                 fields: FIELDS, statistics: STATS_FIELDS, as_multi_part: bool,
                 xy_tolerance: XY_TOL, ) -> None: ...
    def _field_names_and_count(self, element: FeatureClass) -> tuple[int, str, str]: ...
    def _get_target_shape_type(self) -> str: ...
    @property
    def select(self) -> str: ...
    @property
    def select_geometry(self) -> str: ...
    def dissolved_geometries(self) -> Generator[dict[int, BaseMultipartGeometry], None, None]: ...
    @cached_property
    def group_count(self) -> int: ...
    @property
    def source(self) -> FeatureClass: ...
