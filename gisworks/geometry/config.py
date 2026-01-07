# -*- coding: utf-8 -*-
"""
Geometry Configuration
"""


from typing import Any, Callable, NamedTuple, Type

from fudgeo import FeatureClass
from fudgeo.enumeration import GeometryType
from fudgeo.geometry import (
    LineString, LineStringM, LineStringZ, LineStringZM, MultiLineString,
    MultiLineStringM, MultiLineStringZ, MultiLineStringZM, MultiPoint,
    MultiPointM, MultiPointZ, MultiPointZM, MultiPolygon, MultiPolygonM,
    MultiPolygonZ, MultiPolygonZM, Point, PointM, PointZ, PointZM, Polygon,
    PolygonM, PolygonZ, PolygonZM)
from shapely import (
    LineString as ShapelyLineString,
    MultiLineString as ShapelyMultiLineString, MultiPoint as ShapelyMultiPoint,
    MultiPolygon as ShapelyMultiPolygon, Point as ShapelyPoint,
    Polygon as ShapelyPolygon, line_merge)
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry

from gisworks.geometry.util import nada

SHAPELY_GEOMETRY_LOOKUP: dict[str, tuple[Any, Any]] = {
    GeometryType.point: (ShapelyPoint, ShapelyMultiPoint),
    GeometryType.multi_point: (ShapelyPoint, ShapelyMultiPoint),
    GeometryType.linestring: (ShapelyLineString, ShapelyMultiLineString),
    GeometryType.multi_linestring: (ShapelyLineString, ShapelyMultiLineString),
    GeometryType.polygon: (ShapelyPolygon, ShapelyMultiPolygon),
    GeometryType.multi_polygon: (ShapelyPolygon, ShapelyMultiPolygon),
}
FUDGEO_GEOMETRY_LOOKUP: dict[str, dict[tuple[bool, bool], Any]] = {
    GeometryType.point: {
        (False, False): Point,
        (True, False): PointZ,
        (False, True): PointM,
        (True, True): PointZM},
    GeometryType.multi_point: {
        (False, False): MultiPoint,
        (True, False): MultiPointZ,
        (False, True): MultiPointM,
        (True, True): MultiPointZM},
    GeometryType.linestring: {
        (False, False): LineString,
        (True, False): LineStringZ,
        (False, True): LineStringM,
        (True, True): LineStringZM},
    GeometryType.multi_linestring: {
        (False, False): MultiLineString,
        (True, False): MultiLineStringZ,
        (False, True): MultiLineStringM,
        (True, True): MultiLineStringZM},
    GeometryType.polygon: {
        (False, False): Polygon,
        (True, False): PolygonZ,
        (False, True): PolygonM,
        (True, True): PolygonZM},
    GeometryType.multi_polygon: {
        (False, False): MultiPolygon,
        (True, False): MultiPolygonZ,
        (False, True): MultiPolygonM,
        (True, True): MultiPolygonZM}
}


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


def _combine_lines(value: ShapelyLineString | ShapelyMultiLineString) \
        -> ShapelyLineString | ShapelyMultiLineString:
    """
    Combine Lines using Directed Line Merge
    """
    if isinstance(value, ShapelyMultiLineString):
        return line_merge(value, directed=True)
    return value
# End _combine_lines function


def _get_combiner(filter_types: tuple) -> Callable:
    """
    Get Combiner Function
    """
    if ShapelyLineString in filter_types:
        return _combine_lines
    return nada
# End _get_combiner function


if __name__ == '__main__':  # pragma: no cover
    pass
