# -*- coding: utf-8 -*-
"""
Conversion Utilities
"""


from typing import Counter

from fudgeo import Field

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


if __name__ == '__main__':  # pragma: no cover
    pass
