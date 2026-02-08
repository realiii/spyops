# -*- coding: utf-8 -*-
"""
Tests for Fields
"""


from pytest import mark

from spyops.management import delete_field

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


if __name__ == '__main__':  # pragma: no cover
    pass
