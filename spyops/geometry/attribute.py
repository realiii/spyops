# -*- coding: utf-8 -*-
"""
Attribute Functions
"""


from typing import TYPE_CHECKING

from numpy import array
from shapely import (
    MultiPolygon, Polygon, get_coordinates, get_num_interior_rings, get_point,
    point_on_surface, get_x, get_y)
from shapely.constructive import boundary, orient_polygons
from shapely.coordinates import transform
from shapely.measurement import area, length

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.crs.unit import (
    AREA_UNIT_LUT, LENGTH_UNIT_LUT, get_conv_factor, get_unit_conversion,
    get_unit_name)
from spyops.crs.util import equals, make_geodetic_transformer
from spyops.geometry.util import get_geoms_iter


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray
    from pyproj import CRS


def line_azimuth(geoms: 'ndarray', *, crs: 'CRS') -> 'ndarray':
    """
    Line Azimuth
    """
    starts = _transform_geometries(_get_points(geoms, index=0), crs)
    start_x, start_y = get_x(starts), get_y(starts)
    ends = _transform_geometries(_get_points(geoms, index=-1), crs)
    end_x, end_y = get_x(ends), get_y(ends)
    if not (geod := crs.get_geod()):
        raise ValueError('Cannot calculate line azimuth without a Geod')
    forward, _, _ = geod.inv(
        lons1=start_x, lats1=start_y, lons2=end_x, lats2=end_y)
    return forward
# End line_azimuth function


def length_planar(geoms: 'ndarray', *, crs: 'CRS',
                  unit: LengthUnit) -> 'ndarray':
    """
    Length Planar
    """
    if not len(geoms):
        return array([], dtype=float)
    lengths = length(geoms)
    if not (name := get_unit_name(crs)):
        return lengths
    from_factor = get_conv_factor(name)
    to_factor = get_conv_factor(LENGTH_UNIT_LUT[unit])
    return lengths * (from_factor / to_factor)
# End length_planar function


def area_planar(geoms: 'ndarray', *, crs: 'CRS', unit: AreaUnit) -> 'ndarray':
    """
    Area Planar
    """
    if not len(geoms):
        return array([], dtype=float)
    areas = area(geoms)
    if not (name := get_unit_name(crs)):
        return areas
    from_factor = get_conv_factor(name) ** 2
    to_value, to_factor = AREA_UNIT_LUT[unit]
    to_factor *= get_conv_factor(to_value) ** 2
    return areas * (from_factor / to_factor)
# End area_planar function


def length_geodesic(geoms: 'ndarray', *, crs: 'CRS',
                    unit: LengthUnit) -> 'ndarray':
    """
    Length Geodesic
    """
    if not len(geoms):
        return array([], dtype=float)
    if any(isinstance(geom, (Polygon, MultiPolygon)) for geom in geoms):
        geoms = boundary(geoms)
    geoms = _transform_geometries(geoms, crs)
    if not (geod := crs.get_geod()):
        raise ValueError('Cannot calculate geodesic length without a Geod')
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
    if not (geod := crs.get_geod()):
        raise ValueError('Cannot calculate geodesic area without a Geod')
    factor = get_unit_conversion(from_unit=AreaUnit.SQUARE_METERS, to_unit=unit)
    return array([geod.geometry_area_perimeter(geom)[0]
                  for geom in geoms], dtype=float) * factor
# End area_geodesic function


def _transform_geometries(geoms: 'ndarray', crs: 'CRS') -> 'ndarray':
    """
    Transform Geometries into Geographic Coordinates if necessary
    """
    if not (geodetic_crs := crs.geodetic_crs):
        return geoms
    if equals(crs, geodetic_crs):
        return geoms
    transformer = make_geodetic_transformer(crs)
    # noinspection PyTypeChecker
    return transform(
        geoms, transformation=transformer.transform, interleaved=False)
# End _transform_geometries function


def get_hole_count(geoms: 'ndarray') -> list[int]:
    """
    Get Hole Count for Polygons or MultiPolygons
    """
    # noinspection PyTypeChecker
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
    points = _get_points(geoms, index)
    return get_coordinates(points, include_z=has_z, include_m=has_m)
# End _get_line_position function


def _get_points(geoms: 'ndarray', index: int) -> 'ndarray':
    """
    Get Points at Index
    """
    return get_point(
        [get_geoms_iter(geom)[index] for geom in geoms], index=index)
# End _get_points function


if __name__ == '__main__':  # pragma: no cover
    pass
