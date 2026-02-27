# -*- coding: utf-8 -*-
"""
Repair Geometry
"""


from fudgeo.geometry import LineString, MultiLineString, Polygon
from pytest import mark
from shapely import Polygon as ShapelyPolygon
from shapely.io import from_wkb
from shapely.predicates import is_valid_reason

from spyops.geometry.wa import make_valid

pytestmark = [mark.geometry]


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
    @mark.parametrize('poly', [
        Polygon([[(0, 0), (0, 10), (10, 10)]], srs_id=4326),
        Polygon([[(0, 0), (0, 10), (10, 10), (10, 0)], [(2, 2), (2, 5), (5, 5), (5, 2)]], srs_id=4326),
        Polygon([[(0, 0), (0, 10), (10, 10), (10, 0)], []], srs_id=4326),
        Polygon([[(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)], []], srs_id=4326),
    ])
    def test_empty_ring(self, poly):
        """
        Test empty ring
        """
        geom = from_wkb(poly.wkb, on_invalid='fix')
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


if __name__ == '__main__':  # pragma: no cover
    pass
