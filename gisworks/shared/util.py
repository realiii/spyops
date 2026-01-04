# -*- coding: utf-8 -*-
"""
Utilities
"""


from re import IGNORECASE, compile as recompile
from typing import Any, Callable

from fudgeo.sql import KEYWORDS
from fudgeo.util import NAME_MATCHER
from shapely import GeometryCollection

from gisworks.shared.base import GeometryConfig
from gisworks.shared.constant import (
    DOUBLE_UNDER, EMPTY, GEOMS_ATTR, SPACE, UNDERSCORE)
from gisworks.shared.enumeration import Setting
from gisworks.shared.hint import EXTENT, GPKG


NON_WORD_REPLACER: Callable = recompile(r'\W+', IGNORECASE).sub


def make_unique_name(name: str, names: set[str]) -> str:
    """
    Make Unique Name accounting for case sensitivity
    """
    if name.casefold() not in names:
        names.add(name.casefold())
        return name
    counter = 1
    new_name = f'{name}_{counter}'
    while new_name.casefold() in names:
        counter += 1
        new_name = f'{name}_{counter}'
    names.add(new_name.casefold())
    return new_name
# End make_unique_name function


def element_names(geopackage: GPKG) -> set[str]:
    """
    GeoPackage Element Names (lower case)
    """
    names = {t.casefold() for t in geopackage.tables}
    names.update({f.casefold() for f in geopackage.feature_classes})
    return names
# End element_names function


def make_valid_name(name: str, prefix: str) -> str:
    """
    Make Valid Name
    """
    if name is None:
        return 'none'
    if not (name := name.strip()):
        return 'empty'
    if name in KEYWORDS or not name[0].isalpha():
        name = f'{prefix}_{name}'
    name = NON_WORD_REPLACER(UNDERSCORE, name).rstrip(UNDERSCORE)
    name = _replace_double_under(name).rstrip(UNDERSCORE)
    if NAME_MATCHER(name):
        return name
    else:  # pragma: no cover
        return make_valid_name(name, prefix=prefix)
# End _make_valid_name function


def _replace_double_under(name: str) -> str:
    """
    Replace Double Underscore with Single Underscore
    """
    while DOUBLE_UNDER in name:
        name = name.replace(DOUBLE_UNDER, UNDERSCORE)
    return name
# End _replace_double_under function


def expand_extent(extent: EXTENT) -> EXTENT:
    """
    Expand Extent for R-Tree Inaccuracy
    """
    tol = 12.5 * 10 ** -8
    up = 1 + tol
    down = 1 - tol
    min_x, min_y, max_x, max_y = extent
    return min_x * down, min_y * down, max_x * up, max_y * up
# End expand_extent function


def extend_records(results: list[tuple], records: list[tuple],
                   config: GeometryConfig) -> None:
    """
    Extend Records
    """
    srs_id = config.srs_id
    cls = config.geometry_cls
    combiner = config.combiner
    is_multi = config.is_multi
    filter_types = _, multi_cls = config.filter_types
    for result, attrs in results:
        if result.is_empty:
            continue
        if isinstance(result, GeometryCollection):
            result = multi_cls([r for r in getattr(result, GEOMS_ATTR)
                                if isinstance(r, filter_types)])
        elif not isinstance(result, filter_types):
            continue
        result = combiner(result)
        if is_multi:
            if not hasattr(result, GEOMS_ATTR):
                result = multi_cls([result])
            records.append((cls.from_wkb(result.wkb, srs_id=srs_id), *attrs))
        else:
            records.extend([(cls.from_wkb(part.wkb, srs_id=srs_id), *attrs)
                            for part in getattr(result, GEOMS_ATTR, [result])])
# End extend_records function


def safe_int(value: Any) -> int | None:
    """
    Simple Conversion to int, None if fails
    """
    try:
        return int(safe_float(value))
    except (AttributeError, ValueError, TypeError):
        return None
# End safe_int function


def safe_float(value: Any) -> float | None:
    """
    Simple Conversion to float, None default value
    """
    try:
        return float(value)
    except (AttributeError, ValueError, TypeError):
        return None
# End safe_float function


def as_title(setting: Setting | str | None) -> str:
    """
    Change a setting enumeration value to a title text for exceptions
    """
    if setting is None:
        return EMPTY
    if setting == Setting.XY_TOLERANCE:
        return 'XY Tolerance'
    return str(setting).replace(UNDERSCORE, SPACE).title()
# End as_title function


if __name__ == '__main__':  # pragma: no cover
    pass
