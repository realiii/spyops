# -*- coding: utf-8 -*-
"""
Repair Geometry
"""


from math import nan

from fudgeo.geometry import (
    LineString, MultiLineString, Polygon, MultiPolygon,
    LineStringZM, MultiPointZM)
from pytest import mark
from shapely import Polygon as ShapelyPolygon
from shapely.io import from_wkb
from shapely.predicates import is_valid_reason

from spyops.geometry.wa import make_valid


pytestmark = [mark.geometry]


class TestEmptyPoint:
    """
    Test Empty Point
    """
    def test_multipoint(self):
        """
        Test multipoint
        """
        mpt = MultiPointZM([(0, 1, 2, 3), (nan, nan, 1, 2)], srs_id=4326)
        geom = from_wkb(mpt.wkb)
        assert len(geom.geoms) == 2
        geom = make_valid(geom, method='structure', keep_collapsed=False)
        assert geom.is_valid
        assert hasattr(geom, 'geoms')
    # End test_multipoint method

    def test_linestring(self):
        """
        Test linestring
        """
        mpt = LineStringZM([(0, 1, 2, 3), (nan, nan, 1, 2), (1, 2, 3, 4)], srs_id=4326)
        geom = from_wkb(mpt.wkb)
        assert not geom.is_valid
        geom = make_valid(geom, method='structure', keep_collapsed=False)
        assert geom.is_valid
    # End test_linestring method

    def test_polygon_exterior(self):
        """
        Test polygon exterior
        """
        poly = MultiPolygon([], srs_id=4326)
        geom = from_wkb(poly.wkb)
        assert geom.is_empty
        geom = make_valid(geom, method='structure', keep_collapsed=False)
        assert hasattr(geom, 'geoms')
        assert geom.is_empty

        poly = MultiPolygon([[], [], [], []], srs_id=4326)
        geom = from_wkb(poly.wkb)
        assert geom.is_empty
        geom = make_valid(geom, method='structure', keep_collapsed=False)
        assert hasattr(geom, 'geoms')
        assert geom.is_empty

        poly = MultiPolygon([
            [[(10, 20), (10, 30), (30, 30), (nan, nan), (30, 20), (10, 20)],
             [(12, 25), (12, 28), (28, 28), (nan, nan), (28, 25), (12, 25)]],
            [[(10, 20), (10, 30), (nan, nan), (nan, nan)],
             [(12, 25), (12, 28), (28, 28), (nan, nan), (nan, nan)]]],
            srs_id=4326)
        geom = from_wkb(poly.wkb, on_invalid='fix')
        assert not geom.is_valid
        geom = make_valid(geom, method='structure', keep_collapsed=False)
        assert geom.is_valid
        assert not hasattr(geom, 'geoms')

    # End test_polygon_exterior method
# End TestEmptyPoint class


class TestEmptyPart:
    """
    Test repairing empty part
    """
    def test_line(self):
        """
        Test lines
        """
        line1 = [(0, 0), (1, 0)]
        line2 = [(2, 0), (5, 0)]
        line3 = []
        multi = MultiLineString([line1, line2, line3], srs_id=4326)
        assert len(multi.lines) == 3
        truth = [False, False, True]
        assert [line.is_empty for line in multi.lines] == truth
        geom = from_wkb(multi.wkb)
        lines = geom.geoms
        assert len(lines) == 3
        assert [line.is_empty for line in lines] == truth
        geom = geom.__class__([line for line in lines if not line.is_empty])
        lines = geom.geoms
        assert len(lines) == 2
        assert [line.is_empty for line in lines] == truth[:2]
    # End test_line method

    def test_line_make_valid(self):
        """
        Test lines make valid
        """
        line1 = [(0, 0), (1, 0)]
        line2 = [(2, 0), (5, 0)]
        line3 = []
        multi = MultiLineString([line1, line2, line3], srs_id=4326)
        assert len(multi.lines) == 3
        geom = from_wkb(multi.wkb)
        assert geom.is_valid
        assert len(geom.geoms) == 3
        geom = make_valid(geom, method='structure', keep_collapsed=False)
        assert geom.is_valid
        assert len(geom.geoms) == 2
    # End test_line_make_valid method

    def test_line_make_valid_two(self):
        """
        Test lines make valid, multi becomes single
        """
        line1 = [(0, 0), (1, 0)]
        line3 = []
        multi = MultiLineString([line1, line3], srs_id=4326)
        assert len(multi.lines) == 2
        geom = from_wkb(multi.wkb)
        assert geom.is_valid
        assert len(geom.geoms) == 2
        geom = make_valid(geom, method='structure', keep_collapsed=False)
        assert geom.is_valid
        assert not hasattr(geom, 'geoms')
    # End test_line_make_valid_two method

    def test_poly_make_valid(self):
        """
        Test polygon make valid, multi becomes single
        """
        poly1 = [[(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)]]
        poly2 = []
        poly3 = [[(20, 20), (20, 30), (30, 30), (30, 20), (20, 20)]]
        multi = MultiPolygon([poly1, poly2, poly3], srs_id=4326)
        assert len(multi.polygons) == 3
        geom = from_wkb(multi.wkb)
        assert geom.is_valid
        assert len(geom.geoms) == 3
        geom = make_valid(geom, method='structure', keep_collapsed=False)
        assert geom.is_valid
        assert len(geom.geoms) == 2
    # End test_poly_make_valid method

    def test_poly_make_valid_two(self):
        """
        Test polygon make valid, multi becomes single
        """
        poly1 = [[(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)]]
        poly2 = []
        multi = MultiPolygon([poly1, poly2], srs_id=4326)
        assert len(multi.polygons) == 2
        geom = from_wkb(multi.wkb)
        assert geom.is_valid
        assert len(geom.geoms) == 2
        geom = make_valid(geom, method='structure', keep_collapsed=False)
        assert geom.is_valid
        assert not hasattr(geom, 'geoms')
    # End test_poly_make_valid_two method
