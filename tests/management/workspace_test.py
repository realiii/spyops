# -*- coding: utf-8 -*-
"""
Tests for Workspace Module
"""


from fudgeo import GeoPackage
from pytest import mark

from spyops.management import create_sqlite_database


pytestmark = [mark.management, mark.workspace]


def test_create_sqlite_database(tmp_path):
    """
    Test create SQLite database
    """
    path = tmp_path / 'test.gpkg'
    gpkg = create_sqlite_database(
        path, enable_metadata=True, enable_schema=True, ogr_contents=True)
    assert isinstance(gpkg, GeoPackage)
    path.unlink(missing_ok=True)
# End test_create_sqlite_database function


if __name__ == '__main__':  # pragma: no cover
    pass
