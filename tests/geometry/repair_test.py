# -*- coding: utf-8 -*-
"""
Repair Geometry
"""


from math import nan

from fudgeo.geometry import (
    LineString, LineStringZM, MultiLineString, MultiPointZM, MultiPolygon,
    Point, Polygon, MultiPointZ, LineStringZ, PolygonZ, PolygonZM,
    MultiLineStringZ, MultiLineStringZM)
from numpy import array
from pytest import mark
from shapely import (
    LineString as ShapelyLineString, MultiPoint as ShapelyMultiPoint,
    Polygon as ShapelyPolygon, MultiPolygon as ShapelyMultiPolygon)
from shapely.io import from_wkb
from shapely.predicates import is_empty, is_valid, is_valid_reason

from spyops.geometry.repair import (
    _repair_linestrings, _repair_multi_points, _repair_points, _repair_polygons,
    _repair_multi_linestrings, _repair_multi_polygons)
from spyops.geometry.util import to_shapely
from spyops.geometry.wa import make_valid_structure

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
        geom = make_valid_structure(geom)
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
        geom = make_valid_structure(geom)
        assert geom.is_valid
    # End test_linestring method

    def test_polygon_exterior(self):
        """
        Test polygon exterior
        """
        poly = MultiPolygon([], srs_id=4326)
        geom = from_wkb(poly.wkb)
        assert geom.is_empty
        geom = make_valid_structure(geom)
        assert hasattr(geom, 'geoms')
        assert geom.is_empty

        poly = MultiPolygon([[], [], [], []], srs_id=4326)
        geom = from_wkb(poly.wkb)
        assert geom.is_empty
        geom = make_valid_structure(geom)
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
        geom = make_valid_structure(geom)
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
        geom = make_valid_structure(geom)
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
        geom = make_valid_structure(geom)
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
        geom = make_valid_structure(geom)
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
        geom = make_valid_structure(geom)
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
        geom = make_valid_structure(geom)
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
        geom = make_valid_structure(geom)
        assert geom.is_valid
    # End test_inside_ring method
# End TestRings class


