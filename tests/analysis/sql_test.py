# -*- coding: utf-8 -*-
"""
Test for SQL Creation
"""


from textwrap import dedent

from fudgeo import FeatureClass, Field
from fudgeo.constant import COMMA_SPACE
from fudgeo.enumeration import SQLFieldType
from pytest import mark

from geomio.analysis.sql import (
    QuerySplitByAttributes, build_analysis, build_sql_insert,
    _build_field_names_and_count, _build_sql_select)


pytestmark = [mark.extract]


def test_build_sql_insert():
    """
    Test build_sql_insert
    """
    sql = build_sql_insert(
        element_name='test123', field_names=COMMA_SPACE.join('abcde'),
        field_count=5)
    sql = dedent(sql).strip().replace('\n', '')
    assert sql == """INSERT INTO test123(a, b, c, d, e) VALUES (?, ?, ?, ?, ?)"""
# End test_build_sql_insert function


@mark.parametrize('name, fix_name, count, inserts, selects', [
    ('cities', 'world_tables', 11,
     'CITY_NAME, GMI_ADMIN, ADMIN_NAME, FIPS_CNTRY, CNTRY_NAME, STATUS, POP, POP_RANK, POP_CLASS, PORT_ID, POP_SOURCE',
     'CITY_NAME, GMI_ADMIN, ADMIN_NAME, FIPS_CNTRY, CNTRY_NAME, STATUS, POP, POP_RANK, POP_CLASS, PORT_ID, POP_SOURCE'),
    ('lakes_a', 'world_features', 8,
     'SHAPE, FEATURE_ID, PART_ID, NAME, SURF_ELEV, DEPTH, SQMI, SQKM',
     'SHAPE "[Polygon]", FEATURE_ID, PART_ID, NAME, SURF_ELEV, DEPTH, SQMI, SQKM'),
])
def test_build_field_names_and_count(request, name, fix_name, count, inserts, selects):
    """
    Test _build_field_names_and_count
    """
    geo = request.getfixturevalue(fix_name)
    element = geo[name]
    result = _build_field_names_and_count(element)
    field_count, insert_field_names, select_field_names = result
    assert field_count == count
    assert insert_field_names == inserts
    assert select_field_names == selects
# End test_build_field_names_and_count function


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


def test_build_sql_select(world_tables):
    """
    Build SQL Select
    """
    table = world_tables['cities']
    sql = _build_sql_select(table, field_names='bobby, tables', where_clause='1 = 1')
    assert 'SELECT bobby, tables' in sql
    assert 'FROM cities' in sql
    assert 'WHERE 1 = 1' in sql
# End test_build_sql_select function


def test_build_query_components(inputs, world_features, mem_gpkg):
    """
    Test build_analysis
    """
    source = world_features['cities_p']
    operator = inputs['clipper_a']
    target = FeatureClass(mem_gpkg, 'asdf')
    qc = build_analysis(source, target, operator, use_empty=True)
    assert qc.use_index is True
    assert qc.has_intersection is True
    assert 'SELECT SHAPE "[Point]",' in qc.sql_intersect
    assert 'WHERE fid IN ' in qc.sql_intersect
    assert 'minx <= 16.47' in qc.sql_intersect
    assert 'AND maxy >= 46.49' in qc.sql_intersect
    assert 'WHERE fid NOT IN ' in qc.sql_disjoint
    assert 'INSERT INTO asdf(SHAPE, CITY_NAME, GMI_ADMIN' in qc.sql_insert
    assert qc.target.exists is True
# End test_build_query_components function


if __name__ == '__main__':  # pragma: no cover
    pass
