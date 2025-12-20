# -*- coding: utf-8 -*-
"""
Test for Settings
"""


from pytest import mark, raises

from geomio.shared.enumeration import Settings
from geomio.shared.settings import SETTINGS, Swap

pytestmark = [mark.settings]


def test_analysis_settings_defaults():
    """
    Test Analysis Settings Defaults
    """
    assert SETTINGS.overwrite is False
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
    (Settings.OVERWRITE, True, True),
    (Settings.OVERWRITE, False, False),
    (Settings.OVERWRITE, 'True', True),
    (Settings.OVERWRITE, 'False', True),
    (Settings.OVERWRITE, 0, False),
    (Settings.OVERWRITE, 1, True),
    (Settings.OVERWRITE, None, False),
    ('overwrite', True, True),
    ('overwrite', False, False),
    ('overwrite', 'True', True),
    ('overwrite', 'False', True),
    ('OVERWRITE', 0, False),
    ('OVERWRITE', 1, True),
    ('OVERWRITE', None, False),
])
def test_overwrite(setting, value, expected):
    """
    Test Overwrite
    """
    with Swap(setting, value) as s:
        assert s.cached_value is False
        assert s.swap_value is expected
    assert SETTINGS.overwrite is False
# End test_overwrite function


if __name__ == '__main__':  # pragma: no cover
    pass
