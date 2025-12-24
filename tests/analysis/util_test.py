# -*- coding: utf-8 -*-
"""
Tests for Utility Module
"""


from fudgeo import FeatureClass

from geomio.analysis.util import build_analysis


def test_build_analysis(inputs, world_features, mem_gpkg):
    """
    Test build_analysis
    """
    source = world_features['cities_p']
    operator = inputs['clipper_a']
    target = FeatureClass(mem_gpkg, 'asdf')
    qc = build_analysis(source, target, operator)
    assert qc.has_intersection is True
    assert 'SELECT SHAPE "[Point]",' in qc.query.select
    assert 'WHERE fid IN ' in qc.query.select
    assert 'minx <= 16.47' in qc.query.select
    assert 'AND maxy >= 46.49' in qc.query.select
    assert 'WHERE fid NOT IN ' in qc.query.select_disjoint
    assert 'INSERT INTO asdf(SHAPE, CITY_NAME, GMI_ADMIN' in qc.query.insert
    assert qc.target.exists is True
# End test_build_analysis function


if __name__ == '__main__':  # pragma: no cover
    pass
