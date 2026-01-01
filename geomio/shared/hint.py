# -*- coding: utf-8 -*-
"""
Type Hints
"""


from typing import TypeAlias

from fudgeo import FeatureClass, Field, GeoPackage, MemoryGeoPackage, Table
from shapely.geometry import (
    LineString as ShapelyLineString, MultiLineString as ShapelyMultiLineString,
    MultiPoint as ShapelyMultiPoint, MultiPolygon as ShapelyMultiPolygon,
    Point as ShapelyPoint, Polygon as ShapelyPolygon)


NAMES: TypeAlias = list[str] | tuple[str, ...]
XY_TOL: TypeAlias = float | int | None

ELEMENT: TypeAlias = Table | FeatureClass
EXTENT: TypeAlias = tuple[float, float, float, float]
FIELD_NAMES: TypeAlias = NAMES
FIELDS: TypeAlias = list[Field] | tuple[Field, ...]
GPKG: TypeAlias = GeoPackage | MemoryGeoPackage


POLYGONS: TypeAlias = list[ShapelyPolygon] | list[ShapelyMultiPolygon]
LINES: TypeAlias = list[ShapelyLineString] | list[ShapelyMultiLineString]
POINTS: TypeAlias = list[ShapelyPoint] | list[ShapelyMultiPoint]


if __name__ == '__main__':  # pragma: no cover
    pass
