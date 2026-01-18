# -*- coding: utf-8 -*-
"""
Test for Workspace Settings
"""


from fudgeo import GeoPackage, MemoryGeoPackage
from pytest import mark, raises

from spyops.environment.enumeration import Setting
from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.context import Swap
from spyops.environment.workspace import _Workspace

pytestmark = [mark.environment]


def test_check_workspace(data_path):
    """
    Test Check Workspace
    """
    setting = Setting.CURRENT_WORKSPACE
    assert _Workspace._check_workspace(None, setting) is None
    with raises(IOError):
        _Workspace._check_workspace('test', setting)
    assert isinstance(_Workspace._check_workspace(':memory:', setting), MemoryGeoPackage)
    with raises(IOError):
        _Workspace._check_workspace(data_path / 'test.gpkg', setting)
    assert isinstance(_Workspace._check_workspace(data_path / 'crs.gpkg', setting), GeoPackage)
    assert _Workspace._check_workspace(1234, setting) is None
# End test_check_workspace function


def test_scratch_workspace(fresh_gpkg):
    """
    Test scratch workspace
    """
    original = ANALYSIS_SETTINGS.scratch_workspace
    with Swap(Setting.SCRATCH_WORKSPACE, fresh_gpkg) as s:
        assert isinstance(s.cached_value, MemoryGeoPackage)
        assert isinstance(s.swap_value, GeoPackage)
        assert ANALYSIS_SETTINGS.scratch_workspace is fresh_gpkg
    assert ANALYSIS_SETTINGS.scratch_workspace is original
# End test_scratch_workspace function


if __name__ == '__main__':  # pragma: no cover
    pass
