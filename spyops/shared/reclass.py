# -*- coding: utf-8 -*-
"""
Reclassifiers
"""


from abc import ABCMeta, abstractmethod
from math import inf
from numbers import Integral, Number
from statistics import quantiles
from typing import Any, TYPE_CHECKING, Union

from fudgeo.constant import COMMA_SPACE
from numpy import (
    arange, argmin, asarray, cumsum, full, isfinite, ndarray, sort, zeros)

from spyops.shared.constant import EMPTY
from spyops.shared.enumeration import (
    ReclassificationMethod, StandardDeviationOptions)
from spyops.shared.hint import ELEMENT, NUMBER, RECLASS_TABLE
from spyops.shared.stats import Average, Maximum, Minimum, StandardDeviation
from spyops.shared.util import check_str_enum


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Field


class AbstractReclass(metaclass=ABCMeta):
    """
    Abstract Reclass
    """
    def __init__(self, method: ReclassificationMethod,
                 reverse: bool) -> None:
        """
        Initialize the AbstractReclass class
        """
        super().__init__()
        self._method: ReclassificationMethod = method
        self._reverse: bool = reverse
    # End init built-in

    @staticmethod
    def _add_min_max(breaks: list, min_: NUMBER, max_: NUMBER) \
            -> tuple[bool, bool]:
        """
        Add Min and Max to Breaks but only if they extend the range
        """
        add_min, add_max = False, False
        if max(breaks) < max_:
            breaks.append(max_)
            add_max = True
        if min(breaks) > min_:
            breaks.insert(0, min_)
            add_min = True
        return add_min, add_max
    # End _add_min_max method

    @staticmethod
    def _build_labels(breaks: list[NUMBER]) -> list[str]:
        """
        Build Labels
        """
        return [f'{b:f} - {e:f}' for b, e in zip(breaks[:-1], breaks[1:])]
    # End _build_labels method

    @property
    def method(self) -> ReclassificationMethod:
        """
        Reclassification Method
        """
        return self._method
    # End method property

    @abstractmethod
    def _validate(self, value: Any) -> None:
        """
        Validate
        """
        pass
    # End _validate method
    
    @abstractmethod
    def get_breaks(self, element: ELEMENT, field: 'Field',
                   where_clause: str) -> tuple[list[NUMBER], list[str]]:
        """
        Get Breaks
        """
        pass
    # End get_breaks method
# End AbstractReclass class


class ClassesValidationMixin:
    """
    Classes Validation Mixin
    """
    # noinspection PyMethodMayBeStatic
    def _validate(self, value: int) -> None:
        """
        Validate
        """
        if not isinstance(value, Integral):
            # noinspection PyStringConversionWithoutDunderMethod
            raise TypeError(
                f'classes must be an integer, got {type(value)}')
        min_, max_ = 1, 256
        if value < min_ or value > max_:
            raise ValueError(
                f'classes must be between {min_} and {max_} (inclusive)')
    # End _validate method
# End ClassesValidationMixin class


class DefinedIntervalReclass(AbstractReclass):
    """
    Defined Interval Reclassification
    """
    def __init__(self, interval: NUMBER = 100., reverse: bool = False) -> None:
        """
        Initialize the DefinedIntervalReclass class
        """
        super().__init__(
            ReclassificationMethod.DEFINED_INTERVAL, reverse=reverse)
        self._interval: NUMBER = interval
        self._validate(interval)
    # End init built-in

    def _validate(self, value: NUMBER) -> None:
        """
        Validate
        """
        if not isinstance(value, Number):
            raise TypeError(
                f'interval must be a number, got {type(value)}')
        if value <= 0:
            raise ValueError('interval must be greater than 0')
    # End _validate method

    def _build_breaks(self, min_: NUMBER, max_: NUMBER) -> list:
        """
        Build Breaks
        """
        count, rem = divmod(max_ - min_, self._interval)
        count += bool(rem)
        return [min_ + (i * self._interval) for i in range(int(count) + 1)]
    # End _build_breaks method

    def get_breaks(self, element: ELEMENT, field: 'Field',
                   where_clause: str) -> tuple[list[NUMBER], list[str]]:
        """
        Get Breaks
        """
        min_, max_ = _fetch_min_max(
            element, field=field, where_clause=where_clause)
        breaks = self._build_breaks(min_, max_)
        return breaks, self._build_labels(breaks)
    # End get_breaks method
