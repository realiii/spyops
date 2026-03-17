# -*- coding: utf-8 -*-
"""
Units
"""


from functools import cache
from math import nan
from typing import Optional, Self, TYPE_CHECKING, Type, Union

from bottleneck import nanmean
from numpy import isfinite, sign, zeros
from pyproj.database import get_units_map

from spyops.crs.constant import EPSG
from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.crs.util import get_crs_horizontal_component
from spyops.shared.constant import EMPTY, SPACE, UNDERSCORE
from spyops.shared.util import safe_float


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray
    from pyproj import CRS
    from pyproj.database import Unit


def degrees_to_meters(crs: 'CRS', coords: 'ndarray',
                      value: Union[float, 'ndarray']) -> 'ndarray':
    """
    Convert Degrees to Meters, using the given CRS and latitude / longitude
    coordinates.
    """
    value += 0
    if isinstance(value, (float, int)) and not value:
        return zeros(len(coords), dtype=float)
    geod = crs.get_geod()
    lon = coords[:, 0]
    lat = coords[:, 1]
    *_, east = geod.inv(lons1=lon, lats1=lat, lats2=lat, lons2=lon + value)
    *_, west = geod.inv(lons1=lon, lats1=lat, lats2=lat, lons2=lon - value)
    *_, north = geod.inv(lons1=lon, lats1=lat, lons2=lon, lats2=lat + value)
    *_, south = geod.inv(lons1=lon, lats1=lat, lons2=lon, lats2=lat - value)
    xs = _calculate_average_length(east, west)
    ys = _calculate_average_length(north, south)
    return _calculate_average_length(xs, ys) * sign(value)
# End degrees_to_meters function


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
        from_factor = get_conv_factor(LENGTH_UNIT_LUT[from_unit])
        to_factor = get_conv_factor(LENGTH_UNIT_LUT[to_unit])
        return from_factor / to_factor
    else:
        from_value, from_factor = AREA_UNIT_LUT[from_unit]
        from_factor *= get_conv_factor(from_value) ** 2
        to_value, to_factor = AREA_UNIT_LUT[to_unit]
        to_factor *= get_conv_factor(to_value) ** 2
        return from_factor / to_factor
# End get_unit_conversion function


def get_conv_factor(value: str | float):
    """
    Get Conversion Factor
    """
    if isinstance(value, str):
        return _get_unit_by_name(value).conv_factor
    return value
# End get_conv_factor function


def unit_factory(value: str) -> Optional[Union['_LinearUnit', 'DecimalDegrees']]:
    """
    Unit Factory for Linear Units or Decimal Degrees
    """
    if not value:
        return None
    parts = str(value).strip().split(maxsplit=1)
    if len(parts) != 2:
        return None
    value, name = parts
    if (value := safe_float(value)) is None:
        return None
    if (unit_class := UNIT_CLASS_MAP.get(name.strip().casefold())) is None:
        return None
    return unit_class(value)
# End unit_factory function


@cache
def _get_unit_by_name(name: str) -> Optional['Unit']:
    """
    Get Unit by unit name
    """
    units = get_units_map(EPSG.casefold(), category='linear')
    return units.get(name)
# End _get_unit_by_name function


def _calculate_average_length(first: 'ndarray', second: 'ndarray') -> 'ndarray':
    """
    Calculate Average Length
    """
    lengths = zeros((len(first), 2), dtype=float)
    for i, data in enumerate((first, second)):
        data[data == 0] = nan
        data[~isfinite(data)] = nan
        lengths[:, i] = data
    return nanmean(lengths, axis=1)
# End _calculate_average_length function


class _LinearUnit:
    """
    Linear Unit
    """
    def __init__(self, value: str | float, unit: LengthUnit) -> None:
        """
        Initialize the _LinearUnit class
        """
        super().__init__()
        self._value: float | None = safe_float(value)
        self._unit: LengthUnit = unit
    # End init built-in

    def __repr__(self) -> str:
        """
        Representation Override
        """
        return f'{self.__class__.__name__}({self.value})'
    # End repr built-in

    def __eq__(self, other: Self) -> bool:
        """
        Equals Override
        """
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value == other.value and self.unit == other.unit
    # End eq built-in

    @property
    def value(self) -> float | None:
        """
        Value
        """
        return self._value
    # End value property

    @property
    def unit(self) -> LengthUnit:
        """
        Unit
        """
        return self._unit
    # End unit property

    def to_meters(self) -> float | None:
        """
        To Meters
        """
        if self.value is None:
            return None
        return self.value * get_unit_conversion(
            from_unit=self.unit, to_unit=LengthUnit.METERS)
    # End to_meters method
