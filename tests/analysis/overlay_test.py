# -*- coding: utf-8 -*-
"""
Tests for Overlay
"""


from fudgeo import FeatureClass
from pytest import mark, param

from geomio.analysis.overlay import erase, intersect
from geomio.shared.enumeration import AttributeOption, Setting
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
    assert len(eraser) == 5
    source = world_features[fc_name]
    assert source.is_multi_part == ('mp' in fc_name)
    target = FeatureClass(geopackage=fresh_gpkg, name=f'temp_{fc_name}')
    query = QueryErase(source=source, target=target, operator=eraser)
    _, touches = query.select.split('WHERE', 1)
    subset = source.copy(f'subset_{fc_name}', where_clause=touches, geopackage=fresh_gpkg)
    assert len(subset) <= len(source)
    target = FeatureClass(geopackage=fresh_gpkg, name=fc_name)
    result = erase(source=subset, operator=eraser, target=target, xy_tolerance=xy_tolerance)
    assert len(result) == count
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
    assert len(eraser) == 5
    source = world_features[fc_name]
    assert source.is_multi_part == ('mp' in fc_name)
    target = FeatureClass(geopackage=fresh_gpkg, name=fc_name)
    result = erase(source=source, operator=eraser, target=target, xy_tolerance=xy_tolerance)
    assert len(result) == count
# End test_erase function


@mark.parametrize('fc_name, xy_tolerance, option, feature_count, field_count', [
    ('admin_a', None, AttributeOption.ALL, 114, 25),
    ('airports_p', None, AttributeOption.ALL, 40, 14),
    ('roads_l', None, AttributeOption.ALL, 2514, 22),
    ('admin_mp_a', None, AttributeOption.ALL, 68, 23),
    ('airports_mp_p', None, AttributeOption.ALL, 8, 11),
    ('roads_mp_l', None, AttributeOption.ALL, 14, 11),
    ('admin_a', 0.001, AttributeOption.ALL, 112, 25),
    ('airports_p', 0.001, AttributeOption.ALL, 40, 14),
    ('roads_l', 0.001, AttributeOption.ALL, 3380, 22),
    ('admin_mp_a', 0.001, AttributeOption.ALL, 68, 23),
    ('airports_mp_p', 0.001, AttributeOption.ALL, 8, 11),
    ('roads_mp_l', 0.001, AttributeOption.ALL, 14, 11),
    ('admin_a', 1, AttributeOption.ALL, 22, 25),
    ('airports_p', 1, AttributeOption.ALL, 35, 14),
    ('roads_l', 1, AttributeOption.ALL, 378, 22),
    ('admin_mp_a', 1, AttributeOption.ALL, 22, 23),
    ('airports_mp_p', 1, AttributeOption.ALL, 8, 11),
    ('roads_mp_l', 1, AttributeOption.ALL, 13, 11),
    ('admin_a', None, AttributeOption.ONLY_FID, 114, 4),
    ('airports_p', None, AttributeOption.ONLY_FID, 40, 4),
    ('roads_l', None, AttributeOption.ONLY_FID, 2514, 4),
    ('admin_mp_a', None, AttributeOption.ONLY_FID, 68, 4),
    ('airports_mp_p', None, AttributeOption.ONLY_FID, 8, 4),
    ('roads_mp_l', None, AttributeOption.ONLY_FID, 14, 4),
    ('admin_a', 0.001, AttributeOption.ONLY_FID, 112, 4),
    ('airports_p', 0.001, AttributeOption.ONLY_FID, 40, 4),
    ('roads_l', 0.001, AttributeOption.ONLY_FID, 3380, 4),
    ('admin_mp_a', 0.001, AttributeOption.ONLY_FID, 68, 4),
    ('airports_mp_p', 0.001, AttributeOption.ONLY_FID, 8, 4),
    ('roads_mp_l', 0.001, AttributeOption.ONLY_FID, 14, 4),
    ('admin_a', 1, AttributeOption.ONLY_FID, 22, 4),
    ('airports_p', 1, AttributeOption.ONLY_FID, 35, 4),
    ('roads_l', 1, AttributeOption.ONLY_FID, 378, 4),
    ('admin_mp_a', 1, AttributeOption.ONLY_FID, 22, 4),
    ('airports_mp_p', 1, AttributeOption.ONLY_FID, 8, 4),
    ('roads_mp_l', 1, AttributeOption.ONLY_FID, 13, 4),
    ('admin_a', None, AttributeOption.SANS_FID, 114, 23),
    ('airports_p', None, AttributeOption.SANS_FID, 40, 12),
    ('roads_l', None, AttributeOption.SANS_FID, 2514, 20),
    ('admin_mp_a', None, AttributeOption.SANS_FID, 68, 21),
    ('airports_mp_p', None, AttributeOption.SANS_FID, 8, 9),
    ('roads_mp_l', None, AttributeOption.SANS_FID, 14, 9),
    ('admin_a', 0.001, AttributeOption.SANS_FID, 112, 23),
    ('airports_p', 0.001, AttributeOption.SANS_FID, 40, 12),
    ('roads_l', 0.001, AttributeOption.SANS_FID, 3380, 20),
    ('admin_mp_a', 0.001, AttributeOption.SANS_FID, 68, 21),
    ('airports_mp_p', 0.001, AttributeOption.SANS_FID, 8, 9),
    ('roads_mp_l', 0.001, AttributeOption.SANS_FID, 14, 9),
    ('admin_a', 1, AttributeOption.SANS_FID, 22, 23),
    ('airports_p', 1, AttributeOption.SANS_FID, 35, 12),
    ('roads_l', 1, AttributeOption.SANS_FID, 378, 20),
    ('admin_mp_a', 1, AttributeOption.SANS_FID, 22, 21),
    ('airports_mp_p', 1, AttributeOption.SANS_FID, 8, 9),
    ('roads_mp_l', 1, AttributeOption.SANS_FID, 13, 9),
])
def test_intersect_setting(inputs, world_features, mem_gpkg, fc_name, xy_tolerance,
                           option, feature_count, field_count):
    """
    Test intersect using analysis settings
    """
    operator = inputs['intersect_a']
    assert len(operator) == 5
    source = world_features[fc_name]
    target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
    with Swap(Setting.XY_TOLERANCE, xy_tolerance):
        result = intersect(source=source, operator=operator, target=target,
                           attribute_option=option)
    assert len(result) < len(source)
    assert len(result) == feature_count
    assert len(result.fields) == field_count
# End test_intersect_setting function


if __name__ == '__main__':  # pragma: no cover
    pass
