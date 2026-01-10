# -*- coding: utf-8 -*-
"""
Geometry Configuration
"""


from functools import partial
from typing import Any, Callable, NamedTuple, Type

from fudgeo import FeatureClass
from shapely import (
    LineString, MultiLineString, line_merge)
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry

from gisworks.geometry.constant import (
    FUDGEO_GEOMETRY_LOOKUP, SHAPELY_GEOMETRY_LOOKUP)
from gisworks.geometry.convert import GEOMETRY_CAST
from gisworks.geometry.util import nada
from gisworks.shared.constant import HAS_M_KEY, HAS_Z_KEY, SRS_ID_KEY


class GeometryConfig(NamedTuple):
    """
    Geometry Configuration
    """
    geometry_cls: Any
    is_multi: bool
    filter_types: tuple[Type[BaseGeometry], Type[BaseMultipartGeometry]]
    srs_id: int
    combiner: Callable
    caster: Callable | None
# End GeometryConfig class


def geometry_config(target: FeatureClass, cast_geom: bool) -> GeometryConfig:
    """
    Geometry Configuration
    """
    shape_type = target.shape_type
    cls = FUDGEO_GEOMETRY_LOOKUP[shape_type][target.has_z, target.has_m]
    filter_types = SHAPELY_GEOMETRY_LOOKUP[shape_type]
    combiner = _get_combiner(filter_types)
    srs_id = target.spatial_reference_system.srs_id
    if cast_geom:
        caster = GEOMETRY_CAST[target.shape_type]
        kwargs = {SRS_ID_KEY: srs_id,
                  HAS_Z_KEY: target.has_z,
                  HAS_M_KEY: target.has_m}
        caster = partial(caster, **kwargs)
    else:
        caster = None
    return GeometryConfig(
        geometry_cls=cls, is_multi=target.is_multi_part,
        filter_types=filter_types, combiner=combiner,
        srs_id=srs_id, caster=caster)
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
