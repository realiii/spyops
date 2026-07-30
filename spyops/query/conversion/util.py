# -*- coding: utf-8 -*-
"""
Conversion Utilities
"""


from csv import Dialect, excel
from typing import Counter

from fudgeo import Field

from spyops.shared.constant import COMMA
from spyops.shared.field import make_unique_fields
from spyops.shared.hint import FIELDS


def _make_unique_fields(fields: list[Field]) -> FIELDS:
    """
    Make Unique Fields
    """
    names = [f.name.casefold() for f in fields]
    if len(names) == len(set(names)):
        return tuple(fields)
    visited = set()
    names = [n for n, count in Counter(names).items() if count > 1]
    for i, field in enumerate(fields):
        lower = field.name.casefold()
        if lower not in names:
            continue
        if lower not in visited:
            visited.add(lower)
            continue
        field, = make_unique_fields(fields, [field])
        # noinspection PyTypeChecker
        fields[i] = field
    return tuple(fields)
# End _make_unique_fields method


def _get_dialect(delimiter: str) -> Dialect:
    """
    Get Dialect
    """
    dialect = excel()
    dialect.lineterminator = '\n'
    if isinstance(delimiter, str):
        if stripped := delimiter.strip():
            dialect.delimiter = stripped[0]
        else:
            tab = '\t'
            if tab in delimiter:
                dialect.delimiter = tab
            else:
                dialect.delimiter = COMMA
    else:
        dialect.delimiter = COMMA
    return dialect
# End _get_dialect function


if __name__ == '__main__':  # pragma: no cover
    pass
