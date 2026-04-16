# -*- coding: utf-8 -*-
"""
Minimum Bounding Geometry
"""


from math import atan, degrees
from operator import itemgetter
from typing import Callable, TYPE_CHECKING

from numpy import diff, frompyfunc, hypot
from numpy.ma.core import argmax, argmin
from shapely import Polygon
from shapely.affinity import affine_transform
from shapely.constructive import (
    convex_hull, envelope, minimum_bounding_circle, minimum_rotated_rectangle,
    normalize)
from shapely.coordinates import get_coordinates

from spyops.geometry.util import find_slice_indexes
from spyops.shared.enumeration import MinimumGeometryOption


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray


def _minimum_rotated_rectangle_width(geometry, **kwargs) -> Polygon | None:
    """
    Minimum Bounding Rectangle based on Minimum Width
    """
    if geometry is None:
        return None
    if geometry.is_empty:
        return Polygon()
    hull = geometry.convex_hull
    if not hasattr(hull, 'exterior'):
        return hull
    coords = get_coordinates(hull)
    xs = coords[:, 0]
    ys = coords[:, 1]
    dx = diff(xs)
    dy = diff(ys)
    length = hypot(dx, dy)
    uxs, uys = dx / length, dy / length
    vxs, vys = -uys, uxs
    rects = envelope([affine_transform(hull, (*params, 0, 0))
                      for params in zip(uxs, uys, vxs, vys)])
    coords, indexes = get_coordinates(rects, return_index=True)
    ids = find_slice_indexes(indexes)
    widths = []
    for begin, end in zip(ids[:-1], ids[1:]):
        (x1, y1), (x2, y2), (x3, y3), *_ = coords[begin:end]
        widths.append(min(hypot(x2 - x1, y2 - y1), hypot(x3 - x2, y3 - y2)))
    index = argmin(widths)
    rect = rects[index]
    inv_matrix = (uxs[index], vxs[index], uys[index], vys[index], 0, 0)
    return affine_transform(rect, inv_matrix)
# End _minimum_rotated_rectangle_width function


minimum_rotated_rectangle_width = frompyfunc(
    _minimum_rotated_rectangle_width, 1, 1)


def _rectangle_attributes(geoms: 'ndarray') -> list[tuple[float, float, float]]:
    """
    Rectangle Width (shorter side) and Length (longer side) in units of the
    geometry and Orientation in degrees measured clockwise from north along
    the Length (longer side).
    """
    wlo = []
    coords, indexes = get_coordinates(geoms, return_index=True)
    ids = find_slice_indexes(indexes)
    for begin, end in zip(ids[:-1], ids[1:]):
        try:
            pt1, pt2, pt3, *_ = coords[begin:end]
        except ValueError:
            wlo.append((0., 0., 0.))
            continue
        (x1, y1), (x2, y2), (x3, y3) = pt1, pt2, pt3
        width = hypot(x2 - x1, y2 - y1)
        length = hypot(x3 - x2, y3 - y2)
        if length >= width:
            points = pt2, pt3
        else:
            width, length = length, width
            points = pt1, pt2
        (x, y), (other_x, other_y) = sorted(points, key=itemgetter(1))
        wlo.append((width, length, _angle_continuous(other_x - x, other_y - y)))
    return wlo
# End _rectangle_attributes function


def _circle_attributes(geoms: 'ndarray') -> list[tuple[float, float, float]]:
    """
    Circle Diameter reported as Width and Length in units of the geometry.
    Orientation is 0.
    """
    wlo = _convex_hull_attributes(geoms)
    return [(length, length, 0.) for _, length, _ in wlo]
# End _rectangle_attributes function