# End TestEmptyPart class


class TestPointCount:
    """
    Test repairing point count
    """
    def test_line(self):
        """
        Test line
        """
        line = LineString([(0, 0)], srs_id=4326)
        geom = from_wkb(line.wkb, on_invalid='fix')
        assert geom is None
    # End test_line method

    @mark.parametrize('poly, expected', [
        (Polygon([[(0, 0)]], srs_id=4326), type(None)),
        (Polygon([[(0, 0), (0, 1)]], srs_id=4326), ShapelyPolygon),
        (Polygon([[(0, 0), (0, 1), (1, 1)]], srs_id=4326), ShapelyPolygon),
        (Polygon([[(0, 0), (0, 10), (10, 10), (10, 0)],
                  [(2, 2), (2, 5)]], srs_id=4326), ShapelyPolygon),
    ])
    def test_polygon(self, poly, expected):
        """
        Test polygon / ring
        """
        geom = from_wkb(poly.wkb, on_invalid='fix')
        assert isinstance(geom, expected)
    # End test_polygon method
# End TestPointCount class


class TestRings:
    """
    Test repairing Empty Ring
    """
    @mark.parametrize('poly, count', [
        (Polygon([[(0, 0), (0, 10), (10, 10)]], srs_id=4326), 0),
        (Polygon([[(0, 0), (0, 10), (10, 10), (10, 0)], [(2, 2), (2, 5), (5, 5), (5, 2)]], srs_id=4326), 1),
        (Polygon([[(0, 0), (0, 10), (10, 10), (10, 0)], []], srs_id=4326), 0),
        (Polygon([[(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)], []], srs_id=4326), 0),
    ])
    def test_empty_ring(self, poly, count):
        """
        Test empty ring
        """
        geom = from_wkb(poly.wkb, on_invalid='fix')
        geom = make_valid(geom, method='structure', keep_collapsed=False)
        assert len(geom.interiors) == count
        assert isinstance(geom, ShapelyPolygon)
    # End test_empty_ring method

    def test_empty_exterior(self):
        """
        Empty Exterior
        """
        poly = Polygon([[], [(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)]], srs_id=4326)
        geom = from_wkb(poly.wkb, on_invalid='fix')
        assert geom is None
    # End test_empty_exterior method

    @mark.parametrize('poly', [
        Polygon([[(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)],
                 [(20, 20), (20, 25), (25, 25), (25, 20), (20, 20)]], srs_id=4326),
    ])
    def test_outside_ring(self, poly):
        """
        Test outside ring
        """
        geom = from_wkb(poly.wkb)
        assert isinstance(geom, ShapelyPolygon)
        assert not geom.is_valid
        assert is_valid_reason(geom).startswith('Hole lies outside shell')
    # End test_outside_ring method

    @mark.parametrize('poly', [
        Polygon([[(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)],
                 [(2, 2), (2, 5), (5, 5), (5, 2), (2, 2)],
                 [(2, 2), (2, 5), (5, 5), (5, 2), (2, 2)]], srs_id=4326),
        Polygon([[(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)],
                 [(2, 2), (2, 5), (5, 5), (5, 2), (2, 2)],
                 [(3, 3), (3, 6), (6, 6), (6, 3), (3, 3)]], srs_id=4326),
    ])
    def test_inside_ring(self, poly):
        """
        Test inside ring overlap
        """
        geom = from_wkb(poly.wkb)
        assert isinstance(geom, ShapelyPolygon)
        assert not geom.is_valid
        assert is_valid_reason(geom).startswith('Self-intersection')
        geom = make_valid(geom)
        assert geom.is_valid
    # End test_inside_ring method
# End TestRings class


@mark.parametrize('fc_name, expected', [
    ('point_p', 4),
    ('linestring_l', 1),
    ('polygon_a', 1),
    ('multipoint_mp', 1),
    ('multilinestring_ml', 1),
    ('multipolygon_ma', 1),
])
def test_empty_query(check_repair, fc_name, expected):
    """
    Test empty query
    """
    source = check_repair[fc_name]
    cursor = source.select()
    count = sum([g.is_empty for g, in cursor.fetchall()])
    assert count == expected
# End test_empty_query method


if __name__ == '__main__':  # pragma: no cover
    pass
