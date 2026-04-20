# -*- coding: utf-8 -*-
"""
Type Hints
"""


from typing import TYPE_CHECKING, Type, TypeAlias, Union


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, Field, GeoPackage, MemoryGeoPackage, Table
    from fudgeo.geometry.base import AbstractGeometry
    from fudgeo.geometry import (
        LineString, LineStringM, LineStringZ, LineStringZM,
        Point, PointM, PointZM, PointZ)
    from spyops.crs.unit import DecimalDegrees, LinearUnit
    from shapely.geometry import (
        LineString as ShapelyLineString, MultiLineString, MultiPoint,
        MultiPolygon, Point as ShapelyPoint, Polygon)
    from spyops.shared.stats import AbstractStatisticField


DISTANCE: TypeAlias = Union[
    'LinearUnit', 'DecimalDegrees', 'Field', str, float, int]

NAMES: TypeAlias = list[str] | tuple[str, ...]
XY_TOL: TypeAlias = float | int | None
GRID_SIZE: TypeAlias = XY_TOL

ELEMENT: TypeAlias = Union['Table', 'FeatureClass']
ELEMENTS: TypeAlias = list[ELEMENT] | tuple[ELEMENT, ...]
EXTENT: TypeAlias = tuple[float, float, float, float]
FIELD_NAMES: TypeAlias = NAMES
FIELDS: TypeAlias = list['Field'] | tuple['Field', ...]
STATS_FIELDS: TypeAlias = list['AbstractStatisticField'] | tuple['AbstractStatisticField', ...]
GPKG: TypeAlias = Union['GeoPackage', 'MemoryGeoPackage']


POLYGONS: TypeAlias = list['Polygon'] | list['MultiPolygon']
LINES: TypeAlias = list['ShapelyLineString'] | list['MultiLineString']
POINTS: TypeAlias = list['ShapelyPoint'] | list['MultiPoint']


FEATURES: TypeAlias = list[tuple['AbstractGeometry', int]]
LINE: TypeAlias = Union['LineString', 'LineStringZ', 'LineStringM', 'LineStringZM']
LINE_TYPE: TypeAlias = Union[Type['LineString'], Type['LineStringZ'], Type['LineStringM'], Type['LineStringZM']]
POINT: TypeAlias = Union['Point', 'PointZ', 'PointM', 'PointZM']
POINT_TYPE: TypeAlias = Union[Type['Point'], Type['PointZ'], Type['PointM'], Type['PointZM']]


if __name__ == '__main__':  # pragma: no cover
    pass
