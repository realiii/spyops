# -*- coding: utf-8 -*-
"""
Tests for Unit Validation
"""


from pytest import raises, mark, approx

from spyops.crs.unit import DecimalDegrees, Feet, Metres
from spyops.validation import validate_feature_class, validate_linear_unit


pytestmark = [mark.validation]


@mark.parametrize('fc_name, value, expected, throws', [
    ('hydro_4617_a', -1.234, 1.234, False),
    ('hydro_6654_a', -100, 100, False),
    ('hydro_utm11_a', -100, 100, False),
    ('hydro_4617_a', DecimalDegrees(-1.234), 1.234, False),
    ('hydro_6654_a', Metres(-100), 100, False),
    ('hydro_utm11_a', Metres(-100), 100, False),
    ('hydro_4617_a', '-1.234 dd', 1.234, False),
    ('hydro_6654_a', '-100 m', 100, False),
    ('hydro_utm11_a', '-100 meters', 100, False),

    ('hydro_4617_a', 1.234, 1.234, False),
    ('hydro_6654_a', 100, 100, False),
    ('hydro_utm11_a', 100, 100, False),
    ('hydro_4617_a', DecimalDegrees(1.234), 1.234, False),
    ('hydro_6654_a', Metres(100), 100, False),
    ('hydro_utm11_a', Metres(100), 100, False),
    ('hydro_4617_a', '1.234 dd', 1.234, False),
    ('hydro_6654_a', '100 m', 100, False),
    ('hydro_utm11_a', '100 meters', 100, False),

    ('hydro_4617_a', Metres(100000), 1.19337, False),
    ('hydro_6654_a', Feet(100), 30.48, False),
    ('hydro_utm11_a', DecimalDegrees(1.234), 111836.7115, False),

    ('hydro_utm11_a', Ellipsis, 0, True),
    ('hydro_utm11_a', None, 0, True),
    ('hydro_utm11_a', '100 mozilla', 0, True),
    ('hydro_utm11_a', 'None None', 0, True),
])
def test_validate_linear_unit_as_number(ntdb_zm_small, fc_name, value, expected, throws):
    """
    Test validate linear unit as number
    """
    @validate_feature_class('name')
    @validate_linear_unit('tolerance', feature_class_name='name', as_number=True)
    def unit_function(name, tolerance):
        return tolerance
    fc = ntdb_zm_small[fc_name]
    if throws:
        with raises((ValueError, TypeError)):
            unit_function(fc, value)
    else:
        assert approx(unit_function(fc, value), abs=0.001) == expected
# End test_validate_linear_unit_as_number function


@mark.parametrize('fc_name, value, expected', [
    ('hydro_4617_a', -1.234, DecimalDegrees(1.234)),
    ('hydro_6654_a', -100, Metres(100)),
    ('hydro_utm11_a', -100, Metres(100)),
    ('hydro_4617_a', DecimalDegrees(-1.234), DecimalDegrees(1.234)),
    ('hydro_6654_a', Metres(-100), Metres(100)),
    ('hydro_utm11_a', Metres(-100), Metres(100)),
    ('hydro_4617_a', '-1.234 dd', DecimalDegrees(1.234)),
    ('hydro_6654_a', '-100 m', Metres(100)),
    ('hydro_utm11_a', '-100 meters', Metres(100)),

    ('hydro_4617_a', 1.234, DecimalDegrees(1.234)),
    ('hydro_6654_a', 100, Metres(100)),
    ('hydro_utm11_a', 100, Metres(100)),
    ('hydro_4617_a', DecimalDegrees(1.234), DecimalDegrees(1.234)),
    ('hydro_6654_a', Metres(100), Metres(100)),
    ('hydro_utm11_a', Metres(100), Metres(100)),
    ('hydro_4617_a', '1.234 dd', DecimalDegrees(1.234)),
    ('hydro_6654_a', '100 m', Metres(100)),
    ('hydro_utm11_a', '100 meters', Metres(100)),
])
def test_validate_linear_unit(ntdb_zm_small, fc_name, value, expected):
    """
    Test validate linear unit
    """
    @validate_feature_class('name')
    @validate_linear_unit('tolerance', feature_class_name='name', as_number=False)
    def unit_function(name, tolerance):
        return tolerance
    fc = ntdb_zm_small[fc_name]
    assert unit_function(fc, value) == expected
# End test_validate_linear_unit function


if __name__ == '__main__':  # pragma: no cover
    pass
