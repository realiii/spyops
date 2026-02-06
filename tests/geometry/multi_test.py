# -*- coding: utf-8 -*-
"""
Tests for Multi Geometry
"""

from pytest import approx, mark
from shapely import (
    MultiLineString as ShapelyMultiLineString, MultiPoint as ShapelyMultiPoint,
    MultiPolygon as ShapelyMultiPolygon)

from spyops.geometry.multi import build_multi


pytestmark = [mark.geometry]


def test_build_multi_polygon(inputs):
    """
    Test build multi polygon
    """
    fc = inputs['updater_a']
    assert len(fc) == 5
    polygon = build_multi(fc, transformer=None, select_sql='')
    assert isinstance(polygon, ShapelyMultiPolygon)
    assert approx(polygon.bounds, abs=0.0001) == (
        6.74573, 46.13702, 16.47727, 52.52511)
# End test_build_multi_polygon function


def test_build_multi_line_string(world_features):
    """
    Test build multi line string
    """
    fc = world_features['rivers_l']
    assert len(fc) == 136
    line = build_multi(fc, transformer=None, select_sql='')
    assert isinstance(line, ShapelyMultiLineString)
    assert approx(line.bounds, abs=0.0001) == (-164.88743, -36.96944, 160.76359, 71.39248)
# End test_build_multi_line_string function


def test_build_multi_point(world_features):
    """
    Test build multi point
    """
    fc = world_features['airports_p']
    assert len(fc) == 3500
    line = build_multi(fc, transformer=None, select_sql='')
    assert isinstance(line, ShapelyMultiPoint)
    assert approx(line.bounds, abs=0.0001) == (-177.38063, -54.84327, 178.55922, 78.24611)
# End test_build_multi_line_string function


if __name__ == '__main__':  # pragma: no cover
    pass
