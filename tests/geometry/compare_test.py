# -*- coding: utf-8 -*-
"""
Test Compare Geometry
"""


from numpy import array
from pytest import mark
from shapely import (
    Point, LineString, Polygon, MultiPoint, MultiLineString)
from shapely.constructive import normalize

from spyops.geometry.compare import compare_feature_geometry, remove_repeats

pytestmark = [mark.geometry]


class TestCompareGeometry:
    """
    Test Compare Geometry
    """
    @mark.parametrize('xy_tolerance', [
        None,
        0,
        0.1,
    ])
    @mark.parametrize('has_z, has_m', [
        (False, False),
        (True, True),
    ])
    def test_point(self, identical, xy_tolerance, has_z, has_m):
        """
        Test compare on points
        """
        source = identical['point_p']
        cursor = source.select(include_geometry=True, include_primary=True)
        features = cursor.fetchall()
        results = compare_feature_geometry(
            features, has_z=has_z, has_m=has_m, xy_tolerance=xy_tolerance)
        assert results == [(2, 3),
                           (4, 5), (4, 6),
                           (7, 8), (7, 9), (7, 10),
                           (11, 12), (11, 13), (11, 14), (11, 15)]
    # End test_point method

    @mark.parametrize('xy_tolerance', [
        None,
        0,
        0.1,
    ])
    @mark.parametrize('has_z, has_m', [
        (False, False),
        (True, True),
    ])
    def test_multi_point(self, identical, xy_tolerance, has_z, has_m):
        """
        Test compare on multi-points
        """
        source = identical['multipoint_mp']
        cursor = source.select(include_geometry=True, include_primary=True)
        features = cursor.fetchall()
        results = compare_feature_geometry(
            features, has_z=has_z, has_m=has_m, xy_tolerance=xy_tolerance)
        assert results == [
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
            (9, 10), (9, 11), (9, 12), (9, 13), (9, 14), (9, 15),
            (16, 17), (16, 18), (16, 19), (16, 20), (16, 21),
            (22, 23), (22, 24), (22, 25), (22, 26),
            (27, 28), (27, 29), (27, 30),
            (34, 35), (34, 36), (34, 37), (34, 38)]
    # End test_multi_point method

    @mark.parametrize('xy_tolerance', [
        None,
        0,
        0.1,
    ])
    @mark.parametrize('has_z, has_m', [
        (False, False),
        (True, True),
    ])
    def test_line(self, identical, xy_tolerance, has_z, has_m):
        """
        Test compare on line strings
        """
        source = identical['linestring_l']
        cursor = source.select(include_geometry=True, include_primary=True)
        features = cursor.fetchall()
        results = compare_feature_geometry(
            features, has_z=has_z, has_m=has_m, xy_tolerance=xy_tolerance)
        assert results == [
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10),
            (11, 12), (11, 13), (11, 14), (11, 15), (11, 16), (11, 17), (11, 18), (11, 19),
            (20, 21), (20, 22), (20, 23), (20, 24), (20, 25), (20, 26), (20, 27),
            (28, 29), (28, 30), (28, 31), (28, 32), (28, 33), (28, 34),
            (35, 36), (35, 37), (35, 38), (35, 39), (35, 40)]
    # End test_line method

    @mark.parametrize('xy_tolerance', [
        None,
        0,
        0.1,
    ])
    @mark.parametrize('has_z, has_m', [
        (False, False),
        (True, True),
    ])
    def test_multi_line(self, identical, xy_tolerance, has_z, has_m):
        """
        Test compare on multi line strings
        """
        source = identical['multilinestring_ml']
        cursor = source.select(include_geometry=True, include_primary=True)
        features = cursor.fetchall()
        results = compare_feature_geometry(
            features, has_z=has_z, has_m=has_m, xy_tolerance=xy_tolerance)
        assert results == [
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10),
            (11, 12), (11, 13), (11, 14), (11, 15), (11, 16), (11, 17), (11, 18), (11, 19),
            (20, 21), (20, 22), (20, 23), (20, 24), (20, 25), (20, 26), (20, 27),
            (28, 29), (28, 30), (28, 31), (28, 32), (28, 33), (28, 34),
            (35, 36), (35, 37), (35, 38), (35, 39), (35, 40),
            (52, 53)]
    # End test_multi_line method

    @mark.parametrize('xy_tolerance', [
        None,
        0,
        0.1,
    ])
    @mark.parametrize('has_z, has_m', [
        (False, False),
        (True, True),
    ])
    def test_poly(self, identical, xy_tolerance, has_z, has_m):
        """
        Test compare on polygon
        """
        source = identical['polygon_a']
        cursor = source.select(include_geometry=True, include_primary=True)
        features = cursor.fetchall()
        results = compare_feature_geometry(
            features, has_z=has_z, has_m=has_m, xy_tolerance=xy_tolerance)
        assert results == [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
                           (8, 9), (8, 10), (8, 11)]
    # End test_poly method

    @mark.parametrize('xy_tolerance', [
        None,
        0,
        0.1,
    ])
    @mark.parametrize('has_z, has_m', [
        (False, False),
        (True, True),
    ])
    def test_multi_poly(self, identical, xy_tolerance, has_z, has_m):
        """
        Test compare on multi polygon
        """
        source = identical['multipolygon_ma']
        cursor = source.select(include_geometry=True, include_primary=True)
        features = cursor.fetchall()
        results = compare_feature_geometry(
            features, has_z=has_z, has_m=has_m, xy_tolerance=xy_tolerance)
        assert results == [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
                           (8, 9), (8, 10), (8, 11),
                           (17, 33), (17, 34), (17, 35)]
    # End test_multi_poly method
