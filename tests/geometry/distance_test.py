# -*- coding: utf-8 -*-
"""
Tests for Distance
"""


from math import nan

from fudgeo.enumeration import ShapeType
from numpy.ma.core import arange
from pytest import mark, approx
from numpy import cumsum
from shapely.coordinates import get_coordinates
from shapely.geometry.linestring import LineString
from shapely.geometry.multilinestring import MultiLineString
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon
from shapely.measurement import length

from spyops.geometry.convert import GEOMETRY_AS_MULTILINE
from spyops.geometry.distance import (
    _group_by_line_index,
    interpolate_locations, make_points, _add_end_locations)
from spyops.geometry.util import find_slice_indexes, get_geoms


pytestmark = [mark.geometry]


@mark.parametrize('shape_type, geom, expected', [
    (ShapeType.linestring, LineString([(0, 0), (0, 20)]), {0: [5, 15]}),
    (ShapeType.multi_linestring, LineString([(0, 0), (0, 20)]), {0: [5, 15]}),
    (ShapeType.multi_linestring, MultiLineString(
        [LineString([(0, 0), (0, 10)]), LineString([(0, 10), (0, 20)])]), {0: [5], 1: [15]}),
    (ShapeType.polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), {0: [5, 15]}),
    (ShapeType.multi_polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), {0: [5, 15]}),
    (ShapeType.multi_polygon, MultiPolygon(
        [Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]),
         Polygon([(10, 10), (10, 15), (15, 15), (15, 10)])]), {0: [5, 15, 20], 1: [30]}),
])
def test_group_by_line_index(shape_type, geom, expected):
    """
    Test Group by Line Index
    """
    values = -10, 0, 5, 15, 20, 30
    getter = GEOMETRY_AS_MULTILINE[shape_type]
    lines = getter(geom)
    lengths = cumsum(length(get_geoms(lines)))
    result = _group_by_line_index(lengths, values)
    assert result == expected
# End test_group_by_line_index function


@mark.parametrize('coords, has_z, has_m, expected', [
    ([0, 1, 2, 3], False, False, (0, 1)),
    ([0, 1, 2, 3], True, False, (0, 1, 2)),
    ([0, 1, 2, 3], True, True, (0, 1, 2, 3)),
    ([0, 1, 2, 3], False, True, (0, 1, 3)),
])
def test_make_points(coords, has_z, has_m, expected):
    """
    Test make points
    """
    points = make_points([(coords, 1, 2, 3)], has_z=has_z, has_m=has_m)
    assert len(points) == 1
    pt, = points
    assert pt.has_z == has_z
    assert pt.has_m == has_m
    coordinates = get_coordinates(pt, include_m=has_m, include_z=has_z)
    assert tuple(coordinates[0]) == expected
# End test_make_points function


@mark.parametrize('shape_type, geom, expected', [
    (ShapeType.multi_polygon, MultiPolygon(
        [Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]),
         Polygon([(10, 10), (10, 15), (15, 15), (15, 10)])]), (10, 10, nan, nan)),
    (ShapeType.multi_linestring, MultiLineString(
        [LineString([(0, 0), (0, 5), (5, 5), (5, 0)]),
         LineString([(10, 10), (10, 15), (15, 15), (15, 10)])]), (15, 10, nan, nan)),
])
def test_add_end_locations(shape_type, geom, expected):
    """
    Test add end locations
    """
    fid = 12345
    multi = GEOMETRY_AS_MULTILINE[shape_type](geom)
    coordinates, indexes = get_coordinates(
        multi, include_z=True, include_m=True, return_index=True)
    ids = find_slice_indexes(indexes)
    records = [([0, 1, 2, 3], fid, 1, 50)]
    _add_end_locations(coordinates, ids=ids, records=records,
                       fid=fid, total_length=100)
    (first_location, *first_attrs), _, (last_location, *last_attrs) = records
    assert approx(tuple(first_location), nan_ok=True, abs=0.1) == (0, 0, nan, nan)
    assert first_attrs == [fid, 1, 0.0]
    assert approx(tuple(last_location), nan_ok=True, abs=0.1) == expected
    assert last_attrs == [fid, 3, 100.0]
# End test_add_end_locations function


@mark.parametrize('include_ends, shape_type, geom, expected', [
    (True, ShapeType.linestring, LineString([(0, 0), (0, 20)]), (0, 3, 8, 13, 18, 20)),
    (True, ShapeType.multi_linestring, LineString([(0, 0), (0, 20)]), (0, 3, 8, 13, 18, 20)),
    (True, ShapeType.multi_linestring, MultiLineString(
        [LineString([(0, 0), (0, 10)]), LineString([(0, 10), (0, 20)])]), (0, 3, 8, 13, 18, 20)),
    (True, ShapeType.polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), (0, 3, 8, 13, 18, 20)),
    (True, ShapeType.multi_polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), (0, 3, 8, 13, 18, 20)),
    (True, ShapeType.multi_polygon, MultiPolygon(
        [Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]),
         Polygon([(10, 10), (10, 15), (15, 15), (15, 10)])]), (0, 3, 8, 13, 18, 23, 28, 33, 38, 40)),
])
def test_interpolate_locations(include_ends, shape_type, geom, expected):
    """
    Test interpolate locations
    """
    fid = 12345
    values = arange(3, 50, 5, dtype=float)
    getter = GEOMETRY_AS_MULTILINE[shape_type]
    lines = get_geoms(getter(geom))
    lengths = cumsum(length(lines))
    coordinates, indexes = get_coordinates(
        lines, include_z=True, include_m=True, return_index=True)
    ids = find_slice_indexes(indexes)
    results = interpolate_locations(
        values, lengths=lengths, coordinates=coordinates, ids=ids, fid=fid,
        include_ends=include_ends)
    _, fid, seq, along = zip(*results)
    assert set(fid) == set(fid)
    assert tuple(seq) == tuple(range(1, len(results) + 1))
    assert along == expected
# End test_interpolate_locations function


if __name__ == '__main__':  # pragma: no cover
    pass