def _convex_hull_attributes(geoms: 'ndarray') \
        -> list[tuple[float, float, float]]:
    """
    Convex Hull Width (shortest antipodal distance) and Length (longest
    antipodal distance) in units of the geometry and Orientation in degrees
    measured clockwise from north along the Length (longer side).
    """
    wlo = []
    coords, indexes = get_coordinates(normalize(geoms), return_index=True)
    ids = find_slice_indexes(indexes)
    for begin, end in zip(ids[:-1], ids[1:]):
        subset = coords[begin:end]
        pairs = _antipodal_pairs(subset)
        if not pairs:
            wlo.append((0., 0., 0.))
            continue
        distances = _distance_and_points(subset, pairs)
        if not distances:
            wlo.append((0., 0., 0.))
            continue
        width = min(distances)
        length = max(distances)
        points = distances[length]
        (x, y), (other_x, other_y) = sorted(points, key=itemgetter(1))
        wlo.append((width, length, _angle_continuous(other_x - x, other_y - y)))
    return wlo
# End _convex_hull_attributes function


def _angle_continuous(x_coord: float, y_coord: float) -> float:
    """
    Translates an angle into the correct quadrant and returns the
    value between 0 and 360 degrees
    """
    try:
        angle = abs(degrees(atan(y_coord / x_coord)))
    except ZeroDivisionError:
        if y_coord < 0:
            return 180.
        else:
            return 0.
    else:
        if x_coord > 0 <= y_coord:
            return 90. - angle
        elif x_coord > 0 > y_coord:
            return angle + 90.
        elif x_coord < 0 > y_coord:
            return 270. - angle
        elif x_coord < 0 <= y_coord:
            return 270. + angle
        return angle
# End _angle_continuous function


def _antipodal_pairs(coords: 'ndarray') -> set[tuple[int, int]]:
    """
    Find all antipodal pairs of vertices on a convex polygon.

    Algorithm from Preparata and Shamos (1985), p. 174.
    """
    pairs = set()
    if (count := len(coords)) < 3:
        return pairs
    ys = coords[:, 1]
    p = argmax(ys)
    q = argmin(ys)
    p0 = p
    q0 = q
    counter = 0
    while counter <= 2 * count:
        counter += 1
        if p != q:
            pairs.add((p, q))
        p_next = (p + 1) % count
        q_next = (q + 1) % count
        px, py = coords[p]
        qx, qy = coords[q]
        px_next, py_next = coords[p_next]
        qx_next, qy_next = coords[q_next]
        cross = ((px_next - px) * (qy_next - qy) -
                 (py_next - py) * (qx_next - qx))
        if cross < 0:
            p = p_next
        elif cross > 0:
            q = q_next
        else:
            p = p_next
            q = q_next
            if p != q:
                pairs.add((p, q))
        if (p, q) == (p0, q0):
            break
    return pairs
# End _antipodal_pairs function


def _distance_and_points(coords: 'ndarray', pairs: set[tuple[int, int]]) \
        -> dict[float, tuple[tuple[float, float], tuple[float, float]]]:
    """
    Distance and Points
    """

    data = {}
    for begin, end in pairs:
        bx, by = coords[begin]
        ex, ey = coords[end]
        # noinspection PyTypeChecker
        distance: float = hypot(bx - ex, by - ey)
        data[distance] = ((bx, by), (ex, ey))
    return data
# End _distance_and_points function


GEOMETRY_MINIMUM: dict[MinimumGeometryOption, Callable] = {
    MinimumGeometryOption.RECTANGLE_BY_AREA: minimum_rotated_rectangle,
    MinimumGeometryOption.RECTANGLE_BY_WIDTH: minimum_rotated_rectangle_width,
    MinimumGeometryOption.CONVEX_HULL: convex_hull,
    MinimumGeometryOption.CIRCLE: minimum_bounding_circle,
    MinimumGeometryOption.ENVELOPE: envelope,
}


GEOMETRY_MINIMUM_ATTRS: dict[MinimumGeometryOption, Callable] = {
    MinimumGeometryOption.RECTANGLE_BY_AREA: _rectangle_attributes,
    MinimumGeometryOption.RECTANGLE_BY_WIDTH: _rectangle_attributes,
    MinimumGeometryOption.CONVEX_HULL: _convex_hull_attributes,
    MinimumGeometryOption.CIRCLE: _circle_attributes,
    MinimumGeometryOption.ENVELOPE: _rectangle_attributes,
}


if __name__ == '__main__':  # pragma: no cover
    pass
