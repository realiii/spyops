# -*- coding: utf-8 -*-
"""
Attribute Functions Tests
"""


from pyproj import CRS
from pytest import approx, mark
from shapely import Polygon, MultiPolygon, LineString, MultiLineString

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.geometry.attribute import (
    area_geodesic, extent_maximum, extent_minimum, get_hole_count,
    get_inside_xy, length_geodesic, line_end,
    line_start)

pytestmark = [mark.geometry]


@mark.parametrize('geom, expected', [
    (Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]), 0),
    (Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]]), 1),
    (MultiPolygon([Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]])]), 1),
])
def test_get_hole_count(geom, expected):
    """
    Test get hole count
    """
    assert get_hole_count([geom]) == [expected]
# End test_get_hole_count function


@mark.parametrize('geom, expected', [
    (LineString([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)]), (0, 10.)),
    (MultiLineString([LineString([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)])]), (0, 10.)),
    (Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]]), (5., 7.)),
    (MultiPolygon([Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]])]), (5., 7.)),
])
def test_get_inside_xy(geom, expected):
    """
    Test get inside xy
    """
    assert approx(get_inside_xy([geom])[0], abs=0.001) == expected
# End test_get_inside_xy function


@mark.parametrize('geom, expected', [
    (LineString([(1, 2, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)]), (1., 2., 0.)),
    (MultiLineString([LineString([(1, 2, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)])]), (1., 2., 0.)),
    (MultiLineString([LineString([(1, 2, 0), (0, 10, 2)]), LineString([(10, 10, 5), (10, 0, 6)])]), (1., 2., 0.)),

])
def test_line_start(geom, expected):
    """
    Test line start
    """
    assert approx(line_start([geom], has_z=True, has_m=False)[0], abs=0.001) == expected
# End test_line_start function


@mark.parametrize('geom, expected', [
    (LineString([(1, 2, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)]), (10., 0., 6.)),
    (MultiLineString([LineString([(1, 2, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)])]), (10., 0., 6.)),
    (MultiLineString([LineString([(1, 2, 0), (0, 10, 2)]), LineString([(10, 10, 5), (10, 0, 6)])]), (10., 0., 6.)),
])
def test_line_end(geom, expected):
    """
    Test line end
    """
    assert approx(line_end([geom], has_z=True, has_m=False)[0], abs=0.001) == expected
# End test_line_end function


@mark.parametrize('geom, expected', [
    (LineString([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)]), (0., 0., 0.)),
    (MultiLineString([LineString([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)])]), (0., 0., 0.)),
    (Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]]), (0., 0., 0.)),
    (MultiPolygon([Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]])]), (0., 0., 0.)),
])
def test_extent_minimum(geom, expected):
    """
    Test extent minimum
    """
    assert approx(extent_minimum([geom], has_z=True, has_m=False)[0], abs=0.001) == expected
# End test_extent_minimum function


@mark.parametrize('geom, expected', [
    (LineString([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)]), (10., 10., 6.)),
    (MultiLineString([LineString([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)])]), (10., 10., 6.)),
    (Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]]), (10., 10., 6.)),
    (MultiPolygon([Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]])]), (10., 10., 6.)),
])
def test_extent_maximum(geom, expected):
    """
    Test extent maximum
    """
    assert approx(extent_maximum([geom], has_z=True, has_m=False)[0], abs=0.001) == expected
# End test_extent_maximum function


@mark.parametrize('geom, expected', [
    (Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)]), 1_227_877),
    (Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]]), 1_178_704),
    (MultiPolygon([Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]])]), 1_178_704),
])
def test_area_geodesic(geom, expected):
    """
    Test area geodesic
    """
    result = area_geodesic(
        [geom], crs=CRS(4326), unit=AreaUnit.SQUARE_KILOMETERS)[0]
    assert approx(result, abs=1) == expected
# End test_area_geodesic function


@mark.parametrize('geom, expected', [
    (Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)]), 4421),
    (Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]]), 4421),
    (MultiPolygon([Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]])]), 4421),
])
def test_length_geodesic(geom, expected):
    """
    Test length geodesic
    """
    result = length_geodesic([geom], crs=CRS(4326), unit=LengthUnit.KILOMETERS)[0]
    assert approx(result, abs=1) == expected
# End test_length_geodesic function


if __name__ == '__main__':  # pragma: no cover
    pass
