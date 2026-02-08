# -*- coding: utf-8 -*-
"""
Tests for Fields
"""


from fudgeo import Field
from pytest import mark

from spyops.management import add_field, calculate_field, delete_field

pytestmark = [mark.management, mark.field]


def test_delete_field(world_tables, mem_gpkg):
    """
    Test delete field
    """
    name = 'admin'
    table = world_tables[name].copy(
        name=name, geopackage=mem_gpkg, where_clause='ISO_CC = "BR"')
    assert len(table.fields) == 16
    delete_field(table, 'ISO_CC')
    assert len(table.fields) == 15
    delete_field(table, fields='NAME')
    assert len(table.fields) == 14
    delete_field(table, fields=['disputed', 'notes'])
    assert len(table.fields) == 12
# End test_delete_field function


def test_add_fields(world_tables, mem_gpkg):
    """
    Test add_field
    """
    name = 'admin'
    table = world_tables[name].copy(
        name=name, geopackage=mem_gpkg, where_clause='ISO_CC = "BR"')
    assert len(table.fields) == 16
    add_field(table)
    assert len(table.fields) == 16
    add_field(table, elements=table)
    assert len(table.fields) == 16
    add_field(table, elements=world_tables['cities'])
    assert len(table.fields) == 27
    add_field(table, fields=Field('pop_est', data_type='REAL'))
    assert len(table.fields) == 28
    add_field(table, fields=[Field('pop_est', data_type='REAL'),
                             Field('pop_density', data_type='REAL')])
    assert len(table.fields) == 29
    add_field(table, elements=[world_tables['cities'],
                               world_tables['disputed_boundaries']])
    assert len(table.fields) == 30
# End test_add_fields function


def test_calculate_field(world_tables, mem_gpkg):
    """
    Test calculate_field
    """
    name = 'admin'
    table = world_tables[name].copy(
        name=name, geopackage=mem_gpkg, where_clause='ISO_CC = "BR"')
    calculate_field(table, 'ISO_CC', expression='ISO_CC || ISO_CC')
    where_clause = 'ISO_CC = "BRBR"'
    cursor = table.select(where_clause=where_clause)
    assert len(cursor.fetchall()) == 62
    calculate_field(table, 'ISO_CC', expression='NAME', where_clause=where_clause)
# End test_calculate_field function


if __name__ == '__main__':  # pragma: no cover
    pass
