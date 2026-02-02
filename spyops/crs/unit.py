# -*- coding: utf-8 -*-
"""
Units
"""


from functools import cache
from typing import Optional, TYPE_CHECKING

from pyproj.database import get_units_map

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


def get_unit_conversion_factor(from_name: str, to_name: str) -> float:
    """
    Get Unit Conversion Factor
    """
    if from_name == to_name:
        return 1.
    from_unit = _get_unit_by_name(from_name)
    to_unit = _get_unit_by_name(to_name)
    if None in (from_unit, to_unit):
        return 1.
    return from_unit.conv_factor / to_unit.conv_factor
# End get_unit_conversion_factor function


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


if __name__ == '__main__':  # pragma: no cover
    pass
