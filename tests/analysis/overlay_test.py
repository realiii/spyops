# -*- coding: utf-8 -*-
"""
Tests for Overlay
"""


from fudgeo import FeatureClass
from pytest import mark, param

from geomio.analysis.overlay import erase, intersect
from geomio.shared.enumeration import Setting
from geomio.query.overlay import QueryErase
from geomio.shared.setting import Swap


pytestmark = [mark.overlay, mark.query]


@mark.parametrize('fc_name, xy_tolerance, count', [
    ('admin_a', None, 245),
    ('airports_p', None, 29),
    ('roads_l', None, 3054),
    ('admin_mp_a', None, 217),
    ('airports_mp_p', None, 10),
    ('roads_mp_l', None, 14),
    ('admin_a', 0.001, 286),
    ('airports_p', 0.001, 29),
    ('roads_l', 0.001, 3126),
    ('admin_mp_a', 0.001, 217),
    ('airports_mp_p', 0.001, 10),
    param('roads_mp_l', 0.001, 14, marks=mark.slow),
    ('admin_a', 1, 41),
    ('airports_p', 1, 33),
    ('roads_l', 1, 338),
    ('admin_mp_a', 1, 37),
    ('airports_mp_p', 1, 10),
    ('roads_mp_l', 1, 14),
])
def test_erase_reduced(inputs, world_features, fresh_gpkg, fc_name, xy_tolerance, count):
    """
    Test erase -- reduced data for faster testing
    """
    eraser = inputs['eraser_a']
    assert eraser.count == 5
    source = world_features[fc_name]
    assert source.is_multi_part == ('mp' in fc_name)
    target = FeatureClass(geopackage=fresh_gpkg, name=f'temp_{fc_name}')
    query = QueryErase(source=source, target=target, operator=eraser)
    _, touches = query.select.split('WHERE', 1)
    subset = source.copy(f'subset_{fc_name}', where_clause=touches, geopackage=fresh_gpkg)
    assert subset.count <= source.count
    target = FeatureClass(geopackage=fresh_gpkg, name=fc_name)
    result = erase(source=subset, operator=eraser, target=target, xy_tolerance=xy_tolerance)
    assert result.count == count
# End test_erase_reduced function


@mark.parametrize('fc_name, xy_tolerance, count', [
    ('airports_p', None, 3464),
    ('airports_mp_p', None, 191),
    ('airports_p', 0.001, 3464),
    ('airports_mp_p', 0.001, 191),
])
def test_erase(inputs, world_features, fresh_gpkg, fc_name, xy_tolerance, count):
    """
    Test erase - ensure that disjoint is exercised
    """
    eraser = inputs['eraser_a']
    assert eraser.count == 5
    source = world_features[fc_name]
    assert source.is_multi_part == ('mp' in fc_name)
    target = FeatureClass(geopackage=fresh_gpkg, name=fc_name)
    result = erase(source=source, operator=eraser, target=target, xy_tolerance=xy_tolerance)
    assert result.count == count
# End test_erase function


@mark.parametrize('fc_name, xy_tolerance, count', [
    ('admin_a', None, 114),
    ('airports_p', None, 40),
    ('roads_l', None, 2514),
    ('admin_mp_a', None, 68),
    ('airports_mp_p', None, 8),
    ('roads_mp_l', None, 14),
    ('admin_a', 0.001, 112),
    ('airports_p', 0.001, 40),
    ('roads_l', 0.001, 3380),
    ('admin_mp_a', 0.001, 68),
    ('airports_mp_p', 0.001, 8),
    ('roads_mp_l', 0.001, 14),
    ('admin_a', 1, 22),
    ('airports_p', 1, 35),
    ('roads_l', 1, 378),
    ('admin_mp_a', 1, 22),
    ('airports_mp_p', 1, 8),
    ('roads_mp_l', 1, 13),
])
def test_intersect_setting(inputs, world_features, mem_gpkg, fc_name, xy_tolerance, count):
    """
    Test intersect using analysis settings
    """
    operator = inputs['intersect_a']
    assert operator.count == 5
    source = world_features[fc_name]
    target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
    with Swap(Setting.XY_TOLERANCE, xy_tolerance):
        result = intersect(source=source, operator=operator, target=target)
    assert result.count < source.count
    assert result.count == count
# End test_intersect_setting function


if __name__ == '__main__':  # pragma: no cover
    pass
