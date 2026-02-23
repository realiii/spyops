# -*- coding: utf-8 -*-
"""
Attribute Functions
"""


from typing import Callable, TYPE_CHECKING

from bottleneck import nanmax, nanmin
from numpy import array
from pyproj.transformer import Transformer
from shapely import (
    get_coordinates, get_num_interior_rings, get_point, point_on_surface)
from shapely.constructive import orient_polygons
from shapely.coordinates import transform

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.crs.unit import get_unit_conversion
from spyops.crs.util import equals
from spyops.geometry.util import find_slice_indexes, get_geoms_iter


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray
    from pyproj import CRS


def length_geodesic(geoms: 'ndarray', *, crs: 'CRS',
                    unit: LengthUnit) -> 'ndarray':
    """
    Length Geodesic
    """
    if not len(geoms):
        return array([], dtype=float)
    geoms = _transform_geometries(geoms, crs)
    geod = crs.get_geod()
    factor = get_unit_conversion(from_unit=LengthUnit.METERS, to_unit=unit)
    return array([geod.geometry_length(geom)
                  for geom in geoms], dtype=float) * factor
# End length_geodesic function


def area_geodesic(geoms: 'ndarray', *, crs: 'CRS', unit: AreaUnit) -> 'ndarray':
    """
    Area Geodesic
    """
    if not len(geoms):
        return array([], dtype=float)
    geoms = orient_polygons(geoms)
    geoms = _transform_geometries(geoms, crs)
    geod = crs.get_geod()
    factor = get_unit_conversion(from_unit=AreaUnit.SQUARE_METERS, to_unit=unit)
    return array([geod.geometry_area_perimeter(geom)[0]
                  for geom in geoms], dtype=float) * factor
# End area_geodesic function


def _transform_geometries(geoms: 'ndarray', crs: 'CRS') -> 'ndarray':
    """
    Transform Geometries into Geographic Coordinates if necessary
    """
    if equals(crs, crs.geodetic_crs):
        return geoms
    transformer = Transformer.from_crs(
        crs, crs.geodetic_crs, always_xy=True)
    # noinspection PyTypeChecker
    return transform(
        geoms, transformation=transformer.transform, interleaved=False)
# End _transform_geometries function


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


def extent_minimum(geoms: 'ndarray', *, has_z: bool, has_m: bool) -> list:
    """
    Extent Minimums for Non-Point Geometries
    """
    return _get_partial_extent(geoms, has_z=has_z, has_m=has_m, func=nanmin)
# End extent_minimum function


def extent_maximum(geoms: 'ndarray', *, has_z: bool, has_m: bool) -> list:
    """
    Extent Maximums for Non-Point Geometries
    """
    return _get_partial_extent(geoms, has_z=has_z, has_m=has_m, func=nanmax)
# End extent_maximum function


def _get_partial_extent(geoms: 'ndarray', *, has_z: bool, has_m: bool,
                        func: Callable) -> list:
    """
    Get Partial Extent
    """
    coords, indexes = get_coordinates(
        geoms, include_z=has_z, include_m=has_m, return_index=True)
    ids = find_slice_indexes(indexes)
    return [func(coords[b:e], axis=0) for b, e in zip(ids[:-1], ids[1:])]
# End _get_partial_extent function


if __name__ == '__main__':  # pragma: no cover
    pass
