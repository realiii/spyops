# -*- coding: utf-8 -*-
"""
Type Hints
"""


from typing import Optional, TYPE_CHECKING, Type, TypeAlias, Union


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
    from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry
    from spyops.shared.sort import AbstractSortField
    from spyops.shared.stats import AbstractStatisticField


DISTANCE: TypeAlias = Union[
    'LinearUnit', 'DecimalDegrees', 'Field', str, float, int]
UNIT: TypeAlias = Union['LinearUnit', 'DecimalDegrees']
UNIT_TOLERANCE: TypeAlias = Union[UNIT, str, float, int]

UPDATES: TypeAlias = list[tuple[
    int, Optional[Union['BaseGeometry', 'BaseMultipartGeometry']]]]

NAMES: TypeAlias = list[str] | tuple[str, ...]
NUMBER: TypeAlias = float | int
RECLASS_TABLE: TypeAlias = (
        list[tuple[NUMBER, NUMBER | str]] |
        tuple[tuple[NUMBER, NUMBER | str], ...])
OPT_NUMBER: TypeAlias = NUMBER | None

XY_TOL: TypeAlias = OPT_NUMBER
Z_TOL: TypeAlias = OPT_NUMBER
M_TOL: TypeAlias = OPT_NUMBER
GRID_SIZE: TypeAlias = OPT_NUMBER

ELEMENT: TypeAlias = Union['Table', 'FeatureClass']
ELEMENTS: TypeAlias = list[ELEMENT] | tuple[ELEMENT, ...]
FEATURE_CLASSES: TypeAlias = list['FeatureClass'] | tuple['FeatureClass', ...]
EXTENT: TypeAlias = tuple[NUMBER, NUMBER, NUMBER, NUMBER]
FIELD_NAMES: TypeAlias = NAMES
OPT_FIELD_STR: TypeAlias = Optional[Union['Field', str]]
OPT_FIELD: TypeAlias = Optional['Field']
FIELDS: TypeAlias = list['Field'] | tuple['Field', ...]
STATS_FIELDS: TypeAlias = list['AbstractStatisticField'] | tuple['AbstractStatisticField', ...]
SORT_FIELDS: TypeAlias = list['AbstractSortField'] | tuple['AbstractSortField', ...]
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
