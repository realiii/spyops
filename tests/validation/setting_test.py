# -*- coding: utf-8 -*-
"""
Test Validation
"""

from pytest import mark

from spyops.environment.enumeration import Setting
from spyops.environment.context import Swap
from spyops.validation import validate_tolerance, validate_xy_tolerance


pytestmark = [mark.validation]


@mark.parametrize('value, expected', [
    (None, None),
    (0, 0.),
    (-10, 0.),
    ('10', 10.),
])
def test_validate_xy_tolerance_sans_setting(value, expected):
    """
    Test validate xy tolerance (sans setting)
    """
    @validate_xy_tolerance()
    def xy_function(xy_tolerance=None):
        return xy_tolerance

    assert xy_function(value) == expected
# End test_validate_xy_tolerance_sans_setting function


@mark.parametrize('value, expected', [
    (None, None),
    (0, 0.),
    (-10, 0.),
    ('10', 10.),
])
def test_validate_zm_tolerance(value, expected):
    """
    Test validate Z/M tolerance
    """
    @validate_tolerance('tol')
    def tol_function(tol=None):
        return tol

    assert tol_function(value) == expected
# End test_validate_zm_tolerance function


@mark.parametrize('value, swap_value, expected', [
    (None, None, None),
    (0, None, 0.),
    (-10, None, 0.),
    ('10', None, 10.),
])
def test_validate_xy_tolerance_with_setting(value, swap_value, expected):
    """
    Test validate xy tolerance (with setting)
    """
    @validate_xy_tolerance()
    def xy_function(xy_tolerance=None):
        return xy_tolerance
    with Swap(Setting.XY_TOLERANCE, swap_value):
        assert xy_function(value) == expected
    with Swap(Setting.XY_TOLERANCE, value):
        assert xy_function(None) == expected
    with Swap(Setting.XY_TOLERANCE, value):
        assert xy_function(123) == 123.
# End test_validate_xy_tolerance_with_setting function


if __name__ == '__main__':  # pragma: no cover
    pass
