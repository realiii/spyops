# -*- coding: utf-8 -*-
"""
Tests for the database module
"""


from sqlite3 import connect

from pytest import mark

from gisworks.shared.database import (
    _is_sqlite, _is_geopackage, get_table_names,
    has_table, is_geopackage)


pytestmark = [mark.database]


def test_is_sqlite(crs_geopackage, tmp_path):
    """
    Test is sqlite
    """
    connection = connect(':memory:')
    assert _is_sqlite(connection) is True
    connection = connect(crs_geopackage.path)
    assert _is_sqlite(connection) is True
    path = tmp_path / 'test.txt'
    with path.open('w') as fout:
        fout.write('test')
    connection = connect(path)
    assert _is_sqlite(connection) is False
# End test_is_sqlite function


def test_is_geopackage_internal(crs_geopackage, tmp_path):
    """
    Test is geopackage (internal)
    """
    connection = connect(':memory:')
    assert _is_geopackage(connection) is False
    connection = connect(crs_geopackage.path)
    assert _is_geopackage(connection) is True
    path = tmp_path / 'test.txt'
    with path.open('w') as fout:
        fout.write('test')
    connection = connect(path)
    assert _is_geopackage(connection) is False
# End test_is_geopackage_internal function


def test_is_geopackage(crs_geopackage, tmp_path):
    """
    Test is geopackage
    """
    assert is_geopackage('') is False
    assert is_geopackage(':memory:') is False
    assert is_geopackage(crs_geopackage.path) is True
    path = tmp_path / 'test.txt'
    assert is_geopackage(path) is False
    with path.open('w') as fout:
        fout.write('test')
    assert is_geopackage(path) is False
    path = tmp_path / 'test.db'
    connect(path)
    assert is_geopackage(path) is False
# End test_is_geopackage function


def test_get_table_names(crs_geopackage):
    """
    Test get_table_names
    """
    names = get_table_names(crs_geopackage.connection)
    assert set(names) == {'gpkg_contents', 'gpkg_extensions',
                          'gpkg_geometry_columns', 'gpkg_ogr_contents',
                          'gpkg_spatial_ref_sys', 'gpkg_tile_matrix',
                          'gpkg_tile_matrix_set', 'sqlite_sequence',
                          'test_26915_a', 'test_32038_a', 'test_32138_p',
                          'test_custom_a', 'test_custom_p', 'test_undefined_p'}
# End test_get_table_names function


@mark.parametrize('name, expected', [
    ('test_26915_a', True),
    ('asdf', False),
    ('GPKG_CONTENTS', True),
])
def test_has_table(crs_geopackage, name, expected):
    """
    Test Has Table
    """
    assert has_table(crs_geopackage.connection, name) is expected
# End test_has_table function


if __name__ == '__main__':  # pragma: no cover
    pass
