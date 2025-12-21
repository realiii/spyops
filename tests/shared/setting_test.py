# -*- coding: utf-8 -*-
"""
Test for Setting
"""
from fudgeo import GeoPackage, MemoryGeoPackage
from pytest import mark, raises

from geomio.shared.enumeration import Setting
from geomio.shared.setting import ANALYSIS_SETTINGS, Swap, _Workspace

pytestmark = [mark.settings]


def test_analysis_settings_defaults():
    """
    Test Analysis Settings Defaults
    """
    assert ANALYSIS_SETTINGS.overwrite is False
    assert ANALYSIS_SETTINGS.xy_tolerance is None
    assert ANALYSIS_SETTINGS.current_workspace is None
# End test_analysis_settings_defaults function


@mark.parametrize('setting', [
    123,
    'overunder',
])
def test_bad_setting(setting):
    """
    Test bad setting
    """
    with raises((TypeError, ValueError)):
        with Swap(setting, True):
            pass
# End test_bad_setting function


@mark.parametrize('setting, value, expected', [
    (Setting.OVERWRITE, True, True),
    (Setting.OVERWRITE, False, False),
    (Setting.OVERWRITE, 'True', True),
    (Setting.OVERWRITE, 'False', True),
    (Setting.OVERWRITE, 0, False),
    (Setting.OVERWRITE, 1, True),
    (Setting.OVERWRITE, None, False),
    ('overwrite', True, True),
    ('overwrite', False, False),
    ('overwrite', 'True', True),
    ('overwrite', 'False', True),
    ('OVERWRITE', 0, False),
    ('OVERWRITE', 1, True),
    ('OVERWRITE', None, False),
])
def test_swapping(setting, value, expected):
    """
    Test Swapping using Overwrite
    """
    with Swap(setting, value) as s:
        assert s.cached_value is False
        assert s.swap_value is expected
    assert ANALYSIS_SETTINGS.overwrite is False
# End test_swapping function


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


if __name__ == '__main__':  # pragma: no cover
    pass