# End _LinearUnit class


class FeetInternational(_LinearUnit):
    """
    Feet International
    """
    def __init__(self, value: str| float) -> None:
        """
        Initialize the FeetInternational class
        """
        super().__init__(value, unit=LengthUnit.FEET_INTERNATIONAL)
    # End init built-in
# End FeetInternational class


class FeetUS(_LinearUnit):
    """
    Feet US
    """
    def __init__(self, value: str | float) -> None:
        """
        Initialize the FeetUS class
        """
        super().__init__(value, unit=LengthUnit.FEET_US)
    # End init built-in
# End FeetUS class


class Kilometers(_LinearUnit):
    """
    Kilometers
    """
    def __init__(self, value: str | float) -> None:
        """
        Initialize the Kilometers class
        """
        super().__init__(value, unit=LengthUnit.KILOMETERS)
    # End init built-in
# End Kilometers class


class Meters(_LinearUnit):
    """
    Meters
    """
    def __init__(self, value: str | float) -> None:
        """
        Initialize the Meters class
        """
        super().__init__(value, unit=LengthUnit.METERS)
    # End init built-in
# End Meters class


class MilesInternational(_LinearUnit):
    """
    Miles International
    """
    def __init__(self, value: str | float) -> None:
        """
        Initialize the MilesInternational class
        """
        super().__init__(value, unit=LengthUnit.MILES_INTERNATIONAL)
    # End init built-in
# End MilesInternational class


class MilesUS(_LinearUnit):
    """
    Miles US
    """
    def __init__(self, value: str | float) -> None:
        """
        Initialize the MilesUS class
        """
        super().__init__(value, unit=LengthUnit.MILES_US)
    # End init built-in
# End MilesUS class


class NauticalMilesInternational(_LinearUnit):
    """
    Nautical Miles International
    """
    def __init__(self, value: str | float) -> None:
        """
        Initialize the NauticalMilesInternational class
        """
        super().__init__(value, unit=LengthUnit.NAUTICAL_MILES_INTERNATIONAL)
    # End init built-in
# End NauticalMilesInternational class


class NauticalMilesUS(_LinearUnit):
    """
    Nautical Miles US
    """
    def __init__(self, value: str | float) -> None:
        """
        Initialize the NauticalMilesUS class
        """
        super().__init__(value, unit=LengthUnit.NAUTICAL_MILES_US)
    # End init built-in
# End NauticalMilesUS class


class YardsInternational(_LinearUnit):
    """
    Yards International
    """
    def __init__(self, value: str | float) -> None:
        """
        Initialize the YardsInternational class
        """
        super().__init__(value, unit=LengthUnit.YARDS_INTERNATIONAL)
    # End init built-in
# End YardsInternational class


class YardsUS(_LinearUnit):
    """
    Yards US
    """
    def __init__(self, value: str | float) -> None:
        """
        Initialize the YardsUS class
        """
        super().__init__(value, unit=LengthUnit.YARDS_US)
    # End init built-in
# End YardsUS class


class DecimalDegrees:
    """
    Decimal Degrees
    """
    def __init__(self, value: str | float) -> None:
        """
        Initialize the DecimalDegrees class
        """
        super().__init__()
        self._value: float | None = safe_float(value)
    # End init built-in

    def __repr__(self) -> str:
        """
        Representation Override
        """
        return f'{self.__class__.__name__}({self.value})'
    # End repr built-in

    def __eq__(self, other: Self) -> bool:
        """
        Equals Override
        """
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value == other.value
    # End eq built-in

    @property
    def value(self) -> float | None:
        """
        Value
        """
        return self._value
    # End value property
# End DecimalDegrees class


# Aliases
Feet = FeetInternational
USSurveyFeet = FeetUS
Kilometres = Kilometers
Metres = Meters
Miles = MilesInternational
StatuteMiles = MilesInternational
USSurveyMiles = MilesUS
NauticalMiles = NauticalMilesInternational
Yards = YardsInternational
USSurveyYards = YardsUS
Degrees = DecimalDegrees


