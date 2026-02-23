# -*- coding: utf-8 -*-
"""
Units
"""


from functools import cache
from typing import Optional, TYPE_CHECKING

from pyproj.database import get_units_map

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.crs.util import get_crs_horizontal_component
from spyops.shared.constant import EPSG


if TYPE_CHECKING:  # pragma: no cover
    from pyproj import CRS
    from pyproj.database import Unit


@cache
def _get_unit_by_name(name: str) -> Optional['Unit']:
    """
    Get Unit by unit name
    """
    units = get_units_map(EPSG.casefold(), category='linear')
    return units.get(name)
# End _get_unit_by_name function


def get_linear_unit_conversion_factor(from_name: str, to_name: str) -> float:
    """
    Get Linear Unit Conversion Factor
    """
    if from_name == to_name:
        return 1.
    from_unit = _get_unit_by_name(from_name)
    to_unit = _get_unit_by_name(to_name)
    if None in (from_unit, to_unit):
        return 1.
    return from_unit.conv_factor / to_unit.conv_factor
# End get_linear_unit_conversion_factor function


def get_unit_name(crs: 'CRS') -> str | None:
    """
    Get Unit Name from a CRS
    """
    crs = get_crs_horizontal_component(crs)
    try:
        # noinspection PyUnresolvedReferences
        return crs.coordinate_system.axis_list[0].unit_name
    except (AttributeError, IndexError):  # pragma: no cover
        return None
# End get_unit_name function


def get_unit_conversion(from_unit: LengthUnit | AreaUnit,
                        to_unit: LengthUnit | AreaUnit) -> float:
    """
    Get Unit Conversion for Length to Length or Area to Area.
    """
    is_length = isinstance(from_unit, LengthUnit)
    if ((is_length and not isinstance(to_unit, LengthUnit)) or
            (not is_length and isinstance(to_unit, LengthUnit))):
        raise TypeError('Cannot convert Length Unit to/from Area Unit')
    if from_unit == to_unit:
        return 1.
    if is_length:
        from_factor = _get_conv_factor(LENGTH_UNIT_LUT[from_unit])
        to_factor = _get_conv_factor(LENGTH_UNIT_LUT[to_unit])
        return from_factor / to_factor
    else:
        from_value, from_factor = AREA_UNIT_LUT[from_unit]
        from_factor *= _get_conv_factor(from_value) ** 2
        to_value, to_factor = AREA_UNIT_LUT[to_unit]
        to_factor *= _get_conv_factor(to_value) ** 2
        return from_factor / to_factor
# End get_unit_conversion function


def _get_conv_factor(value: str | float):
    """
    Get Conversion Factor
    """
    if isinstance(value, str):
        return _get_unit_by_name(value).conv_factor
    return value
# End get_unit_conversion function


LENGTH_UNIT_LUT: dict[LengthUnit, str | float] = {
    LengthUnit.KILOMETERS: 'kilometre',
    LengthUnit.METERS: 'metre',
    LengthUnit.MILES_INTERNATIONAL: 'Statute mile',
    LengthUnit.NAUTICAL_MILES_INTERNATIONAL: 'nautical mile',
    LengthUnit.YARDS_INTERNATIONAL: 'yard',
    LengthUnit.FEET_INTERNATIONAL: 'foot',
    LengthUnit.MILES_US: 'US survey mile',
    LengthUnit.NAUTICAL_MILES_US: 1853.248,
    LengthUnit.YARDS_US: 0.9144018288036576,
    LengthUnit.FEET_US: 'US survey foot',
}


AREA_UNIT_LUT: dict[AreaUnit, tuple[str | float, float]] = {
    AreaUnit.SQUARE_KILOMETERS: ('kilometre', 1.),
    AreaUnit.SQUARE_METERS: ('metre', 1.),
    AreaUnit.SQUARE_MILES_INTERNATIONAL: ('Statute mile', 1.),
    AreaUnit.SQUARE_NAUTICAL_MILES_INTERNATIONAL: ('nautical mile', 1.),
    AreaUnit.SQUARE_YARDS_INTERNATIONAL: ('yard', 1.),
    AreaUnit.SQUARE_FEET_INTERNATIONAL: ('foot', 1.),
    AreaUnit.SQUARE_MILES_US: ('US survey mile', 1.),
    AreaUnit.SQUARE_NAUTICAL_MILES_US: (
        LENGTH_UNIT_LUT[LengthUnit.NAUTICAL_MILES_US], 1.),
    AreaUnit.SQUARE_YARDS_US: (
        LENGTH_UNIT_LUT[LengthUnit.YARDS_US], 1.),
    AreaUnit.SQUARE_FEET_US: ('US survey foot', 1.),

    AreaUnit.HECTARES: ('kilometre', 100.),
    AreaUnit.ACRES_INTERNATIONAL: ('foot', 43560.),
    AreaUnit.ACRES_US: ('US survey foot', 43560.),
}


if __name__ == '__main__':  # pragma: no cover
    pass