# End DefinedIntervalReclass class


class EqualIntervalReclass(ClassesValidationMixin, AbstractReclass):
    """
    Equal Interval Reclassification
    """
    def __init__(self, classes: int = 10, reverse: bool = False) -> None:
        """
        Initialize the EqualIntervalReclass class
        """
        super().__init__(ReclassificationMethod.EQUAL_INTERVAL, reverse=reverse)
        self._classes: int = classes
        self._validate(classes)
    # End init built-in

    def _build_breaks(self, min_: NUMBER, max_: NUMBER) -> list:
        """
        Build Breaks
        """
        interval = (max_ - min_) / self._classes
        return [min_ + (i * interval) for i in range(self._classes + 1)]
    # End _build_breaks method

    def get_breaks(self, element: ELEMENT, field: 'Field',
                   where_clause: str) -> tuple[list[NUMBER], list[str]]:
        """
        Get Breaks
        """
        min_, max_ = _fetch_min_max(
            element, field=field, where_clause=where_clause)
        breaks = self._build_breaks(min_, max_)
        return breaks, self._build_labels(breaks)
    # End get_breaks method
# End EqualIntervalReclass class


class ManualReclass(AbstractReclass):
    """
    Manual Reclassification
    """
    def __init__(self, table: RECLASS_TABLE) -> None:
        """
        Initialize the ManualReclass class
        """
        super().__init__(ReclassificationMethod.MANUAL, reverse=False)
        self._table: RECLASS_TABLE = table
        self._validate(table)
    # End init built-in

    def _validate(self, value: RECLASS_TABLE) -> None:
        """
        Validate
        """
        if not isinstance(value, (list, tuple)):
            raise TypeError(f'table must be a list or tuple, got {type(value)}')
        if not value:
            raise ValueError('table must contain at least one item')
        msg = ('table must contain lists / tuples with exactly 2 values, '
               'numeric and numeric / text')
        if not all(isinstance(item, (list, tuple)) for item in value):
            raise TypeError(msg)
        if not all(len(item) == 2 for item in value):
            raise TypeError(msg)
        values = [b for b, _ in value]
        if not all(isinstance(v, Number) for v in values):
            raise TypeError(msg)
        if len(set(values)) != len(values):
            raise ValueError('table must contain unique break values')
        if not all(isinstance(label, (Number, str)) for _, label in value):
            raise TypeError(msg)
    # End _validate method

    def _build_breaks(self, min_: NUMBER, max_: NUMBER) \
            -> tuple[list[NUMBER], list[str]]:
        """
        Build Breaks (and Labels)
        """
        table = sorted(self._table)
        breaks = [b for b, _ in table]
        add_min, add_max = self._add_min_max(breaks, min_, max_)
        labels = [str(label) for _, label in table]
        if add_min:
            labels.insert(0, EMPTY)
        if add_max:
            labels.append(EMPTY)
        return breaks, labels
    # End _build_breaks method

    def get_breaks(self, element: ELEMENT, field: 'Field',
                   where_clause: str) -> tuple[list[NUMBER], list[str]]:
        """
        Get Breaks
        """
        min_, max_ = _fetch_min_max(
            element, field=field, where_clause=where_clause)
        return self._build_breaks(min_, max_)
    # End get_breaks method
# End ManualReclass class


class NaturalBreaksReclass(ClassesValidationMixin, AbstractReclass):
    """
    Natural Breaks Reclassification
    """
    def __init__(self, classes: int = 13, reverse: bool = False) -> None:
        """
        Initialize the NaturalBreaksReclass class
        """
        super().__init__(ReclassificationMethod.NATURAL_BREAKS, reverse=reverse)
        self._classes: int = classes
        self._validate(classes)
    # End init built-in

    def get_breaks(self, element: ELEMENT, field: 'Field',
                   where_clause: str) -> tuple[list[NUMBER], list[str]]:
        """
        Get Breaks
        """
        values = _fetch_values(element, field=field, where_clause=where_clause)
        if not values:
            return [], []
        breaks = _fisher_jenks(values, self._classes)
        return breaks, self._build_labels(breaks)
    # End get_breaks method
# End NaturalBreaksReclass class


