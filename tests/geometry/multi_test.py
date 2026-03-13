# -*- coding: utf-8 -*-
"""
Tests for Multi Geometry
"""

from pytest import approx, mark
from shapely import (
    MultiLineString, MultiPoint, MultiPolygon, Point, LineString, Polygon)

from spyops.geometry.multi import (
    build_multi, _dissolve_point, _dissolve_linestring, _dissolve_polygon)


pytestmark = [mark.geometry]


def test_build_multi_polygon(inputs):
    """
    Test build multi polygon
    """
    fc = inputs['updater_a']
    assert len(fc) == 5
    polygon = build_multi(fc, transformer=None, select_sql='')
    assert isinstance(polygon, MultiPolygon)
    assert approx(polygon.bounds, abs=0.0001) == (
        6.74573, 46.13702, 16.47727, 52.52511)
# End test_build_multi_polygon function


def test_build_multi_line_string(world_features):
    """
    Test build multi line string
    """
    fc = world_features['rivers_l']
    assert len(fc) == 136
    line = build_multi(fc, transformer=None, select_sql='')
    assert isinstance(line, MultiLineString)
    assert approx(line.bounds, abs=0.0001) == (-164.88743, -36.96944, 160.76359, 71.39248)
# End test_build_multi_line_string function


def test_build_multi_point(world_features):
    """
    Test build multi point
    """
    fc = world_features['airports_p']
    assert len(fc) == 3500
    line = build_multi(fc, transformer=None, select_sql='')
    assert isinstance(line, MultiPoint)
    assert approx(line.bounds, abs=0.0001) == (-177.38063, -54.84327, 178.55922, 78.24611)
# End test_build_multi_line_string function


@mark.parametrize('geoms, grid_size, expected', [
    ((), None, MultiPoint([])),
    ((Point(0, 0), Point(0.1, 0.1)), None, MultiPoint([Point(0, 0), Point(0.1, 0.1)])),
    ((Point(0, 0), Point(0.1, 0.1)), 1, MultiPoint([Point(0, 0)])),
    ((Point(0, 0), Point(0, 0)), None, MultiPoint([Point(0, 0)])),
    ((Point(0, 0), Point(0, 0)), 0, MultiPoint([Point(0, 0)])),
])
def test_dissolve_point(geoms, grid_size, expected):
    """
    Test Dissolve Point
    """
    assert _dissolve_point(geoms, grid_size=grid_size) == expected
# End test_dissolve_point method


@mark.parametrize('geoms, grid_size, expected', [
    ((), None, MultiLineString([])),
    ((LineString([(0, 0), (10, 0)]), LineString([(0, 0), (10, 0)])), None,
     MultiLineString([[(0, 0), (10, 0)]])),
    ((LineString([(0, 0), (10, 0)]), LineString([(5, 0), (15, 0)])), None,
     MultiLineString([[(0, 0), (5, 0), (10, 0), (15, 0)]])),
    ((LineString([(0, 0), (10, 0)]), LineString([(5, 0), (15, 0)])), 0,
     MultiLineString([[(0, 0), (5, 0), (10, 0), (15, 0)]])),
    ((LineString([(0, 0), (10, 0)]), LineString([(5, -5), (5, 5)])), None,
     MultiLineString([[(0, 0), (5, 0)], [(5, -5), (5, 0)], [(5, 0), (10, 0)], [(5, 0), (5, 5)]])),
    ((LineString([(0, 0), (10, 0)]), LineString([(5, 0.1), (15, 0.1)])), 1,
     MultiLineString([[(0, 0), (5, 0), (10, 0), (15, 0)]])),
])
def test_dissolve_linestring(geoms, grid_size, expected):
    """
    Test Dissolve LineString
    """
    assert _dissolve_linestring(geoms, grid_size=grid_size) == expected
# End test_dissolve_linestring method


def test_dissolve_polygon():
    """
    Test Dissolve Polygon
    """
    poly1 = Polygon([(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)])
    poly2 = Polygon([(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)])
    assert _dissolve_polygon([poly1], grid_size=None) == MultiPolygon([poly1])
    assert _dissolve_polygon([poly2], grid_size=None) == MultiPolygon([poly2])
    geoms = [poly1, poly2]
    expected = MultiPolygon([[[(0, 0), (0, 10), (5, 10), (5, 15), (15, 15), (15, 5), (10, 5), (10, 0), (0, 0)]]])
    assert _dissolve_polygon(geoms, grid_size=None) == expected
# End test_dissolve_polygon function


if __name__ == '__main__':  # pragma: no cover
    pass
