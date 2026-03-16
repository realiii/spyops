# -*- coding: utf-8 -*-
"""
Test for Units
"""


from pyproj import CRS
from pytest import approx, mark, raises

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.crs.unit import (
    DecimalDegrees, FeetInternational, FeetUS, Kilometers, Meters,
    get_linear_unit_conversion_factor, get_unit_conversion, get_unit_name,
    unit_factory)


pytestmark = [mark.crs]


@mark.parametrize('from_name, to_name, expected', [
    ('metre', 'metre', 1.),
    ('metre', 'foot', 3.280839895013123),
    ('metre', 'US survey foot', 3.2808333333333355),
    ('foot', 'foot', 1.),
    ('foot', 'metre', 0.3048),
    ('foot', 'US survey foot', 0.9999980000000006),
    ('US survey foot', 'US survey foot', 1.),
    ('US survey foot', 'foot', 1.0000020000039993),
    ('US survey foot', 'metre', 0.304800609601219),
])
def test_get_linear_unit_conversion_factor(from_name, to_name, expected):
    """
    Test get linear unit conversion factor
    """
    assert approx(get_linear_unit_conversion_factor(from_name, to_name), abs=10 ** -6) == expected
# End test_get_linear_unit_conversion_factor function


class TestGetUnitConversion:
    """
    Test get_unit_conversion
    """
    @mark.parametrize('from_unit, to_unit', [
        (LengthUnit.FEET_US, AreaUnit.SQUARE_MILES_US),
        (AreaUnit.HECTARES, LengthUnit.METERS),
    ])
    def test_bad_inputs(self, from_unit, to_unit):
        """
        Test bad inputs into get_unit_conversion
        """
        with raises(TypeError):
            get_unit_conversion(from_unit, to_unit)
    # End test_bad_inputs method

    def test_length(self):
        """
        Test length conversions
        """
        values = [get_unit_conversion(item, LengthUnit.METERS)
                  for item in LengthUnit]
        assert approx(values, abs=0.000001) == [
            1000., 1.,
            1609.344, 1852., 0.9144, 0.3048,
            1609.34721869444, 1853.248, 0.9144018288036576, 0.304800609601219]
    # End test_length method

    def test_area(self):
        """
        Test area conversions
        """
        values = [get_unit_conversion(item, AreaUnit.SQUARE_METERS)
                  for item in AreaUnit]
        assert approx(values, abs=0.000001) == [
            1000000., 1.,
            2589988.110336, 3429904., 0.83612736, 0.09290304,
            2589998.4703195295, 3434528.1495040003, 0.8361307045194736, 0.09290341161327473,
            100000000., 4046.8564224, 4046.8726098742472]
    # End test_area method
# End TestGetUnitConversion class


@mark.parametrize('code, expected', [
    (4326, 'degree'),
    (26912, 'metre'),
    (32057, 'US survey foot'),
    (6655, 'metre'),
])
def test_get_unit_name(code, expected):
    """
    Test get unit name
    """
    crs = CRS.from_epsg(code)
    assert get_unit_name(crs) == expected
# End test_get_unit_name function


@mark.parametrize('value, expected, meters', [
    ('5 meters', Meters(5), 5),
    ('6 METERS', Meters(6), 6),
    ('7 Meters', Meters(7), 7),
    ('8 Metres', Meters(8), 8),
    ('9 Metre', Meters(9), 9),
    ('9   Metre', Meters(9), 9),
    ('  9   Metre', Meters(9), 9),
    ('10 m', Meters(10), 10),
    ('11 km', Kilometers(11), 11_000),
    ('12 km', Kilometers(12), 12_000),
    ('13 kilometers', Kilometers(13), 13_000),
    ('123.456 feet', FeetInternational(123.456), 37.6),
    ('123.456 feet', FeetInternational(123.456), 37.6),
    ('543.210 us survey feet', FeetUS(543.210), 165.57),
    ('-543.210 foot_us', FeetUS(-543.210), -165.57),
    ('-543.210 foot us', FeetUS(-543.210), -165.57),
    ('-543.210 feet us', FeetUS(-543.210), -165.57),
    ('1.0 decimal degrees', DecimalDegrees(1.), None),
    ('45.5 decimal degree', DecimalDegrees(45.5), None),
    ('90 dd', DecimalDegrees(90), None),
    ('1.234 deg', DecimalDegrees(1.234), None),
    ('1.234 degrees', DecimalDegrees(1.234), None),
    ('1.234 degree', DecimalDegrees(1.234), None),
    ('-1.234 degree', DecimalDegrees(-1.234), None),
])
def test_unit_factory_valid(value, expected, meters):
    """
    Test unit_factory with valid inputs
    """
    result = unit_factory(value)
    assert result == expected
    if meters is not None:
        assert approx(result.to_meters(), abs=0.1) == meters
# End test_unit_factory_valid function


@mark.parametrize('value', [
    None,
    '',
    'invalid_unit',
    'meter',
    'oo meter',
    123,
    12.34,
    [],
    {},
    object(),
])
def test_unit_factory_invalid(value):
    """
    Test unit_factory with invalid inputs that should return None
    """
    assert unit_factory(value) is None
# End test_unit_factory_invalid function


if __name__ == '__main__':  # pragma: no cover
    pass
