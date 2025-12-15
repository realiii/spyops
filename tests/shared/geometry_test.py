# -*- coding: utf-8 -*-
"""
Tests for Geometry Module
"""


from fudgeo.geometry.point import Point
from pytest import approx, mark
from shapely import (
    MultiPolygon, MultiPoint as ShapelyMultiPoint, Point as ShapelyPoint)

from geomio.shared.geometry import (
    build_multi_polygon, overlay_config)


pytestmark = [mark.geometry]


def test_build_multi_polygon(inputs):
    """
    Test build multi polygon
    """
    fc = inputs['updater_a']
    assert fc.count == 5
    polygon = build_multi_polygon(fc)
    assert isinstance(polygon, MultiPolygon)
    assert approx(polygon.bounds, abs=0.0001) == (
        6.74573, 46.13702, 16.47727, 52.52511)
# End test_build_multi_polygon function


def test_overlay_config(inputs, world_features):
    """
    Test overlay config
    """
    operator = inputs['updater_a']
    fc = world_features['cities_p']
    config = overlay_config(fc, operator=operator)
    assert config.fudgeo_cls is Point
    assert config.is_multi is False
    assert config.shapely_multi_cls is ShapelyMultiPoint
    assert approx(config.geometry.bounds, abs=0.0001) == (
        6.74573, 46.13702, 16.47727, 52.52511)
    assert config.shapely_types == (ShapelyPoint, ShapelyMultiPoint)
# End test_overlay_config function


if __name__ == '__main__':  # pragma: no cover
    pass
