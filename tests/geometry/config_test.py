# -*- coding: utf-8 -*-
"""
Config tests
"""


from fudgeo.geometry import PointZM
from fudgeo.geometry.point import Point
from pytest import mark
from shapely import (
    MultiPoint as ShapelyMultiPoint, Point as ShapelyPoint, MultiLineString)
from shapely.io import from_wkt

from gisworks.geometry.config import (
    GeometryConfig, geometry_config, _combine_lines_workaround)
from gisworks.geometry.util import nada


pytestmark = [mark.geometry]


def test_geometry_config(inputs, world_features):
    """
    Test geometry config
    """
    fc = world_features['cities_p']
    config = geometry_config(fc, cast_geom=False)
    assert config.geometry_cls is Point
    assert config.is_multi is False
    assert config.filter_types == (ShapelyPoint, ShapelyMultiPoint)
    assert config.srs_id == 4326
    assert config.caster is None
    assert config.combiner is nada
# End test_geometry_config function


def test_geometry_config_creation():
    """
    Test GeometryConfig
    """
    oc = GeometryConfig(
        geometry_cls=PointZM, is_multi=False,
        filter_types=(ShapelyPoint, ShapelyMultiPoint), srs_id=4326,
        combiner=nada, caster=None
    )
    assert oc.geometry_cls is PointZM
    assert oc.is_multi is False
    assert oc.filter_types == (ShapelyPoint, ShapelyMultiPoint)
    assert oc.srs_id == 4326
    assert oc.combiner is nada
    assert oc.caster is None
# End test_geometry_config_creation function


@mark.parametrize('geom, expected', [
    ('LineString (0 1 2 3, 4 5 6 7)', 'LINESTRING ZM (0 1 2 3, 4 5 6 7)'),
    (MultiLineString([from_wkt('LineString (0 1 2 3, 4 5 6 7)'), from_wkt('LineString (8 9 10 11, 12 13 14 15)')]),
     'MULTILINESTRING ZM ((0 1 2 3, 4 5 6 7), (8 9 10 11, 12 13 14 15))'),
    (MultiLineString([from_wkt('LineString (0 1 2 3, 4 5 6 7)'), from_wkt('LineString (4 5 6 7, 8 9 10 11, 12 13 14 15)')]),
     'LINESTRING ZM (0 1 2 3, 4 5 6 7, 8 9 10 11, 12 13 14 15)'),
    (MultiLineString([from_wkt('LineString (0 1 2 3, 0 1 6 7)'), from_wkt('LineString (0 1 6 7, 0 1 10 11, 0 1 14 15)')]),
     'MULTILINESTRING ZM ((0 1 2 3, 0 1 6 7), (0 1 6 7, 0 1 10 11, 0 1 14 15))'),
])
def test_combine_lines_workaround(geom, expected):
    """
    Test Combine Lines Workaround
    """
    if isinstance(geom, str):
        geom = from_wkt(geom)
    result = _combine_lines_workaround(geom)
    assert result.wkt == expected
# End test_combine_lines_workaround function


if __name__ == '__main__':  # pragma: no cover
    pass
