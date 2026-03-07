# -*- coding: utf-8 -*-
"""
Statistics Functions for use within SQLite
"""


from math import isfinite
from statistics import (
    StatisticsError, mode as _mode, stdev as _standard_deviation, variance)
from typing import Any, Callable


def mode(values: list) -> Any:
    """
    Calculate Mode, ignoring Null values.  Works on a sequence of
    hashable objects (strings, datetime, float, int, etc.).
    """
    if not (values := _filter_none(values)):
        return None
    try:
        return _mode(values)
    except (IndexError, TypeError):
        return None
# End mode function


def stdev(values: list) -> float | None:
    """
    Calculate Standard Deviation, ignoring Null values and non-finite values.
    If a non-number is encountered, the result is None.
    """
    return _calculate_stat(_standard_deviation, values)
# End stdev function


def var(values: list) -> float | None:
    """
    Calculate Variance, ignoring Null values and non-finite values.
    If a non-number is encountered, the result is None.
    """
    return _calculate_stat(variance, values)
# End var function


def first(values: list) -> Any:
    """
    Find the first value, ignores Null values.
    """
    if not (values := _filter_none(values)):
        return None
    return values[0]
# End first function


def last(values: list) -> Any:
    """
    Find the last value, ignores Null values.
    """
    if not (values := _filter_none(values)):
        return None
    return values[-1]
# End last function


def _calculate_stat(func: Callable, values: list) -> float | None:
    """
    Calculate Statistic, ignoring Null values and non-finite values.
    """
    if not (values := _filter_none(values)):
        return None
    try:
        if not (values := [v for v in values if isfinite(v)]):
            return None
    except TypeError:
        return None
    try:
        return func(values)
    except (IndexError, ValueError, StatisticsError):
        return None
# End _calculate_stat function


def _filter_none(values: list) -> list:
    """
    Filter None's out of a list
    """
    return [v for v in values if v is not None]
# End _filter_none function


STATS_FUNCS: dict[str, Callable] = {
    'mode': mode,
    'stdev': stdev,
    'var': var,
    'first': first,
    'last': last,
}


if __name__ == '__main__':  # pragma: no cover
    pass
