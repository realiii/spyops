# -*- coding: utf-8 -*-
"""
Tests for Centroid
"""


from pytest import mark, approx
from shapely import Point, MultiPoint, MultiLineString
from shapely.geometry.multipolygon import MultiPolygon
from shapely.io import from_wkt
from shapely.lib import centroid

from spyops.geometry.centroid import (
    centroid_linestrings, centroid_multi_linestrings, centroid_multi_points,
    centroid_multi_polygons, centroid_points, centroid_polygons)


pytestmark = [mark.geometry]


def test_centroid_points():
    """
    Test centroid points
    """
    points = [Point(0, 1, 2), Point(10, 20, 30)]
    a, b = centroid(points)
    assert approx((a.x, a.y), abs=0.01) == (0., 1.)
    assert approx((b.x, b.y), abs=0.01) == (10., 20.)
    assert centroid_points(points, has_z=True, has_m=False) == [[0., 1., 2.], [10., 20., 30.]]
# End test_centroid_points function


def test_centroid_multi_points():
    """
    Test centroid points
    """
    points = MultiPoint([Point(0, 0, 0), Point(10, 20, 30)]), MultiPoint([Point(0, 1, 2)])
    a, b = centroid(points)
    assert approx((a.x, a.y), abs=0.01) == (5., 10.)
    assert approx((b.x, b.y), abs=0.01) == (0., 1.)
    a, b = centroid_multi_points(points, has_z=True, has_m=False)
    assert a.tolist() == [5., 10., 15.]
    assert b.tolist() == [0., 1., 2.]
# End test_centroid_multi_points function


@mark.parametrize('use_xy_length, expected_a, expected_b', [
    (True, [5., 0., 3333., 4444.], [4., 0., 3.75, 4.75]),
    (False, [5., 0., 3333., 4444.], [4.1269, 0., 3.8451, 4.8451]),
])
def test_centroid_linestrings(use_xy_length, expected_a, expected_b):
    """
    Test centroid linestrings
    """
    line_a = from_wkt('LineString (2 0 1111 2222, 5 0 3333 4444, 8 0 5555 6666)')
    line_b = from_wkt('LineString (0 0 1 2, 3 0 3 4, 6 0 5 6, 8 0 7 8)')
    a, b = centroid(line_a), centroid(line_b)
    assert approx((a.x, a.y), abs=0.001) == [5., 0.]
    assert approx((b.x, b.y), abs=0.001) == [4., 0.]
    a, b = centroid_linestrings([line_a, line_b], has_z=True, has_m=True, use_xy_length=use_xy_length)
    assert approx(a.tolist(), abs=0.001) == expected_a
    assert approx(b.tolist(), abs=0.001) == expected_b
# End test_centroid_linestrings function


@mark.parametrize('use_xy_length, expected_a, expected_b', [
    (True, [2., 2., -1000., 1000.], [0., 50., -2500, 2675.]),
    (False, [2., 2., -1000., 1000.], [0., 16.1834, -1451.6866, 1575.9617]),
])
def test_centroid_linestrings_vertical(use_xy_length, expected_a, expected_b):
    """
    Test centroid linestrings, vertical lines
    """
    line_a = from_wkt('LineString (2 2 0 0, 2 2 -1000 1000, 2 2 -2000 2000)')
    line_b = from_wkt('LineString (0 0 100 0, 0 0 -1000 1100, 0 0 -2000 2100, 0 100 -3000 3250)')
    a, b = centroid(line_a), centroid(line_b)
    assert approx((a.x, a.y), abs=0.001) == [2., 2.]
    assert approx((b.x, b.y), abs=0.001) == [0., 50.]
    a, b = centroid_linestrings([line_a, line_b], has_z=True, has_m=True, use_xy_length=use_xy_length)
    assert approx(a.tolist(), abs=0.001) == expected_a
    assert approx(b.tolist(), abs=0.001) == expected_b
# End test_centroid_linestrings_vertical function


@mark.parametrize('use_xy_length, expected_a, expected_b', [
    (True, [4.4285, 0., 1430.5714, 1907.2857], [5424.9229, 17312.3074, -2141.6409, 9999.]),
    (False, [4.501, 0., 1430.6258, 1907.3401], [5418.0652, 17295.1631, -2139.355, 9999.]),
])
def test_centroid_multi_linestrings(use_xy_length, expected_a, expected_b):
    """
    Test centroid multi linestrings
    """
    line_a = from_wkt('LineString (2 0 1111 2222, 5 0 3333 4444, 8 0 5555 6666)')
    line_b = from_wkt('LineString (0 0 1 2, 3 0 3 4, 6 0 5 6, 8 0 7 8)')
    line1 = MultiLineString([line_a, line_b])
    line2 = MultiLineString([from_wkt('LineString (2000 10000 -1000 9999, 5000 15000 -2000 9999, 8000 25000 -3000 NaN)')])
    a, b = centroid(line1), centroid(line2)
    assert approx((a.x, a.y), abs=0.001) == [4.4285, 0.]
    assert approx((b.x, b.y), abs=0.001) == [5424.9229, 17312.3074]
    a, b = centroid_multi_linestrings([line1, line2], has_z=True, has_m=True, use_xy_length=use_xy_length)
    assert approx(a.tolist(), abs=0.001) == expected_a
    assert approx(b.tolist(), abs=0.001) == expected_b
# End test_centroid_multi_linestrings function


def test_centroid_polygons():
    """
    Test centroid polygons
    """
    poly_a = from_wkt('Polygon ((0 0 0 0, 1 0 4 5, 1 1 1 1, 0 1 2 3, 0 0 0 0))')
    poly_b = from_wkt('Polygon ((100 100 100 100, 101 100 104 105, 101 101 101 101, 100 101 102 103, 100 100 100 100))')
    a, b = centroid(poly_a), centroid(poly_b)
    assert approx((a.x, a.y), abs=0.01) == (0.5, 0.5)
    assert approx((b.x, b.y), abs=0.01) == (100.5, 100.5)
    a, b = centroid_polygons([poly_a, poly_b], has_z=True, has_m=True)
    assert approx(a.tolist(), abs=0.001) == [0.5, 0.5, 1.3333, 1.6666]
    assert approx(b.tolist(), abs=0.001) == [100.5, 100.5, 101.3333, 101.6666]
# End test_centroid_polygons function


def test_centroid_multi_polygons():
    """
    Test centroid multi polygons
    """
    poly_a = from_wkt('Polygon ((0 0 0 0, 1 0 4 5, 1 1 1 1, 0 1 2 3, 0 0 0 0))')
    poly_b = from_wkt('Polygon ((100 100 100 100, 101 100 104 105, 101 101 101 101, 100 101 102 103, 100 100 100 100))')
    multi = MultiPolygon([poly_a, poly_b])
    a = centroid(multi)
    assert approx((a.x, a.y), abs=0.001) == (50.5, 50.5)
    a, = centroid_multi_polygons([multi], has_z=True, has_m=True)
    assert approx(a, abs=0.001) == [50.5, 50.5, 51.3333, 51.6666]
# End test_centroid_multi_polygons function


if __name__ == '__main__':  # pragma: no cover
    pass
