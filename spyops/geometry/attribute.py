# -*- coding: utf-8 -*-
"""
Attribute Functions
"""


from typing import TYPE_CHECKING

from shapely import (
    get_coordinates, get_num_interior_rings, get_point,
    point_on_surface)

from spyops.geometry.util import get_geoms_iter


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray


def get_hole_count(geoms: 'ndarray') -> list[int]:
    """
    Get Hole Count for Polygons or MultiPolygons
    """
    return [sum(get_num_interior_rings(get_geoms_iter(g))) for g in geoms]
# End get_hole_count function


def get_inside_xy(geoms: 'ndarray') -> list[tuple[float, float]]:
    """
    Get Inside XY
    """
    return [(pt.x, pt.y) for pt in point_on_surface(geoms)]
# End get_inside_xy function


def line_start(geoms: 'ndarray', *, has_z: bool, has_m: bool) -> 'ndarray':
    """
    Line Starts
    """
    return _get_line_position(geoms, has_z=has_z, has_m=has_m, index=0)
# End line_start function


def line_end(geoms: 'ndarray', *, has_z: bool, has_m: bool) -> 'ndarray':
    """
    Line Ends
    """
    return _get_line_position(geoms, has_z=has_z, has_m=has_m, index=-1)

# End line_end function


def _get_line_position(geoms: 'ndarray', *, has_z: bool, has_m: bool,
                       index: int) -> 'ndarray':
    """
    Get Line Position
    """
    points = get_point(
        [get_geoms_iter(geom)[index] for geom in geoms], index=index)
    return get_coordinates(points, include_z=has_z, include_m=has_m)
# End _get_line_position function


if __name__ == '__main__':  # pragma: no cover
    pass
