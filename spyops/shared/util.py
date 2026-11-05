# -*- coding: utf-8 -*-
"""
Utilities
"""


from enum import IntFlag, StrEnum
from math import nan
from re import IGNORECASE, compile as recompile
from typing import Any, Callable

from fudgeo.constant import FID, SHAPE
from fudgeo.sql import KEYWORDS
from fudgeo.util import NAME_MATCHER
from numpy import (
    arange, array, diff, full, isfinite, lexsort, ndarray, nonzero, repeat,
    unique)

from spyops.shared.constant import DOUBLE_UNDER, UNDERSCORE
from spyops.shared.hint import EXTENT, GPKG


FIELD_NAME_MATCHER: Callable = recompile(r'^[a-zA-Z]\w*$', IGNORECASE).match
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


def make_valid_table_name(name: str | None, prefix: str) -> str:
    """
    Make Valid Table Name
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
        return make_valid_table_name(name, prefix=prefix)
# End make_valid_table_name function


def make_valid_field_name(name: str) -> str:
    """
    Make Valid Field Name, assumption that name is already upper case
    """
    if not name:
        return 'FIELD'
    if name in (FID.upper(), SHAPE.upper()):
        name = f'{name}_1'
    if name in KEYWORDS or not FIELD_NAME_MATCHER(name):
        name = f'FIELD_{name}'
    name = _replace_double_under(name).rstrip(UNDERSCORE)
    if FIELD_NAME_MATCHER(name):
        return name
    name = NON_WORD_REPLACER(UNDERSCORE, name).rstrip(UNDERSCORE)
    return make_valid_field_name(_replace_double_under(name))
# End make_valid_field_name function


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


def safe_int(value: Any, strict: bool = False) -> int | None:
    """
    Simple Conversion to int, None if fails
    """
    try:
        if strict:
            return int(value)
        else:
            # noinspection bad-argument-type
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


def check_str_enum(value: Any, enum: type[StrEnum]) -> Any:
    """
    Check Str Enumeration
    """
    if isinstance(value, enum):
        return value
    if isinstance(value, str):
        return enum(value.casefold())
    return enum(value)
# End check_str_enum function


def check_int_flag_enum(value: Any, enum: type[IntFlag]) -> Any:
    """
    Check IntFlag Enumeration
    """
    if isinstance(value, enum):
        return value
    return enum(value)
# End check_int_flag_enum function


def nada(value: Any) -> Any:
    """
    Nada
    """
    return value
# End nada function


def find_slice_indexes(indexes: 'ndarray') -> tuple[int, ...]:
    """
    Find Slice Indexes, include the final index to allow for easier striding
    """
    if not len(indexes):
        return ()
    ids, = nonzero(diff(indexes))
    ids += 1
    return 0, *[int(i) for i in ids], len(indexes)
# End find_slice_indexes function


def get_smallest_indexes(ids: 'ndarray', values: 'ndarray', n: int = 1) \
        -> tuple['ndarray', 'ndarray']:
    """
    Extract the indexes of the smallest n values for each group of unique
    identifiers
    """
    if not len(ids):
        return array([]), array([], dtype=int)
    indexes = lexsort((values, ids))
    uids, starts, counts = unique(
        ids[indexes], return_index=True, return_counts=True)
    offsets = arange(n)
    group_indexes = starts[:, None] + offsets
    mask = offsets < counts[:, None]
    return repeat(uids, n)[mask.ravel()], indexes[group_indexes[mask]]
# End get_smallest_indexes function


def get_smallest_values(ids: 'ndarray', values: 'ndarray', n: int = 1) \
        -> tuple['ndarray', 'ndarray']:
    """
    Extract the smallest n values for each group of unique identifiers
    """
    if not len(ids):
        return array([]), array([])
    indexes = lexsort((values, ids))
    uids, starts, counts = unique(
        ids[indexes], return_index=True, return_counts=True)
    smalls = full((len(uids), n), fill_value=nan, dtype=float)
    offsets = arange(n)
    group_indexes = starts[:, None] + offsets
    mask = offsets < counts[:, None]
    smalls[mask] = values[indexes][group_indexes[mask]]
    smalls = smalls.reshape(-1)
    mask = isfinite(smalls)
    return repeat(uids, n)[mask], smalls[mask]
# get_smallest_values function


def make_none_mask(values: 'ndarray') -> 'ndarray':
    """
    Create a mask of None values for the given array.
    """
    # NOTE this is the way
    return values == None
# End make_none_mask function


if __name__ == '__main__':  # pragma: no cover
    pass
