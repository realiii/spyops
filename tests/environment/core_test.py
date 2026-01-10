# -*- coding: utf-8 -*-
"""
Test for Base Analysis Settings
"""

from math import isnan

from fudgeo import MemoryGeoPackage
from pytest import mark

from gisworks.environment.context import Swap
from gisworks.environment.enumeration import (
    OutputMOption, OutputZOption, Setting)
from gisworks.environment import ANALYSIS_SETTINGS
from gisworks.environment.core import ZMConfig, zm_config

pytestmark = [mark.environment]


def test_analysis_settings_defaults():
    """
    Test Analysis Settings Defaults
    """
    assert ANALYSIS_SETTINGS.overwrite is False
    assert ANALYSIS_SETTINGS.xy_tolerance is None
    assert ANALYSIS_SETTINGS.current_workspace is None
    assert isinstance(ANALYSIS_SETTINGS.scratch_workspace, MemoryGeoPackage)
    assert ANALYSIS_SETTINGS.output_z_option == OutputZOption.SAME
    assert ANALYSIS_SETTINGS.output_m_option == OutputMOption.SAME
    assert isnan(ANALYSIS_SETTINGS.z_value)
# End test_analysis_settings_defaults function


@mark.parametrize('has_z, has_m, output_z_option, output_m_option, expected', [
    (True, True, OutputZOption.SAME, OutputMOption.SAME, ZMConfig(is_different=False, z_enabled=True, m_enabled=True)),
    (True, False, OutputZOption.SAME, OutputMOption.SAME, ZMConfig(is_different=False, z_enabled=True, m_enabled=False)),
    (False, True, OutputZOption.SAME, OutputMOption.SAME, ZMConfig(is_different=False, z_enabled=False, m_enabled=True)),
    (False, False, OutputZOption.SAME, OutputMOption.SAME, ZMConfig(is_different=False, z_enabled=False, m_enabled=False)),
    (True, True, OutputZOption.ENABLED, OutputMOption.ENABLED, ZMConfig(is_different=False, z_enabled=True, m_enabled=True)),
    (True, False, OutputZOption.ENABLED, OutputMOption.ENABLED, ZMConfig(is_different=True, z_enabled=True, m_enabled=True)),
    (False, True, OutputZOption.ENABLED, OutputMOption.ENABLED, ZMConfig(is_different=True, z_enabled=True, m_enabled=True)),
    (False, False, OutputZOption.ENABLED, OutputMOption.ENABLED, ZMConfig(is_different=True, z_enabled=True, m_enabled=True)),
    (True, True, OutputZOption.DISABLED, OutputMOption.DISABLED, ZMConfig(is_different=True, z_enabled=False, m_enabled=False)),
    (True, False, OutputZOption.DISABLED, OutputMOption.DISABLED, ZMConfig(is_different=True, z_enabled=False, m_enabled=False)),
    (False, True, OutputZOption.DISABLED, OutputMOption.DISABLED, ZMConfig(is_different=True, z_enabled=False, m_enabled=False)),
    (False, False, OutputZOption.DISABLED, OutputMOption.DISABLED, ZMConfig(is_different=False, z_enabled=False, m_enabled=False)),
])
def test_zm_config(has_z, has_m, output_z_option, output_m_option, expected):
    """
    Test ZM Config function
    """
    with (Swap(Setting.OUTPUT_Z_OPTION, output_z_option),
          Swap(Setting.OUTPUT_M_OPTION, output_m_option)):
        assert zm_config(has_z, has_m) == expected
# End test_zm_config function


if __name__ == '__main__':  # pragma: no cover
    pass
