# -*- coding: utf-8 -*-
"""
Tests for Table Module
"""


from fudgeo import GeoPackage, Table
from fudgeo.constant import FID
from pytest import mark

from conftest import fresh_gpkg
from spyops.management import delete_rows, get_count, create_table

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


def test_delete_rows(grid_index, fresh_gpkg):
    """
    Test delete_rows
    """
    name = 'grid_a_copy'
    grid = grid_index['grid_a'].copy(name, geopackage=fresh_gpkg)
    assert len(grid) == 8
    delete_rows(grid, where_clause='FID >= 5')
    assert len(grid) == 4
    delete_rows(grid)
    assert len(grid) == 0
    path = fresh_gpkg.path
    assert path.exists()
    fresh_gpkg.connection.close()
    gpkg = GeoPackage(path)
    fc = gpkg[name]
    assert fc
    assert fc.is_empty
# End test_delete_rows function


if __name__ == '__main__':  # pragma: no cover
    pass
