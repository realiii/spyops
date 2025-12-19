# -*- coding: utf-8 -*-
"""
Tests for Geometry Module
"""


from fudgeo.geometry.point import Point
from pytest import approx, mark
from shapely import (
    MultiPolygon, MultiPoint as ShapelyMultiPoint, Point as ShapelyPoint)

from geomio.shared.geometry import (
    build_multi_polygon, extent_from_feature_class, overlay_config)


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


@mark.parametrize('name, expected', [
    ('admin_a', (-180.0, -90, 180, 83.6654911040001)),
    ('airports_p', (-177.38063597699997, -54.84327804999998, 178.5592279430001, 78.24611103500007)),
    ('roads_l', (-166.52854919433594, -54.97826385498047, 178.56739807128906, 70.48219299316406)),
])
def test_extent_from_feature_class(world_features, name, expected):
    """
    Test extent from feature class
    """
    fc = world_features[name]
    extent = extent_from_feature_class(fc)
    assert approx(extent, abs=0.000001) == expected
# End test_extent_from_feature_class function


if __name__ == '__main__':  # pragma: no cover
    pass
