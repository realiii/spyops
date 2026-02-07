# -*- coding: utf-8 -*-
"""
Tests for Table Module
"""


from fudgeo import Table
from fudgeo.constant import FID
from pytest import mark

from spyops.management import get_count, create_table

pytestmark = [mark.management, mark.table]


def test_get_count(ntdb_zm):
    """
    Test get count
    """
    source = ntdb_zm['hydro_a']
    result = get_count(source)
    assert result == 12_950
# End test_get_count function


def test_create_table(mem_gpkg):
    """
    Test create table
    """
    table_name = 'test_table'
    result = create_table(mem_gpkg, table_name)
    assert isinstance(result, Table)
    assert [f.name for f in result.fields] == [FID]
# End test_create_table function


if __name__ == '__main__':  # pragma: no cover
    pass
