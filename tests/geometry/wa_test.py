# -*- coding: utf-8 -*-
"""
Workaround Tests
"""


from warnings import simplefilter, catch_warnings

from numpy import isnan
from pytest import mark

from shapely import (
    LineString, Polygon, from_wkt, MultiLineString, MultiPolygon, MultiPoint,
    get_coordinates)

from spyops.geometry.wa import (
    USE_WORKAROUNDS, make_valid_structure, set_precision, simplify)
from spyops.shared.exception import OperationsWarning


pytestmark = [mark.geometry]


def test_make_valid():
    """
    Test Make Valid
    """
    a = from_wkt('Polygon ((0 0 0 0, 1 1 1 1, 0 1 2 3, 1 0 4 5, 0 0 0 0))')
    result = make_valid_structure(a)
    assert result.has_m
# End test_make_valid function


def test_use_workarounds():
    """
    Test USE_WORKAROUNDS
    """
    assert USE_WORKAROUNDS.transform is True
    assert USE_WORKAROUNDS.make_valid is True
    assert USE_WORKAROUNDS.simplify is True
    assert USE_WORKAROUNDS.coverage_simplify is True
    assert USE_WORKAROUNDS.polygonize_drop_m is True
    assert USE_WORKAROUNDS.polygonize_drop_z_nan is True
    assert USE_WORKAROUNDS.polygonize is True
    assert USE_WORKAROUNDS.line_interpolate_point is True
    assert USE_WORKAROUNDS.line_merge is True
    assert USE_WORKAROUNDS.set_precision is True
    assert USE_WORKAROUNDS.inconsistent_zm_source is True
    assert USE_WORKAROUNDS.point_intersection is True
    assert USE_WORKAROUNDS.point_interpolation is True
    assert USE_WORKAROUNDS.geometry_order_interpolation is True
    assert USE_WORKAROUNDS.dropped_nan_measures is True
# End test_use_workarounds function


@mark.parametrize('wkt, cls, expected', [
    ('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7))', None, True),
    ('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 0 0))', None, True),
    ('LineString (0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7)', None, False),
    ('Point (0 0 0 0)', None, False),
    ('Polygon M ((0 0 0, 0 1 1, 1 1 3, 1 0 5, 0 0 7))', None, True),
    ('Polygon M ((0 0 0, 0 1 1, 1 1 3, 1 0 5, 0 0 0))', None, True),
    ('LineString M (0 0 0, 0 1 1, 1 1 3, 1 0 5, 0 0 7)', None, False),
    ('Point M (0 0 0)', None, False),
    ('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7))', MultiPolygon, True),
    ('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 0 0))', MultiPolygon, True),
    ('LineString (0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7)', MultiLineString, False),
    ('Point (0 0 0 0)', MultiPoint, False),
])
def test_set_precision_nan(wkt, cls, expected):
    """
    Test set precision -- issue in polygons where coordinate gets
    assigned a NaN measure
    """
    a = from_wkt(wkt)
    if cls:
        a = cls([a])
    with catch_warnings(record=True) as ws:
        simplefilter('always')
        result = set_precision(a, grid_size=0.001)
        assert len(ws) == int(expected)
        if expected:
            w, = ws
            assert issubclass(w.category, OperationsWarning)
    coords = get_coordinates(result, include_m=True)
    assert bool(isnan(coords[:, 2]).any()) is expected
# End test_set_precision_nan function


