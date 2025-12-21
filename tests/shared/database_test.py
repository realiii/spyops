# -*- coding: utf-8 -*-
"""
Tests for the database module
"""


from sqlite3 import connect

from pytest import mark

from geomio.shared.database import _is_sqlite, _is_geopackage, is_geopackage


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
# End test_is_geopackage function


if __name__ == '__main__':  # pragma: no cover
    pass
