# -*- coding: utf-8 -*-
"""
Test for Extract Query classes
"""


from fudgeo import FeatureClass, Field
from fudgeo.constant import COMMA_SPACE
from fudgeo.enumeration import FieldType
from pytest import approx, mark, raises

from spyops.query.analysis.extract import QueryClip, QuerySplitByAttributes
from spyops.geometry.config import GeometryConfig

pytestmark = [mark.extract, mark.query]


@mark.parametrize('name, fix_name, group_names', [
    ('cities', 'world_tables', ('FIPS_CNTRY', 'CNTRY_NAME', 'STATUS')),
    ('lakes_a', 'world_features', ('FEATURE_ID', 'PART_ID', 'NAME')),
])
def test_query_split_by_attributes(request, name, fix_name, group_names):
    """
    Test QuerySplitByAttributes
    """
    geo = request.getfixturevalue(fix_name)
    element = geo[name]
    fields = [Field(n, data_type=FieldType.text) for n in group_names]
    group_names = COMMA_SPACE.join(group_names)
    query = QuerySplitByAttributes(element, fields)
    assert f'FROM {element.name}' in query.groups
    assert query.insert.strip().startswith('INSERT INTO {}(')
    assert f'dense_rank() OVER (ORDER BY {group_names}' in query.select
# End test_query_split_by_attributes function


def test_query_clip(world_features, inputs, mem_gpkg):
    """
    Test Query Clip
    """
    target = FeatureClass(mem_gpkg, 'test_target')
    source = world_features['cities_p']
    operator = inputs['clipper_a']
    query = QueryClip(source, target, operator)
    assert query.has_intersection is True
    assert approx(query.operator_extent, abs=0.0001) == (6.74573, 46.49314, 16.47727, 51.70966)
    assert approx(query.source_extent, abs=0.001) == (-176.15156, -54.79199, 179.19906, 78.20000)
    assert query.select == query.select_intersect
    assert query.select.strip().startswith('SELECT SHAPE "[Point]"')
    assert query.insert.strip().startswith('INSERT INTO test_target')
    assert query.select_disjoint
    assert query.operator is operator
    assert isinstance(query.geometry_config, GeometryConfig)
    with raises(ValueError):
        _ = query.target_full
    assert 'FROM clipper_a' in query.select_operator
# End test_query_clip function


if __name__ == '__main__':  # pragma: no cover
    pass
