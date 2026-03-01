# -*- coding: utf-8 -*-
"""
Tests for Geometry Util Module
"""


from math import nan

from fudgeo.constant import WGS84
from fudgeo.geometry.point import Point, PointZ, PointZM
from numpy import array, isnan, ndarray
from warnings import simplefilter, catch_warnings
from pytest import mark
from shapely import (
    Point as ShapelyPoint, LineString, MultiPoint, MultiLineString,
    MultiPolygon, get_coordinates, from_wkt)
from shapely.geometry.base import GeometrySequence

from spyops.geometry.enumeration import DimensionOption
from spyops.geometry.util import (
    find_slice_indexes, get_geoms, get_geoms_iter,
    nada, to_shapely)
from spyops.geometry.wa import (
    USE_WORKAROUNDS, make_valid_structure, set_precision)
from spyops.shared.exception import OperationsWarning


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


def test_make_valid():
    """
    Test Make Valid
    """
    a = from_wkt('Polygon ((0 0 0 0, 1 1 1 1, 0 1 2 3, 1 0 4 5, 0 0 0 0))')
    result = make_valid_structure(a)
    assert result.has_m
# End test_make_valid function


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


if __name__ == '__main__':  # pragma: no cover
    pass
