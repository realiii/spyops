# -*- coding: utf-8 -*-
"""
Config tests
"""

from fudgeo.geometry.point import Point
from pytest import mark
from shapely import MultiPoint, Point as ShapelyPoint

from gisworks.geometry.config import geometry_config

pytestmark = [mark.geometry]


def test_geometry_config(inputs, world_features):
    """
    Test geometry config
    """
    fc = world_features['cities_p']
    config = geometry_config(fc)
    assert config.geometry_cls is Point
    assert config.is_multi is False
    assert config.filter_types == (ShapelyPoint, MultiPoint)
    assert config.srs_id == 4326
# End test_geometry_config function


if __name__ == '__main__':  # pragma: no cover
    pass
