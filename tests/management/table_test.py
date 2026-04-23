# -*- coding: utf-8 -*-
"""
Tests for Table Module
"""


from fudgeo import GeoPackage, Table
from fudgeo.constant import FID
from pytest import mark, raises

from spyops.environment import Setting
from spyops.environment.context import Swap
from spyops.management import delete_rows, get_count, create_table, copy_rows
from spyops.shared.exception import OperationsError


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


class TestCopyRows:
    """
    Test Copy Rows
    """
    @mark.parametrize('table_name, where_clause, count', [
        ('admin', None, 5824),
        ('admin', '', 5824),
        ('admin', 'ISO_CC = "BR"', 62),
        ('disputed_boundaries', None, 561),
        ('disputed_boundaries', '', 561),
        ('disputed_boundaries', 'Description = "Disputed Boundary"', 364),
        ('cities', None, 2540),
        ('cities', '', 2540),
        ('cities', 'POP IS NULL', 1377),
        ('cities', 'POP < 0', 0),
    ])
    def test_copy_rows(self, world_tables, mem_gpkg, table_name, where_clause, count):
        """
        Test copy_rows
        """
        source = world_tables[table_name]
        target = Table(geopackage=mem_gpkg, name=table_name)
        result = copy_rows(source=source, target=target, where_clause=where_clause)
        assert len(result) == count
    # End test_copy_rows method

    def test_overwrite(self, world_tables, mem_gpkg):
        """
        Test copy_rows that exercises overwrite
        """
        source = world_tables['admin']
        where_clause = 'ISO_CC = "BR"'
        count = 62
        target = Table(geopackage=mem_gpkg, name=source.name)
        result = copy_rows(source=source, target=target, where_clause=where_clause)
        assert len(result) == count

        with raises(OperationsError):
            copy_rows(source=source, target=target, where_clause=where_clause)

        with Swap(Setting.OVERWRITE, True):
            result = copy_rows(source=source, target=target, where_clause=where_clause)
        assert len(result) == count
    # End test_overwrite method

    @mark.parametrize('table_name, where_clause', [
        ('admin', 'ISO = "BR"'),
        ('disputed_boundaries', 'Description = "Disputed Boundary'),
        ('cities', 'POP ISNULL()'),
        ('cities', 'POP <<>> 0'),
    ])
    def test_bad_sql(self, world_tables, mem_gpkg, table_name, where_clause):
        """
        Test copy_rows bad SQL
        """
        source = world_tables[table_name]
        target = Table(geopackage=mem_gpkg, name=table_name)
        with raises(OperationsError):
            copy_rows(source=source, target=target, where_clause=where_clause)
    # End test_bad_sql method
# End TestCopyRows class


if __name__ == '__main__':  # pragma: no cover
    pass
