# -*- coding: utf-8 -*-
"""
Test for SQL Creation
"""


from textwrap import dedent

from fudgeo.constant import COMMA_SPACE
from pytest import mark

from geomio.analysis.sql import (
    build_query_components, build_sql_insert, _build_field_names_and_count,
    build_sql_select_by_attributes, _build_sql_select)


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
    ('cities', 'world_tables', 'FIPS_CNTRY, CNTRY_NAME, STATUS'),
    ('lakes_a', 'world_features', 'FEATURE_ID, PART_ID, NAME'),
])
def test_build_sql_select_by_attributes(request, name, fix_name, group_names):
    """
    Test build_sql_select_by_attributes
    """
    geo = request.getfixturevalue(fix_name)
    element = geo[name]

    result = build_sql_select_by_attributes(element, group_names=group_names)
    group_count_sql, insert_sql, select_sql = result

    assert f'FROM {element.name}' in group_count_sql
    assert f'GROUP BY {group_names}' in group_count_sql

    assert insert_sql.strip().startswith('INSERT INTO {}(')
    assert f'dense_rank() OVER (ORDER BY {group_names}' in select_sql
# End test_build_sql_select_by_attributes function


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
    Test build_query_components
    """
    source = world_features['cities_p']
    operator = inputs['clipper_a']
    target = source.copy(name='asdf', geopackage=mem_gpkg)
    qc = build_query_components(source, target, operator)
    assert qc.use_index is True
    assert qc.has_intersection is True
    assert 'SELECT SHAPE "[Point]",' in qc.sql_touches
    assert 'WHERE fid IN ' in qc.sql_touches
    assert 'minx <= 16.47' in qc.sql_touches
    assert 'AND maxy >= 46.49' in qc.sql_touches
    assert 'WHERE fid NOT IN ' in qc.sql_outside
    assert 'INSERT INTO asdf(SHAPE, CITY_NAME, GMI_ADMIN' in qc.sql_insert
# End test_build_query_components function


if __name__ == '__main__':  # pragma: no cover
    pass
