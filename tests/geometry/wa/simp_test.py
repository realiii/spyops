# -*- coding: utf-8 -*-
"""
Workaround Tests
"""

from pytest import mark
from shapely import (
    LineString, MultiLineString, MultiPolygon, Polygon, from_wkt)

from spyops.geometry.wa.simp import simplify


pytestmark = [mark.geometry]


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
                  (50, 50, 123)]),
         Polygon([(50, 50, 123), (51, 50, 234), (51, 51, 345), (51, 50, 456),
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


if __name__ == '__main__':  # pragma: no cover
    pass
