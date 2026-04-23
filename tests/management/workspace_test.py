# -*- coding: utf-8 -*-
"""
Tests for Workspace Module
"""


from fudgeo import GeoPackage
from pytest import mark, raises

from spyops.environment import Setting
from spyops.environment.context import Swap
from spyops.management import create_folder, create_sqlite_database


pytestmark = [mark.management, mark.workspace]


def test_create_sqlite_database(tmp_path):
    """
    Test create SQLite database
    """
    path = tmp_path / 'test.gpkg'
    gpkg = create_sqlite_database(
        path, enable_metadata=True, enable_schema=True, ogr_contents=True)
    assert isinstance(gpkg, GeoPackage)
    try:
        path.unlink(missing_ok=True)
    except PermissionError:
        pass
# End test_create_sqlite_database function


def test_create_folder(tmp_path):
    """
    Test Create Folder
    """
    path = tmp_path
    name = 'test_folder'
    output = create_folder(path, name)
    assert output.is_dir()
    with Swap(Setting.OVERWRITE, False):
        with raises(FileExistsError):
            create_folder(path, name)
    with Swap(Setting.OVERWRITE, True):
        output = create_folder(path, name)
        assert output.is_dir()
# End test_create_folder function


if __name__ == '__main__':  # pragma: no cover
    pass
