# -*- coding: utf-8 -*-
"""
Constants in support of Geometry
"""


from typing import Any

from fudgeo.enumeration import ShapeType
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
    ShapeType.point: (ShapelyPoint, ShapelyMultiPoint),
    ShapeType.multi_point: (ShapelyPoint, ShapelyMultiPoint),
    ShapeType.linestring: (ShapelyLineString, ShapelyMultiLineString),
    ShapeType.multi_linestring: (ShapelyLineString, ShapelyMultiLineString),
    ShapeType.polygon: (ShapelyPolygon, ShapelyMultiPolygon),
    ShapeType.multi_polygon: (ShapelyPolygon, ShapelyMultiPolygon),
}
FUDGEO_GEOMETRY_LOOKUP: dict[str, dict[tuple[bool, bool], Any]] = {
    ShapeType.point: {
        (False, False): Point,
        (True, False): PointZ,
        (False, True): PointM,
        (True, True): PointZM},
    ShapeType.multi_point: {
        (False, False): MultiPoint,
        (True, False): MultiPointZ,
        (False, True): MultiPointM,
        (True, True): MultiPointZM},
    ShapeType.linestring: {
        (False, False): LineString,
        (True, False): LineStringZ,
        (False, True): LineStringM,
        (True, True): LineStringZM},
    ShapeType.multi_linestring: {
        (False, False): MultiLineString,
        (True, False): MultiLineStringZ,
        (False, True): MultiLineStringM,
        (True, True): MultiLineStringZM},
    ShapeType.polygon: {
        (False, False): Polygon,
        (True, False): PolygonZ,
        (False, True): PolygonM,
        (True, True): PolygonZM},
    ShapeType.multi_polygon: {
        (False, False): MultiPolygon,
        (True, False): MultiPolygonZ,
        (False, True): MultiPolygonM,
        (True, True): MultiPolygonZM}
}


if __name__ == '__main__':  # pragma: no cover
    pass
