# -*- coding: utf-8 -*-
"""
Test for Geometry Dimensions
"""


from math import nan

from pytest import approx, mark

from gisworks.environment.enumeration import (
    OutputMOption, Setting, OutputZOption)
from gisworks.environment import ANALYSIS_SETTINGS
from gisworks.environment.context import Swap


pytestmark = [mark.environment]


@mark.parametrize('swap_value', [
    OutputZOption.SAME,
    OutputZOption.ENABLED,
    OutputZOption.DISABLED
])
def test_swap_output_z_option(swap_value):
    """
    Test swapping output_z_option setting
    """
    original_value = ANALYSIS_SETTINGS.output_z_option
    with Swap(Setting.OUTPUT_Z_OPTION, swap_value) as swap:
        assert ANALYSIS_SETTINGS.output_z_option == swap_value
        assert swap.swap_value == swap_value
        assert swap.cached_value == original_value

    assert ANALYSIS_SETTINGS.output_z_option == original_value
# End test_swap_output_z_option function


@mark.parametrize('value, expected', [
    ('0.0', 0.),
    (0., 0.),
    (1., 1.),
    (None, nan),
    (nan, nan),
])
def test_z_value(value, expected):
    """
    Test swapping z_value
    """
    with Swap(Setting.Z_VALUE, value):
        assert approx([ANALYSIS_SETTINGS.z_value], nan_ok=True) == [expected]
# End test_z_value function


@mark.parametrize('value, expected', [
    ('0.0', 0.),
    (0., 0.),
    (1., 1.),
    (None, None),
    (nan, None),
])
def test_xy_tolerance(value, expected):
    """
    Test swapping xy tolerance
    """
    with Swap(Setting.XY_TOLERANCE, value):
        assert approx([ANALYSIS_SETTINGS.xy_tolerance], nan_ok=True) == [expected]
# End test_xy_tolerance function


@mark.parametrize('swap_value', [
    OutputMOption.SAME,
    OutputMOption.ENABLED,
    OutputMOption.DISABLED
])
def test_swap_output_m_option(swap_value):
    """
    Test swapping output_m_option setting
    """
    original_value = ANALYSIS_SETTINGS.output_m_option
    with Swap(Setting.OUTPUT_M_OPTION, swap_value) as swap:
        assert ANALYSIS_SETTINGS.output_m_option == swap_value
        assert swap.swap_value == swap_value
        assert swap.cached_value == original_value

    assert ANALYSIS_SETTINGS.output_m_option == original_value
# End test_swap_output_m_option function


if __name__ == '__main__':  # pragma: no cover
    pass
