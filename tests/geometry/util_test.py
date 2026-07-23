# -*- coding: utf-8 -*-
"""
Tests for Geometry Util Module
"""


from math import nan

from fudgeo.constant import WGS84
from fudgeo.geometry.point import Point, PointZ, PointZM
from numpy import array, ndarray
from pytest import mark, approx
from shapely import (
    Point as ShapelyPoint, LineString, MultiPoint, MultiLineString)
from shapely.geometry.base import GeometrySequence
from shapely.geometry.polygon import LinearRing

from spyops.geometry.enumeration import DimensionOption
from spyops.geometry.util import (
    ring_area_and_centroid, find_slice_indexes, get_geoms, get_geoms_iter,
    nada, to_shapely)


pytestmark = [mark.geometry]


@mark.parametrize('indexes, expected', [
    ([], ()),
    ([0, 0, 0, 0], (0, 4)),
    ([0, 0, 1, 1], (0, 2, 4)),
    ([0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2], (0, 3, 8, 12)),
])
def test_find_slice_indexes(indexes, expected):
    """
    Test find_slice_indexes
    """
    assert find_slice_indexes(array(indexes, dtype=int)) == expected
# End test_find_slice_indexes function


@mark.parametrize('value, expected', [
    (None, None),
    (2, 2),
    (Point, Point),
])
def test_nada(value, expected):
    """
    Test
    """
    assert nada(value) == expected
# End test_nada function


@mark.parametrize('geom, expected_count, expected_type', [
    (MultiPoint([ShapelyPoint(0, 0), ShapelyPoint(1, 1)]), 2, ShapelyPoint),
    (MultiLineString([[(0, 0), (1, 1)], [(2, 2), (3, 3)]]), 2, LineString),
])
def test_get_geoms(geom, expected_count, expected_type):
    """
    Test get_geoms for multi-part geometries
    """
    result = get_geoms(geom)
    assert isinstance(result, GeometrySequence)
    assert all(isinstance(geom, expected_type) for geom in result)
    assert len(result) == expected_count
# End test_get_geoms function


@mark.parametrize('geom, expected_count, expected_type', [
    (ShapelyPoint(0, 0), 1, list),
    (LineString([(0, 0), (1, 1)]), 1, list),
    (MultiPoint([ShapelyPoint(0, 0), ShapelyPoint(1, 1)]), 2, GeometrySequence),
    (MultiLineString([[(0, 0), (1, 1)], [(2, 2), (3, 3)]]), 2, GeometrySequence),
])
def test_get_geoms_iter(geom, expected_count, expected_type):
    """
    Test get_geoms_iter for single and multi-part geometries
    """
    result = get_geoms_iter(geom)
    assert isinstance(result, expected_type)
    assert len(list(result)) == expected_count
# End test_get_geoms_iter function


@mark.parametrize('features, expected_count, expected_type', [
    ([(Point(x=0.0, y=0.0, srs_id=WGS84),)], 1, ShapelyPoint),
    ([(Point(x=1.0, y=2.0, srs_id=WGS84),), (Point(x=3.0, y=4.0, srs_id=WGS84),)], 2, ShapelyPoint),
])
@mark.parametrize('option', [
    DimensionOption.TWO_D,
    DimensionOption.THREE_D,
    DimensionOption.SAME,
])
def test_to_shapely(features, expected_count, expected_type, option):
    """
    Test to_shapely conversion from Fudgeo to Shapely geometries
    """
    _, geometries = to_shapely(features, transformer=None, option=option)
    assert isinstance(geometries, ndarray)
    assert len(geometries) == expected_count
    assert all(isinstance(geom, expected_type) for geom in geometries)
# End test_to_shapely function


@mark.parametrize('features, expected_count, expected_type', [
    ([(Point(x=1, y=2, srs_id=WGS84),), (Point(x=nan, y=nan, srs_id=WGS84),)], 2, ShapelyPoint),
    ([(Point(x=1, y=2, srs_id=WGS84),), (Point.empty(WGS84),)], 2, ShapelyPoint),
    ([(PointZ(x=1, y=2, z=3, srs_id=WGS84),), (PointZ.empty(WGS84),)], 2, ShapelyPoint),
    ([(PointZ(x=1, y=2, z=nan, srs_id=WGS84),), (PointZ.empty(WGS84),)], 2, ShapelyPoint),
    ([(PointZ(x=nan, y=nan, z=3, srs_id=WGS84),), (PointZ.empty(WGS84),)], 2, ShapelyPoint),
    ([(PointZM(x=1, y=2, z=3, m=4, srs_id=WGS84),), (PointZM.empty(WGS84),)], 2, ShapelyPoint),
    ([(PointZM(x=1, y=2, z=nan, m=nan, srs_id=WGS84),), (PointZM.empty(WGS84),)], 2, ShapelyPoint),
    ([(PointZM(x=nan, y=nan, z=3, m=4, srs_id=WGS84),), (PointZM.empty(WGS84),)], 2, ShapelyPoint),
])
def test_to_shapely_fix(features, expected_count, expected_type):
    """
    Test to_shapely conversion from Fudgeo to Shapely geometries
    """
    _, geometries = to_shapely(features, transformer=None, on_invalid='fix')
    assert isinstance(geometries, ndarray)
    assert len(geometries) == expected_count
    assert all(isinstance(geom, expected_type) for geom in geometries)
# End test_to_shapely_fix function


def test_ring_area_and_centroid():
    """
    Test ring_area_and_centroid
    """
    coords = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    ring = LinearRing(coords)
    area, centroid = ring_area_and_centroid(ring, has_z=False, has_m=False, use_xy_length=True)
    assert area == 1
    assert centroid.tolist() == [0.5, 0.5]
    ring = LinearRing(list(reversed(coords)))
    area, centroid = ring_area_and_centroid(ring, has_z=False, has_m=False, use_xy_length=True)
    assert area == -1
    assert centroid.tolist() == [0.5, 0.5]
# End test_ring_area_and_centroid function


@mark.parametrize('use_xy_length, coords, expected_area, expected_centroid', [
    (True, [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 0]], 1, [0.5, 0.5, 0]),
    (False, [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 0]], 1, [0.5, 0.5, 0]),
    (True, [[0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1], [0, 0, 1]], 1, [0.5, 0.5, 1]),
    (False, [[0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1], [0, 0, 1]], 1, [0.5, 0.5, 1]),
    (True, [[0, 0, 0], [1, 0, 0], [1, 1, 1], [0, 1, 1], [0, 0, 0]], 1, [0.5, 0.5, 0.4444]),
    (False, [[0, 0, 0], [1, 0, 0], [1, 1, 1], [0, 1, 1], [0, 0, 0]], 1.4142, [0.5, 0.5, 0.5]),
    (True, [[0, 0, 0], [0, 0, 1], [1, 0, 1], [1, 0, 0], [0, 0, 0]], 0, [0.5, 0, 0.5]),
    (False, [[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1], [0, 0, 0]], -1, [0.5, 0, 0.5]),
])
def test_ring_area_and_centroid_length_options(use_xy_length, coords, expected_area, expected_centroid):
    """
    Test ring_area_and_centroid with different options for length calculation
    """
    ring = LinearRing(coords)
    area, centroid = ring_area_and_centroid(
        ring, has_z=True, has_m=False, use_xy_length=use_xy_length)
    assert approx(area, abs=0.001) == expected_area
    assert approx(centroid.tolist(), abs=0.001) == expected_centroid
# End test_ring_area_and_centroid_length_options function


if __name__ == '__main__':  # pragma: no cover
    pass
