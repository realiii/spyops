# -*- coding: utf-8 -*-
"""
Constants in support of Geometry
"""


from typing import Any

from fudgeo.enumeration import GeometryType
from fudgeo.geometry import (
    LineString, LineStringM, LineStringZ, LineStringZM, MultiLineString,
    MultiLineStringM, MultiLineStringZ, MultiLineStringZM, MultiPoint,
    MultiPointM, MultiPointZ, MultiPointZM, MultiPolygon, MultiPolygonM,
    MultiPolygonZ, MultiPolygonZM, Point, PointM, PointZ, PointZM, Polygon,
    PolygonM, PolygonZ, PolygonZM)
from shapely import (
    LineString as ShapelyLineString, MultiLineString as ShapelyMultiLineString,
    MultiPoint as ShapelyMultiPoint, MultiPolygon as ShapelyMultiPolygon,
    Point as ShapelyPoint, Polygon as ShapelyPolygon)


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


if __name__ == '__main__':  # pragma: no cover
    pass
