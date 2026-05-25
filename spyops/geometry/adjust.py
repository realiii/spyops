# -*- coding: utf-8 -*-
"""
Adjust Z
"""


from typing import Any, Callable, TYPE_CHECKING, TypeAlias

from fudgeo.enumeration import ShapeType
from fudgeo.geometry import (
    LineStringZ, LineStringZM,  MultiLineStringZ, MultiLineStringZM,
    MultiPointZ, MultiPointZM, MultiPolygonZ, MultiPolygonZM, PointZ, PointZM,
    PolygonZ, PolygonZM)
from numpy import copy


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray


ADJUSTER: TypeAlias = Callable[['ndarray'], 'ndarray']


def _to_gpkg(features: list[tuple]) -> list[tuple[int, bytes]]:
    """
    Geometry to GPKG WKB format and reorder record
    """
    return [(i, geom.to_gpkg()) for geom, i in features]
# End _to_gpkg function


def adjust_points(features: list[tuple[PointZ | PointZM, int]],
                  adjuster: ADJUSTER) -> list[tuple[int, bytes]]:
    """
    Adjust Z value on Points
    """
    for point, _ in features:
        # noinspection PyTypeChecker
        point.z = adjuster(point.z)
    return _to_gpkg(features)
# End adjust_points function


def adjust_multi_points(features: list[tuple[MultiPointZ | MultiPointZM, int]],
                        adjuster: ADJUSTER) -> list[tuple[int, bytes]]:
    """
    Adjust Z values on Multi Points
    """
    for multi, _ in features:
        multi._coordinates = copy(multi.coordinates)
        multi.coordinates[:, 2] = adjuster(multi.coordinates[:, 2])
    return _to_gpkg(features)
# End adjust_multi_points function


def adjust_linestrings(features: list[tuple[LineStringZ | LineStringZM, int]],
                       adjuster: ADJUSTER) -> list[tuple[int, bytes]]:
    """
    Adjust Z values on LineStrings
    """
    for line, _ in features:
        line._coordinates = copy(line.coordinates)
        line.coordinates[:, 2] = adjuster(line.coordinates[:, 2])
    return _to_gpkg(features)
# End adjust_linestrings function


def adjust_multi_linestrings(features: list[tuple[MultiLineStringZ | MultiLineStringZM, int]],
                             adjuster: ADJUSTER) -> list[tuple[int, bytes]]:
    """
    Adjust Z values on Multi LineStrings
    """
    for multi, _ in features:
        for line in multi:
            line._coordinates = copy(line.coordinates)
            line.coordinates[:, 2] = adjuster(line.coordinates[:, 2])
    return _to_gpkg(features)
# End adjust_multi_linestrings function


def adjust_polygons(features: list[tuple[PolygonZ | PolygonZM, int]],
                    adjuster: ADJUSTER) -> list[tuple[int, bytes]]:
    """
    Adjust Z values on Polygons
    """
    for polygon, _ in features:
        for ring in polygon:
            ring.coordinates = copy(ring.coordinates)
            ring.coordinates[:, 2] = adjuster(ring.coordinates[:, 2])
    return _to_gpkg(features)
# End adjust_polygons function


def adjust_multi_polygons(features: list[tuple[MultiPolygonZ | MultiPolygonZM, int]],
                          adjuster: ADJUSTER) -> list[tuple[int, bytes]]:
    """
    Adjust Z values on Multi Polygons
    """
    for multi, _ in features:
        for polygon in multi:
            for ring in polygon:
                ring.coordinates = copy(ring.coordinates)
                ring.coordinates[:, 2] = adjuster(ring.coordinates[:, 2])
    return _to_gpkg(features)
# End adjust_multi_polygons function


GEOMETRY_ADJUST_Z: dict[str, Callable] = {
    ShapeType.point: adjust_points,
    ShapeType.multi_point: adjust_multi_points,
    ShapeType.linestring: adjust_linestrings,
    ShapeType.multi_linestring: adjust_multi_linestrings,
    ShapeType.polygon: adjust_polygons,
    ShapeType.multi_polygon: adjust_multi_polygons,
}


if __name__ == '__main__':  # pragma: no cover
    pass