# End TestCompareGeometry class


class TestRemoveRepeats:
    """
    Test Remove Repeats
    """
    @mark.parametrize('geoms, grid_size', [
        ([], None),
        (array([]), None),
        ([], 1),
        (array([]), 1),
    ])
    def test_empty(self, geoms, grid_size):
        """
        Test empty
        """
        assert not len(remove_repeats(geoms, grid_size=grid_size))
    # End test_empty method

    @mark.parametrize('grid_size, expected', [
        (None, [Point(0.25, 0.5)]),
        (1, [Point(0, 1)]),
        (10, [Point(0, 0)]),
    ])
    def test_points(self, grid_size, expected):
        """
        Test points
        """
        geom = Point(0.25, 0.5)
        assert remove_repeats([geom] * 3, grid_size=grid_size) == expected
    # End test_points method

    @mark.parametrize('grid_size, expected', [
        (None, [MultiPoint([Point(0.25, 0.5)] * 2)]),
        (1, [MultiPoint([Point(0, 1)] * 2)]),
        (10, [MultiPoint([Point(0, 0)] * 2)]),
    ])
    def test_multi_points(self, grid_size, expected):
        """
        Test points
        """
        geom = MultiPoint([Point(0.25, 0.5)] * 2)
        assert remove_repeats([geom] * 3, grid_size=grid_size) == expected
    # End test_multi_points method

    @mark.parametrize('grid_size, expected', [
        (None, [LineString([(0.25, 0.5), (0.75, 1.5)])]),
        (1, [LineString([(0, 1), (1, 2)])]),
        (0.5, [LineString([(0.5, 0.5), (1, 1.5)])]),
        (10, [LineString()]),
    ])
    def test_lines(self, grid_size, expected):
        """
        Test lines
        """
        geom = LineString([(0.25, 0.5), (0.75, 1.5)])
        assert remove_repeats([geom] * 3, grid_size=grid_size) == expected
    # End test_lines method

    @mark.parametrize('grid_size, expected', [
        (None, [MultiLineString([LineString([(0.25, 0.5), (0.75, 1.5)])] * 2)]),
        (1, [MultiLineString([LineString([(0, 1), (1, 2)])] * 2)]),
        (0.5, [MultiLineString([LineString([(0.5, 0.5), (1, 1.5)])] * 2)]),
        (10, [MultiLineString()]),
    ])
    def test_multi_lines(self, grid_size, expected):
        """
        Test multi lines
        """
        geom = MultiLineString([LineString([(0.25, 0.5), (0.75, 1.5)])] * 2)
        assert remove_repeats([geom] * 3, grid_size=grid_size) == expected
    # End test_multi_lines method

    @mark.parametrize('grid_size, expected', [
        (None, [Polygon([(0.25, 0.25), (0.75, 0.25), (0.75, 1.25), (0.25, 0.75)])]),
        (1, [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]),
        (0.5, [Polygon([(0.5, 0.5), (1, 0.5), (1, 1.5), (0.5, 1)])]),
        (10, [Polygon()]),
    ])
    def test_polygons(self, grid_size, expected):
        """
        Test polygons
        """
        geom = Polygon([(0.25, 0.25), (0.75, 0.25), (0.75, 1.25), (0.25, 0.75)])
        assert remove_repeats([geom] * 3, grid_size=grid_size) == normalize(expected)
    # End test_polygons method

    @mark.parametrize('grid_size, expected', [
        (None, [LineString([(0, 0.5), (0, 1.5)]), LineString([(0, 0.75), (0, 2)])]),
        (1, [LineString([(0, 1), (0, 2)])]),
        (10, [LineString()]),
    ])
    def test_overlaps_lines(self, grid_size, expected):
        """
        Test overlaps lines
        """
        lines = [LineString([(0, 0.5), (0, 1.5)]),
                 LineString([(0, 0.75), (0, 2)])]
        assert set(remove_repeats(lines, grid_size=grid_size)) == set(expected)
    # End test_overlaps_lines method
# End TestRemoveRepeats class


if __name__ == '__main__':  # pragma: no cover
    pass
