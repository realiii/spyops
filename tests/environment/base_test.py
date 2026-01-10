# -*- coding: utf-8 -*-
"""
Test for Base Analysis Settings
"""

from math import isnan

from pytest import mark

from gisworks.environment.enumeration import (
    OutputMOption, OutputZOption)
from gisworks.environment import ANALYSIS_SETTINGS


pytestmark = [mark.environment]


def test_analysis_settings_defaults():
    """
    Test Analysis Settings Defaults
    """
    assert ANALYSIS_SETTINGS.overwrite is False
    assert ANALYSIS_SETTINGS.xy_tolerance is None
    assert ANALYSIS_SETTINGS.current_workspace is None
    assert ANALYSIS_SETTINGS.scratch_workspace is None
    assert ANALYSIS_SETTINGS.output_z_option == OutputZOption.SAME
    assert ANALYSIS_SETTINGS.output_m_option == OutputMOption.SAME
    assert isnan(ANALYSIS_SETTINGS.z_value)
# End test_analysis_settings_defaults function


if __name__ == '__main__':  # pragma: no cover
    pass