class QuantileReclass(ClassesValidationMixin, AbstractReclass):
    """
    Quantile Reclassification
    """
    def __init__(self, classes: int = 5, reverse: bool = False) -> None:
        """
        Initialize the QuantileReclass class
        """
        super().__init__(ReclassificationMethod.QUANTILE, reverse=reverse)
        self._classes: int = classes
        self._validate(classes)
    # End init built-in

    def _build_breaks(self, values: list) -> list:
        """
        Build Breaks
        """
        min_, max_ = min(values), max(values)
        return sorted({min_, *quantiles(values, n=self._classes), max_})
    # End _build_breaks method

    def get_breaks(self, element: ELEMENT, field: 'Field',
                   where_clause: str) -> tuple[list[NUMBER], list[str]]:
        """
        Get Breaks
        """
        values = _fetch_values(element, field=field, where_clause=where_clause)
        if not values:
            return [], []
        breaks = self._build_breaks(values)
        return breaks, self._build_labels(breaks)
    # End get_breaks method
# End QuantileReclass class


class StandardDeviationReclass(AbstractReclass):
    """
    Standard Deviation Reclassification
    """
    def __init__(self, deviations: StandardDeviationOptions = (
            StandardDeviationOptions.ONE), reverse: bool = False) -> None:
        """
        Initialize the StandardDeviationReclass class
        """
        super().__init__(
            ReclassificationMethod.STANDARD_DEVIATION, reverse=reverse)
        self._deviations: StandardDeviationOptions = deviations
        self._validate(deviations)
    # End init built-in

    def _validate(self, value: StandardDeviationOptions) -> None:
        """
        Validate
        """
        check_str_enum(value, enum=StandardDeviationOptions)
    # End _validate method

    def _get_classes(self) -> tuple[int, NUMBER]:
        """
        Get Classes
        """
        lut = {StandardDeviationOptions.ONE: (5, 1.),
               StandardDeviationOptions.HALF: (9, 1 / 2),
               StandardDeviationOptions.THIRD: (15, 1 / 3),
               StandardDeviationOptions.QUARTER: (17, 1 / 4)}
        return lut[self._deviations]
    # End _get_classes method

    def _build_extended_labels(self, breaks: list, devs: list) -> list[str]:
        """
        Build Extended Labels
        """
        std_dev = 'Std. Dev.'
        labels = self._build_labels(breaks)
        first_idx, last_idx = 0, len(labels) - 1
        for i, (lab, low, high) in enumerate(zip(labels, devs[:-1], devs[1:])):
            if i == first_idx:
                labels[i] = f'{lab} (< {low:.3f} {std_dev})'
            elif i == last_idx:
                labels[i] = f'{lab} (> {high:.3f} {std_dev})'
            else:
                labels[i] = f'{lab} ({low:.3f} - {high:.3f} {std_dev})'
        return labels
    # End _build_extended_labels method

    def _build_breaks(self, avg: NUMBER, dev: NUMBER, min_: NUMBER,
                      max_: NUMBER, half_count: int,
                      size: NUMBER) -> tuple[list, list]:
        """
        Build Breaks
        """
        sized_dev = dev * size
        low = avg - (sized_dev / 2.)
        high = avg + (sized_dev / 2.)
        breaks = [low, high]
        breaks.extend([low - sized_dev * (i + 1) for i in range(half_count)])
        breaks.extend([high + sized_dev * (i + 1) for i in range(half_count)])
        breaks = sorted(breaks)
        devs = [(size / 2) + (size * i)
                for i in range(-half_count - 1, half_count + 1)]
        while min(breaks) < min_:
            breaks.pop(0)
            devs.pop(0)
        if min(breaks) > min_:
            breaks.insert(0, min_)
            devs.insert(0, devs[0])
        while max(breaks) > max_:
            breaks.pop()
            devs.pop()
        if max(breaks) < max_:
            breaks.append(max_)
            devs.append(devs[-1])
        return breaks, devs
    # End _build_breaks method

    def get_breaks(self, element: ELEMENT, field: 'Field',
                   where_clause: str) -> tuple[list[NUMBER], list[str]]:
        """
        Get Breaks
        """
        stats = (Average(field), StandardDeviation(field),
                 Minimum(field), Maximum(field))
        stat_names = COMMA_SPACE.join([stat.aggregate for stat in stats])
        sql = f"""
            SELECT {stat_names}
            FROM {element.escaped_name}
            WHERE {field.escaped_name} IS NOT NULL
        """
        if where_clause:
            sql = f'{sql} AND ({where_clause})'
        cursor = element.geopackage.connection.execute(sql)
        avg, dev, min_, max_ = cursor.fetchone()
        count, size = self._get_classes()
        half_count = int((count - 1) / 2)
        breaks, devs = self._build_breaks(
            avg=avg, dev=dev, min_=min_, max_=max_,
            half_count=half_count, size=size)
        return breaks, self._build_extended_labels(breaks, devs)
    # End get_breaks method
