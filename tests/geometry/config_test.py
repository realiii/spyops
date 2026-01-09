# -*- coding: utf-8 -*-
"""
Config tests
"""


from fudgeo.geometry import PointZM
from fudgeo.geometry.point import Point
from pytest import mark
from shapely import MultiPoint as ShapelyMultiPoint, Point as ShapelyPoint

from gisworks.geometry.config import GeometryConfig, geometry_config
pytestmark = [mark.geometry]


def test_geometry_config(inputs, world_features):
    """
    Test geometry config
    """
    fc = world_features['cities_p']
    config = geometry_config(fc)
    assert config.geometry_cls is Point
    assert config.is_multi is False
    assert config.filter_types == (ShapelyPoint, ShapelyMultiPoint)
    assert config.srs_id == 4326
# End test_geometry_config function


def test_geometry_config_creation():
    """
    Test GeometryConfig
    """
    oc = GeometryConfig(
        geometry_cls=PointZM, is_multi=False,
        filter_types=(ShapelyPoint, ShapelyMultiPoint), srs_id=4326, combiner=lambda x: x
    )
    assert oc.geometry_cls is PointZM
    assert oc.is_multi is False
    assert oc.filter_types == (ShapelyPoint, ShapelyMultiPoint)
    assert oc.srs_id == 4326
# End test_geometry_config_creation function


if __name__ == '__main__':  # pragma: no cover
    pass
