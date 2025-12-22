# -*- coding: utf-8 -*-
"""
Tests for Overlay
"""


from fudgeo import FeatureClass
from pytest import mark, param

from geomio.analysis.overlay import erase
from geomio.analysis.sql import build_analysis

pytestmark = [mark.overlay]


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
def test_erase(inputs, world_features, fresh_gpkg, fc_name, xy_tolerance, count):
    """
    Test erase
    """
    eraser = inputs['eraser_a']
    assert eraser.count == 5
    source = world_features[fc_name]
    assert source.is_multi_part == ('mp' in fc_name)
    target = FeatureClass(geopackage=fresh_gpkg, name=f'temp_{fc_name}')
    components = build_analysis(source=source, target=target, operator=eraser, use_empty=True)
    _, touches = components.sql_intersect.split('WHERE', 1)
    subset = source.copy(f'subset_{fc_name}', where_clause=touches, geopackage=fresh_gpkg)
    assert subset.count <= source.count
    target = FeatureClass(geopackage=fresh_gpkg, name=fc_name)
    result = erase(source=subset, operator=eraser, target=target, xy_tolerance=xy_tolerance)
    assert result.count == count
# End test_erase function


if __name__ == '__main__':  # pragma: no cover
    pass