# End StandardDeviationReclass class


class UniqueValuesReclass(AbstractReclass):
    """
    Unique Values
    """
    def __init__(self, reverse: bool = False) -> None:
        """
        Initialize the UniqueValuesReclass class
        """
        super().__init__(ReclassificationMethod.UNIQUE_VALUES, reverse=reverse)
    # End init built-in

    def _validate(self, value: Any) -> None:
        """
        Validate
        """
        pass
    # End _validate method

    def get_breaks(self, element: ELEMENT, field: 'Field',
                   where_clause: str) -> tuple[list[NUMBER], list[str]]:
        """
        Get Breaks
        """
        return [], []
    # End get_breaks method
# End UniqueValuesReclass class


def _fisher_jenks(values: Union[list[NUMBER], 'ndarray'],
                  count: int) -> list[NUMBER]:
    """
    Fisher-Jenks natural breaks
    """
    values = asarray(values, dtype=float)
    values = values[isfinite(values)]
    if not (length := values.size):
        return []
    if count > length:
        return []
    values = sort(values)
    if count == 1:
        return [values[0], values[-1]]

    n1 = length + 1
    count1 = count + 1

    prefix_sum = zeros(n1, dtype=float)
    prefix_sum[1:] = cumsum(values)
    prefix_sum_sq = zeros(n1, dtype=float)
    prefix_sum_sq[1:] = cumsum(values * values)

    dp = full((count1, n1), fill_value=inf, dtype=float)
    backtrack = zeros((count1, n1), dtype=int)

    dp[0, 0] = 0
    for k in range(1, count1):
        previous = dp[k - 1]
        current = dp[k]
        for i in range(k, n1):
            j = arange(k - 1, i, dtype=int)
            sums = prefix_sum[i] - prefix_sum[j]
            sums_sq = prefix_sum_sq[i] - prefix_sum_sq[j]
            costs = previous[j] + sums_sq - (sums * sums / (i - j))
            best_offset = argmin(costs)
            best_j = j[best_offset]
            current[i] = costs[best_offset]
            backtrack[k, i] = best_j

    i = length
    breaks = [values[-1]]
    for k in range(count, 1, -1):
        j = backtrack[k, i]
        breaks.append(values[j - 1])
        i = j
    breaks.append(values[0])
    breaks.reverse()
    return breaks
# End _fisher_jenks function


def _fetch_min_max(element: ELEMENT, field: 'Field',
                   where_clause: str) -> tuple[NUMBER, NUMBER]:
    """
    Fetch Minimum and Maximum values
    """
    stats = Minimum(field), Maximum(field)
    stat_names = COMMA_SPACE.join([stat.aggregate for stat in stats])
    sql = f"""
        SELECT {stat_names} 
        FROM {element.escaped_name}
        WHERE {field.escaped_name} IS NOT NULL
    """
    if where_clause:
        sql = f'{sql} AND ({where_clause})'
    cursor = element.geopackage.connection.execute(sql)
    return cursor.fetchone()
# End _fetch_min_max function


def _fetch_values(element: ELEMENT, field: 'Field', where_clause: str) -> list:
    """
    Fetch Values
    """
    field_name = field.escaped_name
    sql = f"""
        SELECT {field_name} 
        FROM {element.escaped_name} 
        WHERE {field_name} IS NOT NULL
    """
    if where_clause:
        sql = f'{sql} AND ({where_clause})'
    cursor = element.geopackage.connection.execute(sql)
    return [v for v, in cursor.fetchall()]
# End _fetch_values function


if __name__ == '__main__':  # pragma: no cover
    pass
