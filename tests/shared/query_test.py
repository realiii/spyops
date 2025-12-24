# -*- coding: utf-8 -*-
"""
Test for Query builders
"""


from fudgeo import FeatureClass, Field
from fudgeo.constant import COMMA_SPACE
from fudgeo.enumeration import SQLFieldType
from pytest import approx, mark

from geomio.shared.query import QueryClip, QuerySplitByAttributes


pytestmark = [mark.extract]


@mark.parametrize('name, fix_name, count, inserts, selects', [
    ('cities', 'world_tables', 11,
     'CITY_NAME, GMI_ADMIN, ADMIN_NAME, FIPS_CNTRY, CNTRY_NAME, STATUS, POP, POP_RANK, POP_CLASS, PORT_ID, POP_SOURCE',
     'CITY_NAME, GMI_ADMIN, ADMIN_NAME, FIPS_CNTRY, CNTRY_NAME, STATUS, POP, POP_RANK, POP_CLASS, PORT_ID, POP_SOURCE'),
    ('lakes_a', 'world_features', 8,
     'SHAPE, FEATURE_ID, PART_ID, NAME, SURF_ELEV, DEPTH, SQMI, SQKM',
     'SHAPE "[Polygon]", FEATURE_ID, PART_ID, NAME, SURF_ELEV, DEPTH, SQMI, SQKM'),
])
def test_field_names_and_count(request, name, fix_name, count, inserts, selects):
    """
    Test _field_names_and_count
    """
    geo = request.getfixturevalue(fix_name)
    element = geo[name]
    fields = [Field('a', data_type=SQLFieldType.text)]
    result = QuerySplitByAttributes(element, fields)._field_names_and_count
    field_count, insert_field_names, select_field_names = result
    assert field_count == count
    assert insert_field_names == inserts
    assert select_field_names == selects
# End test_field_names_and_count function


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
    fields = [Field(n, data_type=SQLFieldType.text) for n in group_names]
    group_names = COMMA_SPACE.join(group_names)
    query = QuerySplitByAttributes(element, fields)
    assert f'FROM {element.name}' in query.group_count
    assert f'GROUP BY {group_names}' in query.group_count
    assert query.insert.strip().startswith('INSERT INTO {}(')
    assert f'dense_rank() OVER (ORDER BY {group_names}' in query.select
# End test_query_split_by_attributes function


def test_query_analysis(world_features, inputs, mem_gpkg):
    """
    Test Query Analysis
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
# End test_query_analysis function


if __name__ == '__main__':  # pragma: no cover
    pass
