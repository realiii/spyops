# -*- coding: utf-8 -*-
"""
Geometry Configuration
"""


from typing import Any, Callable, NamedTuple, Type

from fudgeo import FeatureClass
from shapely import (
    LineString, MultiLineString, line_merge)
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry

from gisworks.geometry.constant import (
    FUDGEO_GEOMETRY_LOOKUP, SHAPELY_GEOMETRY_LOOKUP)
from gisworks.geometry.util import nada


class GeometryConfig(NamedTuple):
    """
    Geometry Configuration
    """
    geometry_cls: Any
    is_multi: bool
    filter_types: tuple[Type[BaseGeometry], Type[BaseMultipartGeometry]]
    srs_id: int
    combiner: Callable
# End GeometryConfig class


def geometry_config(target: FeatureClass) -> GeometryConfig:
    """
    Geometry Configuration
    """
    shape_type = target.shape_type
    cls = FUDGEO_GEOMETRY_LOOKUP[shape_type][target.has_z, target.has_m]
    filter_types = SHAPELY_GEOMETRY_LOOKUP[shape_type]
    combiner = _get_combiner(filter_types)
    return GeometryConfig(
        geometry_cls=cls, is_multi=target.is_multi_part,
        filter_types=filter_types, combiner=combiner,
        srs_id=target.spatial_reference_system.srs_id)
# End geometry_config function


def _combine_lines(value: LineString | MultiLineString) \
        -> LineString | MultiLineString:
    """
    Combine Lines using Directed Line Merge
    """
    if isinstance(value, MultiLineString):
        return line_merge(value, directed=True)
    return value
# End _combine_lines function


def _get_combiner(filter_types: tuple) -> Callable:
    """
    Get Combiner Function
    """
    if LineString in filter_types:
        return _combine_lines
    return nada
# End _get_combiner function


if __name__ == '__main__':  # pragma: no cover
    pass