@mark.parametrize('fc_name, expected', [
    ('point_p', 4),
    ('linestring_l', 1),
    ('polygon_a', 3),
    ('multipoint_mp', 1),
    ('multilinestring_ml', 2),
    ('multipolygon_ma', 5),
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


def test_repair_points():
    """
    Test repair points
    """
    points = [Point(x=nan, y=nan, srs_id=4326),
              Point(x=1, y=2, srs_id=4326),
              Point.empty(srs_id=4326)]
    features = [(pt, i) for i, pt in enumerate(points, 1)]
    features, geometries = to_shapely(
        features=features, transformer=None, on_invalid='fix')
    assert is_valid(geometries).tolist() == [True, True, True]
    assert is_empty(geometries).tolist() == [True, False, True]
    ids = array([fid for _, fid in features], dtype=int)
    deletes = []
    _repair_points(geometries, ids=ids, deletes=deletes)
    assert deletes == [1, 3]
# End test_repair_point function


@mark.parametrize('has_m', [
    True,
    False,
])
def test_repair_multipoints(has_m):
    """
    Test repair multipoints
    """
    if has_m:
        multi1 = MultiPointZM([(nan, nan, 1, 2), (1, 2, 3, 4), (nan, nan, nan, nan)], srs_id=4326)
        multi2 = MultiPointZM([], srs_id=4326)
        multi3 = MultiPointZM([(7, 8, 9, 10), (7, 8, 9, 10)], srs_id=4326)
        multi4 = MultiPointZM([(7, 8, 9, 10), (7, 8, 90, 100)], srs_id=4326)
        multi5 = MultiPointZM([(nan, nan, nan, nan)], srs_id=4326)
        multi6 = MultiPointZM([(nan, nan, nan, nan), (5, 6, 7, 8)], srs_id=4326)
    else:
        multi1 = MultiPointZ([(nan, nan, 1), (1, 2, 3), (nan, nan, nan)], srs_id=4326)
        multi2 = MultiPointZ([], srs_id=4326)
        multi3 = MultiPointZ([(7, 8, 9), (7, 8, 9)], srs_id=4326)
        multi4 = MultiPointZ([(7, 8, 9), (7, 8, 90)], srs_id=4326)
        multi5 = MultiPointZ([(nan, nan, nan)], srs_id=4326)
        multi6 = MultiPointZ([(nan, nan, nan), (5, 6, 7)], srs_id=4326)

    multi = multi1, multi2, multi3, multi4, multi5, multi6
    features = [(mpt, i) for i, mpt in enumerate(multi, 1)]
    features, geometries = to_shapely(
        features=features, transformer=None, on_invalid='fix')
    assert is_valid(geometries).tolist() == [True, True, True, True, True, True]
    assert is_empty(geometries).tolist() == [False, True, False, False, True, False]

    ids = array([fid for _, fid in features], dtype=int)
    deletes = []
    empties = []
    updates = []
    _repair_multi_points(
        geometries, ids=ids, updates=updates, deletes=deletes,
        empties=empties, has_m=has_m)
    assert deletes == [2, 5]
    assert empties == []
    ids, multi  = zip(*updates)
    assert ids == (1, 3, 4, 6)
    assert all(isinstance(mpt, ShapelyMultiPoint) for mpt in multi)
    assert all(mpt.has_z for mpt in multi)
    assert all(mpt.has_m is has_m for mpt in multi)
# End test_repair_multipoints function


@mark.parametrize('has_m', [
    True,
    False,
])
def test_repair_linestrings(has_m):
    """
    Test repair linestrings
    """
    if has_m:
        line1 = LineStringZM([(nan, nan, 1, 2), (1, 2, 3, 4), (nan, nan, nan, nan)], srs_id=4326)
        line2 = LineStringZM([], srs_id=4326)
        line3 = LineStringZM([(7, 8, 9, 10), (7, 8, 9, 10)], srs_id=4326)
        line4 = LineStringZM([(7, 8, 9, 10), (7, 8, 90, 100)], srs_id=4326)
        line5 = LineStringZM([(nan, nan, nan, nan)], srs_id=4326)
        line6 = LineStringZM([(nan, nan, nan, nan), (5, 6, 7, 8)], srs_id=4326)
        line7 = LineStringZM([(0, 1, 2, 3)], srs_id=4326)
        line8 = LineStringZM([(1, 2, 3, 4), (nan, nan, nan, nan), (10, 20, 30, 40)], srs_id=4326)
        line9 = LineStringZM([(7, 8, 9, 10), (70, 80, 90, 100)], srs_id=4326)
    else:
        line1 = LineStringZ([(nan, nan, 1), (1, 2, 3), (nan, nan, nan)], srs_id=4326)
        line2 = LineStringZ([], srs_id=4326)
        line3 = LineStringZ([(7, 8, 9), (7, 8, 9)], srs_id=4326)
        line4 = LineStringZ([(7, 8, 9), (7, 8, 90)], srs_id=4326)
        line5 = LineStringZ([(nan, nan, nan)], srs_id=4326)
        line6 = LineStringZ([(nan, nan, nan), (5, 6, 7)], srs_id=4326)
        line7 = LineStringZ([(0, 1, 2)], srs_id=4326)
        line8 = LineStringZ([(1, 2, 3), (nan, nan, nan), (10, 20, 30)], srs_id=4326)
        line9 = LineStringZ([(7, 8, 9), (70, 80, 90)], srs_id=4326)
    lines = line1, line2, line3, line4, line5, line6, line7, line8, line9
    features = [(line, i) for i, line in enumerate(lines, 1)]
    features, geometries = to_shapely(
        features=features, transformer=None, on_invalid='fix')
    assert is_valid(geometries).tolist() == [
        False, True, False, False, False, False, False, False, True]
    assert is_valid_reason(geometries).tolist() == [
        'Invalid Coordinate[nan nan]',
        'Valid Geometry',
        'Too few points in geometry component[7 8]',
        'Too few points in geometry component[7 8]',
        None,
        'Invalid Coordinate[nan nan]',
        None,
        'Invalid Coordinate[nan nan]',
        'Valid Geometry']
    assert is_empty(geometries).tolist() == [
        False, True, False, False, False, False, False, False, False]

    ids = array([fid for _, fid in features], dtype=int)
    deletes = []
    empties = []
    updates = []
    _repair_linestrings(
        geometries, ids=ids, updates=updates, deletes=deletes,
        empties=empties, has_m=has_m)
    assert deletes == [2]
    assert set(empties) == {5, 7, 1, 6}
    ids, lines = zip(*updates)
    assert all(line.has_m is has_m for line in lines)
    assert all(isinstance(line, ShapelyLineString) for line in lines)
    assert all(line.has_z for line in lines)
    assert set(ids) == {3, 4, 8, 9}
# End test_repair_linestrings function


@mark.parametrize('has_m', [
    True,
    False
])
def test_repair_polygons(has_m):
    """
    Test repair polygons
    """
    if has_m:
        poly1 = PolygonZM([[(nan, nan, 1, 2), (1, 2, 3, 4), (nan, nan, nan, nan)]], srs_id=4326)
        poly2 = PolygonZM([], srs_id=4326)
        poly3 = PolygonZM([[(7, 8, 9, 10), (7, 8, 9, 10), (7, 8, 9, 10), (7, 8, 9, 10), (7, 8, 9, 10)]], srs_id=4326)
        poly4 = PolygonZM([[(7, 8, 0, 100), (7, 8, 10, 200), (7, 18, 10, 300), (7, 18, 0, 400)]], srs_id=4326)
        poly5 = PolygonZM([[(nan, nan, nan, nan), (nan, nan, nan, nan), (nan, nan, nan, nan)]], srs_id=4326)
        poly6 = PolygonZM([[(nan, nan, nan, nan), (5, 6, 7, 8), (nan, nan, nan, nan)]], srs_id=4326)
        poly7 = PolygonZM([[(0, 1, 2, 3)]], srs_id=4326)
        poly8 = PolygonZM([[(0, 0, 3, 4), (nan, nan, nan, nan), (0, 1, 30, 40), (1, 1, 300, 400), (1, 0, 3000, 4000), (0, 0, 3, 4)]], srs_id=4326)
        poly9 = PolygonZM([[(0, 0, 3, 4), (0, 1, 30, 40), (1, 1, 300, 400), (1, 0, 3000, 4000), (0, 0, 3, 4)]], srs_id=4326)
        poly10 = PolygonZM([[(0, 0, 3, 4), (0, 1, 30, 40), (1, 1, 300, 400), (1, 0, 3000, 4000)]], srs_id=4326)
        poly11 = PolygonZM([[], []], srs_id=4326)
        poly12 = PolygonZM([[], [(0, 0, 3, 4), (1, 0, 5, 6), (1, 1, 7, 8), (0, 1, 9, 10), (0, 0, 3, 4)],
                            [(50, 50, 60, 70), (51, 50, 80, 90), (51, 51, 100, 110), (50, 51, 120, 130), (50, 50, 140, 150)]], srs_id=4326)
        poly13 = PolygonZM([[(0, 0, 3, 4), (0, 1, 30, 40), (1, 1, 300, 400), (1, 0, 3000, 4000)], [], []], srs_id=4326)
        poly14 = PolygonZM([[(0, 0, 3, 4), (10, 0, 5, 6), (10, 10, 7, 8), (0, 10, 9, 10), (0, 0, 3, 4)],
                            [(2, 2, 10, 11), (2, 5, 12, 13), (5, 5, 14, 15), (5, 2, 16, 17), (2, 2, 18, 19)],
                            [(3, 3, 20, 21), (3, 6, 22, 23), (6, 6, 24, 25), (6, 3, 26, 27), (3, 3, 28, 29)]], srs_id=4326)
        poly15 = PolygonZM([[(10, 20, 0, 1), (10, 30, 2, 3), (30, 30, 4, 5), (30, 20, 6, 7), (10, 20, 8, 9)],
                            [(12, 15, 50, 60), (12, 18, 70, 80)]], srs_id=4326)
        poly16 = PolygonZM([[(0, 0, 3, 4), (1, 0, 5, 6), (1, 1, 7, 8), (0, 1, 9, 10), (0, 0, 3, 4)],
                            [(50, 50, 60, 70), (51, 50, 80, 90), (51, 51, 100, 110), (50, 51, 120, 130), (50, 50, 140, 150)]], srs_id=4326)
        poly17 = PolygonZM([[(0, 0, 3, 4), (1, 1, 5, 6), (1, 0, 7, 8), (0, 1, 9, 10), (0, 0, 3, 4)]], srs_id=4326)
        poly18 = PolygonZM([[(0, 0, 3, 4), (1, 0, 5, 6), (nan, nan, nan, nan), (1, 1, 7, 8), (0, 1, 9, 10), (0, 0, 3, 4)],
                            [(50, 50, 60, 70), (51, 50, 80, 90), (51, 51, 100, 110), (50, 51, 120, 130), (50, 50, 140, 150)]], srs_id=4326)
        poly19 = PolygonZM([[(0, 0, 3, 4), (10, 0, 5, 6), (10, 10, 7, 8), (0, 10, 9, 10), (0, 0, 3, 4)],
                            [(2, 2, 10, 11), (2, 5, 12, 13), (5, 5, 14, 15)]], srs_id=4326)
        poly20 = PolygonZM([[(0, 0, 3, 4), (10, 0, 5, 6), (10, 10, 7, 8), (0, 10, 9, 10), (0, 0, 3, 4)],
                            [(2, 2, 10, 11), (2, 2.5, 12, 13)],
                            [(3, 3, 20, 21), (3, 6, 22, 23), (6, 6, 24, 25), (6, 3, 26, 27), (3, 3, 28, 29)]], srs_id=4326)
    else:
        poly1 = PolygonZ([[(nan, nan, 1), (1, 2, 3), (nan, nan, nan)]], srs_id=4326)
        poly2 = PolygonZ([], srs_id=4326)
        poly3 = PolygonZ([[(7, 8, 9), (7, 8, 9), (7, 8, 9), (7, 8, 9), (7, 8, 9)]], srs_id=4326)
        poly4 = PolygonZ([[(7, 8, 0), (7, 8, 10), (7, 18, 10), (7, 18, 0)]], srs_id=4326)
        poly5 = PolygonZ([[(nan, nan, nan), (nan, nan, nan), (nan, nan, nan)]], srs_id=4326)
        poly6 = PolygonZ([[(nan, nan, nan), (5, 6, 7), (nan, nan, nan)]], srs_id=4326)
        poly7 = PolygonZ([[(0, 1, 2)]], srs_id=4326)
        poly8 = PolygonZ([[(0, 0, 3), (nan, nan, nan), (0, 1, 30), (1, 1, 300), (1, 0, 3000), (0, 0, 3)]], srs_id=4326)
        poly9 = PolygonZ([[(0, 0, 3), (0, 1, 30), (1, 1, 300), (1, 0, 3000), (0, 0, 3)]], srs_id=4326)
        poly10 = PolygonZ([[(0, 0, 3), (0, 1, 30), (1, 1, 300), (1, 0, 3000)]], srs_id=4326)
        poly11 = PolygonZ([[], []], srs_id=4326)
        poly12 = PolygonZ([[], [(0, 0, 3), (1, 0, 5), (1, 1, 7), (0, 1, 9), (0, 0, 3)],
                            [(50, 50, 60), (51, 50, 80), (51, 51, 100), (50, 51, 120), (50, 50, 140)]], srs_id=4326)
        poly13 = PolygonZ([[(0, 0, 3), (0, 1, 30), (1, 1, 300), (1, 0, 3000)], [], []], srs_id=4326)
        poly14 = PolygonZ([[(0, 0, 3), (10, 0, 5), (10, 10, 7), (0, 10, 9), (0, 0, 3)],
                           [(2, 2, 10), (2, 5, 12), (5, 5, 14), (5, 2, 16), (2, 2, 18)],
                           [(3, 3, 20), (3, 6, 22), (6, 6, 24), (6, 3, 26), (3, 3, 28)]], srs_id=4326)
        poly15 = PolygonZ([[(10, 20, 0), (10, 30, 2), (30, 30, 4), (30, 20, 6), (10, 20, 8)],
                           [(12, 15, 50), (12, 18, 70)]], srs_id=4326)
        poly16 = PolygonZ([[(0, 0, 3), (1, 0, 5), (1, 1, 7), (0, 1, 9), (0, 0, 3)],
                           [(50, 50, 60), (51, 50, 80), (51, 51, 100), (50, 51, 120), (50, 50, 140)]], srs_id=4326)
        poly17 = PolygonZ([[(0, 0, 3), (1, 1, 5), (1, 0, 7), (0, 1, 9), (0, 0, 3)]], srs_id=4326)
        poly18 = PolygonZ([[(0, 0, 3), (1, 0, 5), (nan, nan, nan), (1, 1, 7), (0, 1, 9), (0, 0, 3)],
                           [(50, 50, 60), (51, 50, 80), (51, 51, 100), (50, 51, 120), (50, 50, 140)]], srs_id=4326)
        poly19 = PolygonZ([[(0, 0, 3), (10, 0, 5), (10, 10, 7), (0, 10, 9), (0, 0, 3)],
                           [(2, 2, 10), (2, 5, 12), (5, 5, 14)]], srs_id=4326)
        poly20 = PolygonZ([[(0, 0, 3), (10, 0, 5), (10, 10, 7), (0, 10, 9), (0, 0, 3)],
                           [(2, 2, 10), (2, 2.5, 12)],
                           [(3, 3, 20), (3, 6, 22), (6, 6, 24), (6, 3, 26), (3, 3, 28)]], srs_id=4326)
    polys = (poly1, poly2, poly3, poly4, poly5, poly6, poly7, poly8, poly9,
             poly10, poly11, poly12, poly13, poly14, poly15, poly16, poly17,
             poly18, poly19, poly20)
    features = [(poly, i) for i, poly in enumerate(polys, 1)]
    features, geometries = to_shapely(
        features=features, transformer=None, on_invalid='fix')
    assert is_valid(geometries).tolist() == [
        False, True, False, False, False,
        False, False, False, True, True,
        True, False, True, False, False,
        False, False, False, True, False]
    assert is_valid_reason(geometries).tolist() == [
        None,
        'Valid Geometry',
        'Too few points in geometry component[7 8]',
        'Too few points in geometry component[7 8]',
        None,
        None,
        None,
        'Invalid Coordinate[nan nan]',
        'Valid Geometry',
        'Valid Geometry',
        'Valid Geometry',
        None,
        'Valid Geometry',
        'Self-intersection[5 3]',
        'Too few points in geometry component[12 15]',
        'Hole lies outside shell[50 50]',
        'Self-intersection[0.5 0.5]',
        'Invalid Coordinate[nan nan]',
        'Valid Geometry',
        'Too few points in geometry component[2 2]'
    ]
    assert is_empty(geometries).tolist() == [
        False, True, False, False, False,
        False, False, False, False, False,
        True, False, False, False, False,
        False, False, False, False, False]

    ids = array([fid for _, fid in features], dtype=int)
    deletes = []
    empties = []
    updates = []
    _repair_polygons(geometries, ids, deletes=deletes, empties=empties, updates=updates, has_m=has_m)
    assert deletes == [2, 11]
    assert set(empties) == {1, 5, 6, 7, 12}
    ids, polys = zip(*updates)
    assert all(poly.has_m is has_m for poly in polys)
    assert set(ids) == {3, 4, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20}
    assert all(isinstance(poly, ShapelyPolygon) for poly in polys)
    assert all(poly.has_z for poly in polys)
# End test_repair_polygons function


@mark.parametrize('has_m', [
    True,
    False,
])
def test_repair_multi_linestrings(has_m):
    """
    Test repair multi linestrings
    """
    if has_m:
        line1 = LineStringZM([(nan, nan, 1, 2), (1, 2, 3, 4), (nan, nan, nan, nan)], srs_id=4326)
        line2 = LineStringZM([], srs_id=4326)
        line3 = LineStringZM([(7, 8, 9, 10), (7, 8, 9, 10)], srs_id=4326)
        line4 = LineStringZM([(7, 8, 9, 10), (7, 8, 90, 100)], srs_id=4326)
        line5 = LineStringZM([(nan, nan, nan, nan), (nan, nan, nan, nan)], srs_id=4326)
        line6 = LineStringZM([(nan, nan, nan, nan), (5, 6, 7, 8)], srs_id=4326)
        line7 = LineStringZM([(0, 1, 2, 3), (2, 3, 4, 5)], srs_id=4326)
        line8 = LineStringZM([(1, 2, 3, 4), (nan, nan, nan, nan), (10, 20, 30, 40)], srs_id=4326)
        line9 = LineStringZM([(7, 8, 9, 10), (70, 80, 90, 100)], srs_id=4326)
        cls = MultiLineStringZM
    else:
        line1 = LineStringZ([(nan, nan, 1), (1, 2, 3), (nan, nan, nan)], srs_id=4326)
        line2 = LineStringZ([], srs_id=4326)
        line3 = LineStringZ([(7, 8, 9), (7, 8, 9)], srs_id=4326)
        line4 = LineStringZ([(7, 8, 9), (7, 8, 90)], srs_id=4326)
        line5 = LineStringZ([(nan, nan, nan), (nan, nan, nan)], srs_id=4326)
        line6 = LineStringZ([(nan, nan, nan), (5, 6, 7)], srs_id=4326)
        line7 = LineStringZ([(0, 1, 2), (2, 3, 4)], srs_id=4326)
        line8 = LineStringZ([(1, 2, 3), (nan, nan, nan), (10, 20, 30)], srs_id=4326)
        line9 = LineStringZ([(7, 8, 9), (70, 80, 90)], srs_id=4326)
        cls = MultiLineStringZ
    lines = line1, line2, line3, line4, line5, line6, line7, line8, line9
    multi = cls([line.coordinates for line in lines], srs_id=4326)
    features = [(multi, 0)]
    features, geometries = to_shapely(
        features=features, transformer=None, on_invalid='fix')
    assert is_valid(geometries).tolist() == [False]
    assert is_valid_reason(geometries).tolist() == [
        'Invalid Coordinate[nan nan]']
    assert is_empty(geometries).tolist() == [False]

    ids = array([fid for _, fid in features], dtype=int)
    deletes = []
    empties = []
    updates = []
    _repair_multi_linestrings(
        geometries, ids=ids, updates=updates, deletes=deletes,
        empties=empties, has_m=has_m)
    assert not deletes
    assert not empties
    ids, multi = updates[0]
    geoms = multi.geoms
    assert len(geoms) == 5
    assert all(line.has_m is has_m for line in geoms)
    assert all(line.has_z for line in geoms)
    assert all(isinstance(line, ShapelyLineString) for line in geoms)
    assert ids == 0
# End test_repair_multi_linestrings function


@mark.parametrize('has_m', [
    True,
    False
])
def test_repair_multi_polygons(has_m):
    """
    Test repair polygons
    """
    if has_m:
        poly1 = PolygonZM([[(nan, nan, 1, 2), (1, 2, 3, 4), (nan, nan, nan, nan)]], srs_id=4326)
        poly2 = PolygonZM([], srs_id=4326)
        poly3 = PolygonZM([[(7, 8, 9, 10), (7, 8, 9, 10), (7, 8, 9, 10), (7, 8, 9, 10), (7, 8, 9, 10)]], srs_id=4326)
        poly4 = PolygonZM([[(7, 8, 0, 100), (7, 8, 10, 200), (7, 18, 10, 300), (7, 18, 0, 400)]], srs_id=4326)
        poly5 = PolygonZM([[(nan, nan, nan, nan), (nan, nan, nan, nan), (nan, nan, nan, nan)]], srs_id=4326)
        poly6 = PolygonZM([[(nan, nan, nan, nan), (5, 6, 7, 8), (nan, nan, nan, nan)]], srs_id=4326)
        poly7 = PolygonZM([[(0, 1, 2, 3)]], srs_id=4326)
        poly8 = PolygonZM([[(0, 0, 3, 4), (nan, nan, nan, nan), (0, 1, 30, 40), (1, 1, 300, 400), (1, 0, 3000, 4000), (0, 0, 3, 4)]], srs_id=4326)
        poly9 = PolygonZM([[(0, 0, 3, 4), (0, 1, 30, 40), (1, 1, 300, 400), (1, 0, 3000, 4000), (0, 0, 3, 4)]], srs_id=4326)
        poly10 = PolygonZM([[(0, 0, 3, 4), (0, 1, 30, 40), (1, 1, 300, 400), (1, 0, 3000, 4000)]], srs_id=4326)
        poly11 = PolygonZM([[], []], srs_id=4326)
        poly12 = PolygonZM([[], [(0, 0, 3, 4), (1, 0, 5, 6), (1, 1, 7, 8), (0, 1, 9, 10), (0, 0, 3, 4)],
                            [(50, 50, 60, 70), (51, 50, 80, 90), (51, 51, 100, 110), (50, 51, 120, 130), (50, 50, 140, 150)]], srs_id=4326)
        poly13 = PolygonZM([[(0, 0, 3, 4), (0, 1, 30, 40), (1, 1, 300, 400), (1, 0, 3000, 4000)], [], []], srs_id=4326)
        poly14 = PolygonZM([[(0, 0, 3, 4), (10, 0, 5, 6), (10, 10, 7, 8), (0, 10, 9, 10), (0, 0, 3, 4)],
                            [(2, 2, 10, 11), (2, 5, 12, 13), (5, 5, 14, 15), (5, 2, 16, 17), (2, 2, 18, 19)],
                            [(3, 3, 20, 21), (3, 6, 22, 23), (6, 6, 24, 25), (6, 3, 26, 27), (3, 3, 28, 29)]], srs_id=4326)
        poly15 = PolygonZM([[(10, 20, 0, 1), (10, 30, 2, 3), (30, 30, 4, 5), (30, 20, 6, 7), (10, 20, 8, 9)],
                            [(12, 15, 50, 60), (12, 18, 70, 80)]], srs_id=4326)
        poly16 = PolygonZM([[(0, 0, 3, 4), (1, 0, 5, 6), (1, 1, 7, 8), (0, 1, 9, 10), (0, 0, 3, 4)],
                            [(50, 50, 60, 70), (51, 50, 80, 90), (51, 51, 100, 110), (50, 51, 120, 130), (50, 50, 140, 150)]], srs_id=4326)
        poly17 = PolygonZM([[(0, 0, 3, 4), (1, 1, 5, 6), (1, 0, 7, 8), (0, 1, 9, 10), (0, 0, 3, 4)]], srs_id=4326)
        poly18 = PolygonZM([[(0, 0, 3, 4), (1, 0, 5, 6), (nan, nan, nan, nan), (1, 1, 7, 8), (0, 1, 9, 10), (0, 0, 3, 4)],
                            [(50, 50, 60, 70), (51, 50, 80, 90), (51, 51, 100, 110), (50, 51, 120, 130), (50, 50, 140, 150)]], srs_id=4326)
        poly19 = PolygonZM([[(0, 0, 3, 4), (10, 0, 5, 6), (10, 10, 7, 8), (0, 10, 9, 10), (0, 0, 3, 4)],
                            [(2, 2, 10, 11), (2, 5, 12, 13), (5, 5, 14, 15)]], srs_id=4326)
        poly20 = PolygonZM([[(0, 0, 3, 4), (10, 0, 5, 6), (10, 10, 7, 8), (0, 10, 9, 10), (0, 0, 3, 4)],
                            [(2, 2, 10, 11), (2, 2.5, 12, 13)],
                            [(3, 3, 20, 21), (3, 6, 22, 23), (6, 6, 24, 25), (6, 3, 26, 27), (3, 3, 28, 29)]], srs_id=4326)
    else:
        poly1 = PolygonZ([[(nan, nan, 1), (1, 2, 3), (nan, nan, nan)]], srs_id=4326)
        poly2 = PolygonZ([], srs_id=4326)
        poly3 = PolygonZ([[(7, 8, 9), (7, 8, 9), (7, 8, 9), (7, 8, 9), (7, 8, 9)]], srs_id=4326)
        poly4 = PolygonZ([[(7, 8, 0), (7, 8, 10), (7, 18, 10), (7, 18, 0)]], srs_id=4326)
        poly5 = PolygonZ([[(nan, nan, nan), (nan, nan, nan), (nan, nan, nan)]], srs_id=4326)
        poly6 = PolygonZ([[(nan, nan, nan), (5, 6, 7), (nan, nan, nan)]], srs_id=4326)
        poly7 = PolygonZ([[(0, 1, 2)]], srs_id=4326)
        poly8 = PolygonZ([[(0, 0, 3), (nan, nan, nan), (0, 1, 30), (1, 1, 300), (1, 0, 3000), (0, 0, 3)]], srs_id=4326)
        poly9 = PolygonZ([[(0, 0, 3), (0, 1, 30), (1, 1, 300), (1, 0, 3000), (0, 0, 3)]], srs_id=4326)
        poly10 = PolygonZ([[(0, 0, 3), (0, 1, 30), (1, 1, 300), (1, 0, 3000)]], srs_id=4326)
        poly11 = PolygonZ([[], []], srs_id=4326)
        poly12 = PolygonZ([[], [(0, 0, 3), (1, 0, 5), (1, 1, 7), (0, 1, 9), (0, 0, 3)],
                            [(50, 50, 60), (51, 50, 80), (51, 51, 100), (50, 51, 120), (50, 50, 140)]], srs_id=4326)
        poly13 = PolygonZ([[(0, 0, 3), (0, 1, 30), (1, 1, 300), (1, 0, 3000)], [], []], srs_id=4326)
        poly14 = PolygonZ([[(0, 0, 3), (10, 0, 5), (10, 10, 7), (0, 10, 9), (0, 0, 3)],
                           [(2, 2, 10), (2, 5, 12), (5, 5, 14), (5, 2, 16), (2, 2, 18)],
                           [(3, 3, 20), (3, 6, 22), (6, 6, 24), (6, 3, 26), (3, 3, 28)]], srs_id=4326)
        poly15 = PolygonZ([[(10, 20, 0), (10, 30, 2), (30, 30, 4), (30, 20, 6), (10, 20, 8)],
                           [(12, 15, 50), (12, 18, 70)]], srs_id=4326)
        poly16 = PolygonZ([[(0, 0, 3), (1, 0, 5), (1, 1, 7), (0, 1, 9), (0, 0, 3)],
                           [(50, 50, 60), (51, 50, 80), (51, 51, 100), (50, 51, 120), (50, 50, 140)]], srs_id=4326)
        poly17 = PolygonZ([[(0, 0, 3), (1, 1, 5), (1, 0, 7), (0, 1, 9), (0, 0, 3)]], srs_id=4326)
        poly18 = PolygonZ([[(0, 0, 3), (1, 0, 5), (nan, nan, nan), (1, 1, 7), (0, 1, 9), (0, 0, 3)],
                           [(50, 50, 60), (51, 50, 80), (51, 51, 100), (50, 51, 120), (50, 50, 140)]], srs_id=4326)
        poly19 = PolygonZ([[(0, 0, 3), (10, 0, 5), (10, 10, 7), (0, 10, 9), (0, 0, 3)],
                           [(2, 2, 10), (2, 5, 12), (5, 5, 14)]], srs_id=4326)
        poly20 = PolygonZ([[(0, 0, 3), (10, 0, 5), (10, 10, 7), (0, 10, 9), (0, 0, 3)],
                           [(2, 2, 10), (2, 2.5, 12)],
                           [(3, 3, 20), (3, 6, 22), (6, 6, 24), (6, 3, 26), (3, 3, 28)]], srs_id=4326)
    polys = (poly1, poly2, poly3, poly4, poly5, poly6, poly7, poly8, poly9,
             poly10, poly11, poly12, poly13, poly14, poly15, poly16, poly17,
             poly18, poly19, poly20)
    features = [(poly, i) for i, poly in enumerate(polys, 1)]
    _, geometries = to_shapely(
        features=features, transformer=None, on_invalid='fix')
    geometries = [geom for geom in geometries if geom is not None]
    geometries = array([ShapelyMultiPolygon(geometries)], dtype=object)

    assert is_valid(geometries).tolist() == [False]
    assert is_valid_reason(geometries).tolist() == ['Too few points in geometry component[7 8]']
    assert is_empty(geometries).tolist() == [False]

    ids = array([0], dtype=int)
    deletes = []
    empties = []
    updates = []
    _repair_multi_polygons(geometries, ids, deletes=deletes, empties=empties,
                           updates=updates, has_m=has_m)
    assert not deletes
    assert not empties
    ids, multi = updates[0]
    geoms = multi.geoms
    assert len(geoms) == 13
    assert all(poly.has_m is has_m for poly in geoms)
    assert all(poly.has_z for poly in geoms)
    assert all(isinstance(poly, ShapelyPolygon) for poly in geoms)
    assert ids == 0
# End test_repair_multi_polygons function


if __name__ == '__main__':  # pragma: no cover
    pass