UNIT_CLASS_MAP: dict[str, Type['_LinearUnit'] | Type['DecimalDegrees']] = {
    'ft': FeetInternational,
    'feet': FeetInternational,
    'foot': FeetInternational,
    'feet_international': FeetInternational,
    'foot_international': FeetInternational,
    'us_survey_foot': FeetUS,
    'us_survey_feet': FeetUS,
    'feet_us': FeetUS,
    'foot_us': FeetUS,
    'us_feet': FeetUS,
    'us_foot': FeetUS,

    'km': Kilometers,
    'kms': Kilometers,
    'kilometers': Kilometers,
    'kilometres': Kilometers,
    'kilometre': Kilometers,
    'kilometer': Kilometers,

    'm': Meters,
    'ms': Meters,
    'meters': Meters,
    'metres': Meters,
    'meter': Meters,
    'metre': Meters,

    'mi': MilesInternational,
    'miles': MilesInternational,
    'mile': MilesInternational,
    'miles_international': MilesInternational,
    'mile_international': MilesInternational,
    'statute_miles': StatuteMiles,
    'statute_mile': StatuteMiles,
    'us_survey_miles': MilesUS,
    'us_survey_mile': MilesUS,
    'miles_us': MilesUS,
    'mile_us': MilesUS,
    'us_miles': MilesUS,
    'us_mile': MilesUS,

    'nm': NauticalMilesInternational,
    'nautical_miles': NauticalMilesInternational,
    'nautical_mile': NauticalMilesInternational,
    'nautical_miles_international': NauticalMilesInternational,
    'nautical_mile_international': NauticalMilesInternational,
    'nautical_miles_us': NauticalMilesUS,
    'nautical_mile_us': NauticalMilesUS,
    'us_nautical_miles': NauticalMilesUS,
    'us_nautical_mile': NauticalMilesUS,

    'yd': YardsInternational,
    'yds': YardsInternational,
    'yards': YardsInternational,
    'yard': YardsInternational,
    'yards_international': YardsInternational,
    'yard_international': YardsInternational,
    'us_survey_yards': YardsUS,
    'us_survey_yard': YardsUS,
    'yards_us': YardsUS,
    'yard_us': YardsUS,
    'us_yards': YardsUS,
    'us_yard': YardsUS,

    'dd': DecimalDegrees,
    'deg': DecimalDegrees,
    'degrees': DecimalDegrees,
    'degree': DecimalDegrees,
    'decimal_degrees': DecimalDegrees,
    'decimal_degree': DecimalDegrees,
}
UNIT_CLASS_MAP.update(
    {k.replace(UNDERSCORE, SPACE): v for k, v in UNIT_CLASS_MAP.items()})
UNIT_CLASS_MAP.update(
    {k.replace(UNDERSCORE, EMPTY): v for k, v in UNIT_CLASS_MAP.items()})


LENGTH_UNIT_LUT: dict[LengthUnit, str | float] = {
    LengthUnit.FEET_INTERNATIONAL: 'foot',
    LengthUnit.FEET_US: 'US survey foot',
    LengthUnit.KILOMETERS: 'kilometre',
    LengthUnit.METERS: 'metre',
    LengthUnit.MILES_INTERNATIONAL: 'Statute mile',
    LengthUnit.MILES_US: 'US survey mile',
    LengthUnit.NAUTICAL_MILES_INTERNATIONAL: 'nautical mile',
    LengthUnit.NAUTICAL_MILES_US: 1853.248,
    LengthUnit.YARDS_INTERNATIONAL: 'yard',
    LengthUnit.YARDS_US: 0.9144018288036576,
}


AREA_UNIT_LUT: dict[AreaUnit, tuple[str | float, float]] = {
    AreaUnit.ACRES_INTERNATIONAL: ('foot', 43560.),
    AreaUnit.ACRES_US: ('US survey foot', 43560.),
    AreaUnit.HECTARES: ('kilometre', 100.),
    AreaUnit.SQUARE_FEET_INTERNATIONAL: ('foot', 1.),
    AreaUnit.SQUARE_FEET_US: ('US survey foot', 1.),
    AreaUnit.SQUARE_KILOMETERS: ('kilometre', 1.),
    AreaUnit.SQUARE_METERS: ('metre', 1.),
    AreaUnit.SQUARE_MILES_INTERNATIONAL: ('Statute mile', 1.),
    AreaUnit.SQUARE_MILES_US: ('US survey mile', 1.),
    AreaUnit.SQUARE_NAUTICAL_MILES_INTERNATIONAL: ('nautical mile', 1.),
    AreaUnit.SQUARE_NAUTICAL_MILES_US: (
        LENGTH_UNIT_LUT[LengthUnit.NAUTICAL_MILES_US], 1.),
    AreaUnit.SQUARE_YARDS_INTERNATIONAL: ('yard', 1.),
    AreaUnit.SQUARE_YARDS_US: (LENGTH_UNIT_LUT[LengthUnit.YARDS_US], 1.),
}


if __name__ == '__main__':  # pragma: no cover
    pass
