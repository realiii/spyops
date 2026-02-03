# -*- coding: utf-8 -*-
"""
Test for Units
"""


from pyproj import CRS
from pytest import approx, mark

from spyops.crs.unit import get_unit_conversion_factor, get_unit_name


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
def test_get_unit_conversion_factor(from_name, to_name, expected):
    """
    Test get unit conversion factor
    """
    assert approx(get_unit_conversion_factor(from_name, to_name), abs=10**-6) == expected
# End test_get_unit_conversion_factor function


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
