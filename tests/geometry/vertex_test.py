# -*- coding: utf-8 -*-
"""
Vertex Tests
"""


from bottleneck import nanmean
from pytest import mark, approx

from spyops.geometry.vertex import (
    GEOMETRY_VERTICES_ALL, GEOMETRY_VERTICES_BOTH_ENDS, GEOMETRY_VERTICES_END,
    GEOMETRY_VERTICES_MIDDLE, GEOMETRY_VERTICES_START)


pytestmark = [mark.geometry]


@mark.parametrize('fc_name, expected', [
    ('admin_a', {1: 2831, 2: 1101, 3: 1064, 4: 1017, 5: 1193}),
    ('admin_mp_a', {1: 2831, 2: 1101, 3: 1064, 4: 1017, 5: 1193}),
    ('roads_l', {1: 2, 2: 3, 3: 10, 4: 2, 5: 13}),
    ('roads_ml', {1: 3420, 2: 14736, 3: 281, 4: 110052, 5: 13376}),
    ('airports_p', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('airports_mp_p', {1: 8, 2: 2, 3: 1, 4: 1, 5: 3}),
])
def test_all_vertices(world_features, fc_name, expected):
    """
    Test all vertices
    """
    source = world_features[fc_name]
    features = source.select(include_primary=True, limit=5).fetchall()
    func = GEOMETRY_VERTICES_ALL[source.shape_type]
    result = func(features)
    counts = {k: len(v) for k, v in result.items()}
    assert counts == expected
# End test_all_vertices function


@mark.parametrize('fc_name, expected', [
    ('admin_a', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('admin_mp_a', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('roads_l', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('roads_ml', {1: 191, 2: 418, 3: 11, 4: 4762, 5: 697}),
    ('airports_p', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('airports_mp_p', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
])
def test_start_vertices(world_features, fc_name, expected):
    """
    Test start vertices
    """
    source = world_features[fc_name]
    features = source.select(include_primary=True, limit=5).fetchall()
    func = GEOMETRY_VERTICES_START[source.shape_type]
    result = func(features)
    counts = {k: len(v) for k, v in result.items()}
    assert counts == expected
# End test_start_vertices function


@mark.parametrize('fc_name, expected', [
    ('admin_a', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('admin_mp_a', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('roads_l', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('roads_ml', {1: 191, 2: 418, 3: 11, 4: 4762, 5: 697}),
    ('airports_p', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('airports_mp_p', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
])
def test_end_vertices(world_features, fc_name, expected):
    """
    Test end vertices
    """
    source = world_features[fc_name]
    features = source.select(include_primary=True, limit=5).fetchall()
    func = GEOMETRY_VERTICES_END[source.shape_type]
    result = func(features)
    counts = {k: len(v) for k, v in result.items()}
    assert counts == expected
# End test_end_vertices function


@mark.parametrize('fc_name, expected', [
    ('admin_a', {1: 2, 2: 2, 3: 2, 4: 2, 5: 2}),
    ('admin_mp_a', {1: 2, 2: 2, 3: 2, 4: 2, 5: 2}),
    ('roads_l', {1: 2, 2: 2, 3: 2, 4: 2, 5: 2}),
    ('roads_ml', {1: 382, 2: 836, 3: 22, 4: 9524, 5: 1394}),
    ('airports_p', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('airports_mp_p', {1: 2, 2: 2, 3: 2, 4: 2, 5: 2}),
])
def test_both_ends_vertices(world_features, fc_name, expected):
    """
    Test both_ends vertices
    """
    source = world_features[fc_name]
    features = source.select(include_primary=True, limit=5).fetchall()
    func = GEOMETRY_VERTICES_BOTH_ENDS[source.shape_type]
    result = func(features)
    counts = {k: len(v) for k, v in result.items()}
    assert counts == expected
# Both_Ends test_both_ends_vertices function


@mark.parametrize('fc_name, expected', [
    ('admin_a', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('admin_mp_a', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('roads_l', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('roads_ml', {1: 191, 2: 418, 3: 11, 4: 4762, 5: 697}),
    ('airports_p', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
    ('airports_mp_p', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}),
])
def test_mid_vertices(world_features, fc_name, expected):
    """
    Test mid vertices
    """
    source = world_features[fc_name]
    features = source.select(include_primary=True, limit=5).fetchall()
    func = GEOMETRY_VERTICES_MIDDLE[source.shape_type]
    result = func(features, has_z=source.has_z, has_m=source.has_m,
                  srs_id=source.spatial_reference_system.srs_id)
    counts = {k: len(v) for k, v in result.items()}
    assert counts == expected
# End test_mid_vertices function


@mark.zm
@mark.parametrize('fc_name, expected, avg_z, avg_m', [
    ('hydro_6654_a', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 0, 0),
    ('hydro_6654_z_a', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 1230.3839, 0),
    ('hydro_6654_m_a', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 0, 101007.0956),
    ('hydro_6654_zm_a', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 1230.3839, 201007.0956),
    ('structures_10tm_ma', {1: 7, 2: 1, 3: 156, 4: 1, 5: 8}, 0, 101003.3288),
    ('structures_10tm_z_ma', {1: 7, 2: 1, 3: 156, 4: 1, 5: 8}, 1099.0560, 0),
    ('structures_10tm_m_ma', {1: 7, 2: 1, 3: 156, 4: 1, 5: 8}, 0, 101003.3288),
    ('structures_10tm_zm_ma', {1: 7, 2: 1, 3: 156, 4: 1, 5: 8}, 1099.0560, 201003.3288),
    ('transmission_10tm_l', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 0, 0),
    ('transmission_10tm_z_l', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 1158.5081, 0),
    ('transmission_10tm_m_l', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 0, 300002.4131),
    ('transmission_10tm_zm_l', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 1158.5081, 400002.4131),
    ('transmission_10tm_ml', {1: 1, 2: 7, 3: 5, 4: 38}, 0, 0),
    ('transmission_10tm_z_ml', {1: 1, 2: 7, 3: 5, 4: 38}, 1166.1410, 0),
    ('transmission_10tm_m_ml', {1: 1, 2: 7, 3: 5, 4: 38}, 0, 134441.9674),
    ('transmission_10tm_zm_ml', {1: 1, 2: 7, 3: 5, 4: 38}, 1166.1410, 234441.9674),
    ('toponymy_6654_mp', {1: 1}, 0, 0),
    ('toponymy_6654_z_mp', {1: 1}, 1111.3894, 0),
    ('toponymy_6654_m_mp', {1: 1}, 0, 500068.1239),
    ('toponymy_6654_zm_mp', {1: 1}, 1111.3894, 600068.1239),
    ('transmission_p', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 0, 0),
    ('transmission_z_p', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 1162.7429, 0),
    ('transmission_m_p', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 0, 500015.6),
    ('transmission_zm_p', {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 1162.7429, 600015.6),
])
def test_mid_vertices_zm(ntdb_zm_small, fc_name, expected, avg_z, avg_m):
    """
    Test mid vertices
    """
    source = ntdb_zm_small[fc_name]
    features = source.select(include_primary=True, limit=5).fetchall()
    func = GEOMETRY_VERTICES_MIDDLE[source.shape_type]
    result = func(features, has_z=source.has_z, has_m=source.has_m,
                  srs_id=source.spatial_reference_system.srs_id)
    counts = {k: len(v) for k, v in result.items()}
    assert counts == expected
    points = sum(result.values(), [])
    if source.has_z:
        assert approx(nanmean([pt.z for pt in points]), abs=0.001) == avg_z
    if source.has_m:
        assert approx(nanmean([pt.m for pt in points]), abs=0.001) == avg_m
# End test_mid_vertices_zm function


if __name__ == '__main__':  # pragma: no cover
    pass
