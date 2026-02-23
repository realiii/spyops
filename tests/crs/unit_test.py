# -*- coding: utf-8 -*-
"""
Test for Units
"""


from pyproj import CRS
from pytest import approx, mark, raises

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.crs.unit import (
    get_linear_unit_conversion_factor, get_unit_conversion, get_unit_name)


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


if __name__ == '__main__':  # pragma: no cover
    pass