class TestSimplify:
    """
    Test Simplify
    """
    @mark.parametrize('geom, expected', [
        (LineString([(50, 50), (51, 51), (52, 52)]),
         LineString([(50, 50), (52, 52)])),
        (LineString([(50, 50, 123), (51, 51, 456), (52, 52, 789)]),
         LineString([(50, 50, 123), (52, 52, 789)])),
    ])
    def test_linestring_sans_measures(self, geom, expected):
        """
        Test line string sans measures
        """
        result = simplify(geom, tolerance=10)
        assert result.equals(expected)
        assert geom.has_z == result.has_z
    # End test_linestring_sans_measures method

    @mark.parametrize('geom, expected', [
        ('LineString M (50 50 123, 51 51 456, 52 52 789)',
         'LineString M (50 50 123, 52 52 789)'),
        ('LineString (50 50 111 123, 51 51 222 456, 52 52 333 789)',
         'LineString (50 50 111 123, 52 52 333 789)'),
    ])
    def test_linestring_with_measures(self, geom, expected):
        """
        Test line string with measures
        """
        geom = from_wkt(geom)
        expected = from_wkt(expected)
        result = simplify(geom, tolerance=10)
        assert result.equals(expected)
        assert geom.has_z == result.has_z
        assert geom.has_m == result.has_m
    # End test_linestring_with_measures method

    @mark.parametrize('geom, expected', [
        (LineString([(50, 50), (51, 51), (52, 52)]),
         LineString([(50, 50), (52, 52)])),
        (LineString([(50, 50, 123), (51, 51, 456), (52, 52, 789)]),
         LineString([(50, 50, 123), (52, 52, 789)])),
    ])
    def test_multilinestring_sans_measures(self, geom, expected):
        """
        Test multi line string sans measures
        """
        geom = MultiLineString([geom])
        expected = MultiLineString([expected])
        result = simplify(geom, tolerance=10)
        assert result.equals(expected)
        assert geom.has_z == result.has_z
    # End test_multilinestring_sans_measures method

    @mark.parametrize('geom, expected', [
        ('LineString M (50 50 123, 51 51 456, 52 52 789)',
         'LineString M (50 50 123, 52 52 789)'),
        ('LineString (50 50 111 123, 51 51 222 456, 52 52 333 789)',
         'LineString (50 50 111 123, 52 52 333 789)'),
    ])
    def test_multilinestring_with_measures(self, geom, expected):
        """
        Test multi line string with measures
        """
        geom = from_wkt(geom)
        expected = from_wkt(expected)
        geom = MultiLineString([geom])
        expected = MultiLineString([expected])
        result = simplify(geom, tolerance=10)
        assert result.equals(expected)
        assert geom.has_z == result.has_z
        assert geom.has_m == result.has_m
    # End test_multilinestring_with_measures method

    @mark.parametrize('geom, expected', [
        (Polygon([(50, 50), (51, 50), (51, 51), (51, 50), (50, 50)]),
         Polygon([(50, 50), (51, 50), (51, 51), (51, 50), (50, 50)])),
        (Polygon([(50, 50, 123), (51, 50, 234), (51, 51, 345), (51, 50, 456),
                  (50, 50, 123)]), Polygon(
            [(50, 50, 123), (51, 50, 234), (51, 51, 345), (51, 50, 456),
             (50, 50, 123)])),
    ])
    def test_polygon_sans_measures(self, geom, expected):
        """
        Test polygon sans measures
        """
        result = simplify(geom, tolerance=0.5)
        assert result.normalize().equals(expected.normalize())
        assert geom.has_z == result.has_z
    # End test_polygon_sans_measures method

    @mark.parametrize('geom, expected', [
        ('Polygon M ((50 50 123, 51 50 234, 51 51 345, 51 50 456, 50 50 123))',
         'Polygon M ((50 50 123, 51 50 234, 51 51 345, 51 50 456, 50 50 123))'),
        ('Polygon ((50 50 1000 123, 51 50 2000 234, 51 51 3000 345, 51 50 4000 456, 50 50 5000 123))',
         'Polygon ((50 50 1000 123, 51 50 2000 234, 51 51 3000 345, 51 50 4000 456, 50 50 5000 123))'),
    ])
    def test_polygon_with_measures(self, geom, expected):
        """
        Test polygon with measures
        """
        geom = from_wkt(geom)
        expected = from_wkt(expected)
        result = simplify(geom, tolerance=0.5)
        assert result.normalize().equals(expected.normalize())
        assert geom.has_z == result.has_z
        assert geom.has_m == result.has_m
    # End test_polygon_with_measures method

    @mark.parametrize('geom, expected', [
        (Polygon([(50, 50), (51, 50), (51, 51), (51, 50), (50, 50)]),
         Polygon([(50, 50), (51, 50), (51, 51), (51, 50), (50, 50)])),
        (Polygon([(50, 50, 123), (51, 50, 234), (51, 51, 345), (51, 50, 456),
                  (50, 50, 123)]), Polygon(
            [(50, 50, 123), (51, 50, 234), (51, 51, 345), (51, 50, 456),
             (50, 50, 123)])),
    ])
    def test_multi_polygon_sans_measures(self, geom, expected):
        """
        Test multi polygon sans measures
        """
        geom = MultiPolygon([geom])
        expected = MultiPolygon([expected])
        result = simplify(geom, tolerance=0.5)
        assert result.normalize().equals(expected.normalize())
        assert geom.has_z == result.has_z
    # End test_multi_polygon_sans_measures method

    @mark.parametrize('geom, expected', [
        ('Polygon M ((50 50 123, 51 50 234, 51 51 345, 51 50 456, 50 50 123))',
         'Polygon M ((50 50 123, 51 50 234, 51 51 345, 51 50 456, 50 50 123))'),
        ('Polygon ((50 50 1000 123, 51 50 2000 234, 51 51 3000 345, 51 50 4000 456, 50 50 5000 123))',
         'Polygon ((50 50 1000 123, 51 50 2000 234, 51 51 3000 345, 51 50 4000 456, 50 50 5000 123))'),
    ])
    def test_multi_polygon_with_measures(self, geom, expected):
        """
        Test multi polygon with measures
        """
        geom = from_wkt(geom)
        expected = from_wkt(expected)
        geom = MultiPolygon([geom])
        expected = MultiPolygon([expected])
        result = simplify(geom, tolerance=0.5)
        assert result.normalize().equals(expected.normalize())
        assert geom.has_z == result.has_z
        assert geom.has_m == result.has_m
    # End test_multi_polygon_with_measures method
# End TestSimplify class


class TestLineInterpolatePoint:
    """
    Test line interpolate point
    """

# End TestLineInterpolatePoint class


if __name__ == '__main__':  # pragma: no cover
    pass
