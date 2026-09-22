# -*- coding: utf-8 -*-
"""
Fill Missing Z Values
"""


from typing import Callable, TYPE_CHECKING, TypeAlias

from fudgeo.enumeration import ShapeType
from fudgeo.geometry import (
    LineStringZ, LineStringZM,  MultiLineStringZ, MultiLineStringZM,
    MultiPolygonZ, MultiPolygonZM, PolygonZ, PolygonZM)
from numpy import copy

from spyops.environment import ANALYSIS_SETTINGS
from spyops.geometry.util import interpolate_zs
from spyops.shared.hint import VALUES


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray


MATCHER: TypeAlias = Callable[[VALUES], 'ndarray']


def _to_gpkg(features: list[tuple]) -> list[tuple[int, bytes]]:
    """
    Geometry to GPKG WKB format and reorder record
    """
    return [(i, geom.to_gpkg()) for geom, i in features]
# End _to_gpkg function


def _interpolate_zs(coordinates: 'ndarray', matcher: MATCHER) -> 'ndarray':
    """
    Interpolate Missing Z values
    """
    # noinspection bad-return
    return interpolate_zs(
        xs=coordinates[:, 0], ys=coordinates[:, 1], zs=coordinates[:, 2],
        matcher=matcher, value=ANALYSIS_SETTINGS.z_value)
# End _interpolate_zs function


def fill_linestrings(features: list[tuple[LineStringZ | LineStringZM, int]],
                     matcher: MATCHER) -> list[tuple[int, bytes]]:
    """
    Fill Missing Z values on LineStrings
    """
    for line, _ in features:
        line._coordinates = copy(line.coordinates)
        line.coordinates[:, 2] = _interpolate_zs(
            line.coordinates, matcher=matcher)
    return _to_gpkg(features)
# End fill_linestrings function


def fill_multi_linestrings(features: list[tuple[MultiLineStringZ | MultiLineStringZM, int]],
                           matcher: MATCHER) -> list[tuple[int, bytes]]:
    """
    Fill Missing Z values on Multi LineStrings
    """
    for multi, _ in features:
        for line in multi:
            line._coordinates = copy(line.coordinates)
            line.coordinates[:, 2] = _interpolate_zs(
                line.coordinates, matcher=matcher)
    return _to_gpkg(features)
# End fill_multi_linestrings function


def fill_polygons(features: list[tuple[PolygonZ | PolygonZM, int]],
                  matcher: MATCHER) -> list[tuple[int, bytes]]:
    """
    Fill Missing Z values on Polygons
    """
    for polygon, _ in features:
        for ring in polygon:
            ring.coordinates = copy(ring.coordinates)
            ring.coordinates[:, 2] = _interpolate_zs(
                ring.coordinates, matcher=matcher)
    return _to_gpkg(features)
# End fill_polygons function


def fill_multi_polygons(features: list[tuple[MultiPolygonZ | MultiPolygonZM, int]],
                        matcher: MATCHER) -> list[tuple[int, bytes]]:
    """
    Fill Missing Z values on Multi Polygons
    """
    for multi, _ in features:
        for polygon in multi:
            for ring in polygon:
                ring.coordinates = copy(ring.coordinates)
                ring.coordinates[:, 2] = _interpolate_zs(
                    ring.coordinates, matcher=matcher)
    return _to_gpkg(features)
# End fill_multi_polygons function


GEOMETRY_FILL_MISSING_Z: dict[str, Callable] = {
    ShapeType.linestring: fill_linestrings,
    ShapeType.multi_linestring: fill_multi_linestrings,
    ShapeType.polygon: fill_polygons,
    ShapeType.multi_polygon: fill_multi_polygons,
}


if __name__ == '__main__':  # pragma: no cover
    pass
