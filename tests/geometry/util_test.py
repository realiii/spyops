# -*- coding: utf-8 -*-
"""
Tests for Geometry Util Module
"""


from fudgeo.constant import WGS84
from fudgeo.geometry.point import Point
from pytest import mark
from shapely import (
    Point as ShapelyPoint, LineString, MultiPoint, MultiLineString)
from shapely.geometry.base import GeometrySequence

from gisworks.geometry.util import (
    USE_WORKAROUNDS, get_geoms, get_geoms_iter,
    nada, to_shapely)

pytestmark = [mark.geometry]


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
def test_to_shapely(features, expected_count, expected_type):
    """
    Test to_shapely conversion from Fudgeo to Shapely geometries
    """
    result = to_shapely(features)
    assert isinstance(result, list)
    assert len(result) == expected_count
    assert all(isinstance(geom, expected_type) for geom in result)
# End test_to_shapely function


def test_use_workarounds():
    """
    Test USE_WORKAROUNDS
    """
    assert USE_WORKAROUNDS.make_valid is True
    assert USE_WORKAROUNDS.simplify is True
    assert USE_WORKAROUNDS.coverage_simplify is True
    assert USE_WORKAROUNDS.polygonize is True
    assert USE_WORKAROUNDS.line_merge is True
    assert USE_WORKAROUNDS.set_precision is True
    assert USE_WORKAROUNDS.inconsistent_zm_source is True
    assert USE_WORKAROUNDS.point_intersection is True
    assert USE_WORKAROUNDS.point_interpolation is True
    assert USE_WORKAROUNDS.geometry_order_interpolation is True
    assert USE_WORKAROUNDS.dropped_nan_measures is True
# End test_use_workarounds function


if __name__ == '__main__':  # pragma: no cover
    pass
