# -*- coding: utf-8 -*-
"""
Statistics Functions for use within SQLite
"""


from abc import ABCMeta, abstractmethod
from collections import Counter
from datetime import datetime, timezone
from math import isfinite
from statistics import (
    StatisticsError, mean as _mean, median as _median, mode as _mode,
    quantiles as _quantiles, stdev as _standard_deviation, variance as _var)
from typing import Any, Callable, Self, Type

from fudgeo import Field
from fudgeo.enumeration import FieldType

from spyops.shared.constant import COMMA, SPYOPS, UNDERSCORE
from spyops.shared.enumeration import Statistic
from spyops.shared.field import DATES, FREQUENCY, NUMBERS, get_data_type
from spyops.shared.sql import ROWID


def _kurt(values: list) -> float | None:
    """
    Uses the Fisher's definition, Normal = 0.
    """
    n = len(values)
    if n < 4:
        return None
    avg = _mean(values)
    variance = _var(values)
    moment = sum([(x - avg) ** 4 for x in values]) / n
    return (moment / (variance ** 2)) - 3
# End _kurt function


def _skew(values: list) -> float | None:
    """
    Skewness via Adjusted Fisher-Pearson's Skewness.
    """
    n = len(values)
    if n < 3:
        return None
    factor = n / ((n - 1) * (n - 2))
    avg = _mean(values)
    std = _standard_deviation(values)
    return factor * sum([((x - avg) / std) ** 3 for x in values])
# End _skew function


def _cv(values: list) -> float | None:
    """
    Coefficient of Variation
    """
    avg = _mean(values)
    std = _standard_deviation(values)
    return 100 * std / avg
# End _cv function


def _first_quartile(values: list) -> float | None:
    """
    First Quartile
    """
    # noinspection PyArgumentEqualDefault
    return _quantiles(values, n=4)[0]
# End _first_quartile function


def _third_quartile(values: list) -> float | None:
    """
    Third Quartile
    """
    # noinspection PyArgumentEqualDefault
    return _quantiles(values, n=4)[-1]
# End _third_quartile function


def _interquartile_range(values: list) -> float | None:
    """
    Interquartile Range
    """
    # noinspection PyArgumentEqualDefault
    a, _, c = _quantiles(values, n=4)
    return c - a
# End _interquartile_range function


def _count_outlier(values: list) -> int | None:
    """
    Outlier Count
    """
    # noinspection PyArgumentEqualDefault
    a, _, c = _quantiles(values, n=4)
    if not (rng := 1.5 * (c - a)):
        return None
    lower, upper = a - rng, c + rng
    return sum(v < lower or v > upper for v in values)
# End _count_outlier function


def _least(values: list) -> Any:
    """
    Least Common
    """
    *_, (value, _) = Counter(values).most_common()
    return value
# End _least function


def _most(values: list) -> Any:
    """
    Most Common
    """
    (value, _), *_ = Counter(values).most_common()
    return value
# End _most function


def mode(values: list) -> Any:
    """
    Calculate Mode, ignoring Null values.  Works on a sequence of
    hashable objects (strings, datetime, float, int, etc.).
    """
    if not (values := _filter_none(values)):
        return None
    try:
        return _mode(values)
    except (IndexError, TypeError, StatisticsError):
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
    return _calculate_stat(_var, values)
# End var function


def median(values: list) -> float | None:
    """
    Calculate Median, ignoring Null values and non-finite values.
    If a non-number is encountered, the result is None.
    """
    return _calculate_stat(_median, values)
# End median function


def kurtosis(values: list) -> float | None:
    """
    Calculate Kurtosis, ignoring Null values and non-finite values.
    If a non-number is encountered, the result is None.
    """
    return _calculate_stat(_kurt, values)
# End kurtosis function


def skewness(values: list) -> float | None:
    """
    Calculate Skewness, ignoring Null values and non-finite values.
    If a non-number is encountered, the result is None.
    """
    return _calculate_stat(_skew, values)
# End skewness function


def coefficient_of_variation(values: list) -> float | None:
    """
    Calculate Coefficient of Variation, ignoring Null values and non-finite
    values. If a non-number is encountered, the result is None.
    """
    return _calculate_stat(_cv, values)
# End coefficient_of_variation function


def first_quartile(values: list) -> float | None:
    """
    Calculate First Quartile, ignoring Null values and non-finite values.
    If a non-number is encountered, the result is None.
    """
    return _calculate_stat(_first_quartile, values)
# End first_quartile function


def third_quartile(values: list) -> float | None:
    """
    Calculate Third Quartile, ignoring Null values and non-finite values.
    If a non-number is encountered, the result is None.
    """
    return _calculate_stat(_third_quartile, values)
# End third_quartile function


def interquartile_range(values: list) -> float | None:
    """
    Calculate Interquartile Range, ignoring Null values and non-finite values.
    If a non-number is encountered, the result is None.
    """
    return _calculate_stat(_interquartile_range, values)
# End interquartile_range function


def count_outlier(values: list) -> int | None:
    """
    Calculate Outlier Count, ignoring Null values and non-finite values.
    If a non-number is encountered, the result is None.
    """
    # noinspection PyTypeChecker
    return _calculate_stat(_count_outlier, values)
# End count_outlier function


def least_common(values: list) -> float | None:
    """
    Calculate Least Common, ignoring Null values and non-finite values.
    If a non-number is encountered, the result is None.
    """
    return _calculate_stat(_least, values)
# End least_common function


def most_common(values: list) -> float | None:
    """
    Calculate Most Common, ignoring Null values and non-finite values.
    If a non-number is encountered, the result is None.
    """
    return _calculate_stat(_most, values)
# End most_common function


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


def _calculate_stat(func: Callable, values: list | float | None) -> float | None:
    """
    Calculate Statistic, ignoring Null values and non-finite values.
    """
    # noinspection PyTypeChecker
    if not (values := _filter_none(values)):
        return None
    try:
        # noinspection PyTypeChecker
        if not (values := [v for v in values if isfinite(v)]):
            return None
    except TypeError:
        return None
    try:
        return func(values)
    except (IndexError, ZeroDivisionError, ValueError, StatisticsError):
        return None
# End _calculate_stat function


def _filter_none(values: list) -> list:
    """
    Filter None's out of a list
    """
    if values is None:
        return []
    if not isinstance(values, list):
        values = [values]
    return [v for v in values if v is not None]
# End _filter_none function


class AbstractAggregate(metaclass=ABCMeta):
    """
    Abstract Aggregate
    """
    def __init__(self) -> None:
        """
        Initialize the AbstractAggregate class
        """
        super().__init__()
        self._values: list = []
    # End init built-in

    def step(self, value: Any) -> None:
        """
        Step
        """
        self._values.append(value)
    # End step method

    @abstractmethod
    def finalize(self) -> Any:
        """
        Finalize
        """
        pass
    # End finalize method
# End AbstractAggregate class


class _ModeAggregate(AbstractAggregate):
    """
    Mode Aggregate for SQLite
    """
    def finalize(self) -> float | None:
        """
        Finalize
        """
        return mode(self._values)
    # End finalize method
# End _ModeAggregate class


class _StandardDeviationAggregate(AbstractAggregate):
    """
    Standard Deviation Aggregate for SQLite
    """
    def finalize(self) -> float | None:
        """
        Finalize
        """
        return stdev(self._values)
    # End finalize method
# End _StandardDeviationAggregate class


class _VarianceAggregate(AbstractAggregate):
    """
    Variance Aggregate for SQLite
    """
    def finalize(self) -> float | None:
        """
        Finalize
        """
        return var(self._values)
    # End finalize method
# End _VarianceAggregate class


class _MedianAggregate(AbstractAggregate):
    """
    Median Aggregate for SQLite
    """
    def finalize(self) -> float | None:
        """
        Finalize
        """
        return median(self._values)
    # End finalize method
# End _MedianAggregate class


class _FirstAggregate(AbstractAggregate):
    """
    First Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        return first(self._values)
    # End finalize method
# End _FirstAggregate class


class _LastAggregate(AbstractAggregate):
    """
    Last Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        return last(self._values)
    # End finalize method
# End _LastAggregate class


class _KurtAggregate(AbstractAggregate):
    """
    Kurtosis Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        return kurtosis(self._values)
    # End finalize method
# End _KurtAggregate class


class _SkewAggregate(AbstractAggregate):
    """
    Skewness Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        return skewness(self._values)
    # End finalize method
# End _SkewAggregate class


class _VariationAggregate(AbstractAggregate):
    """
    Coefficient of Variation Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        return coefficient_of_variation(self._values)
    # End finalize method
# End _VariationAggregate class


class _FirstQuartileNumericAggregate(AbstractAggregate):
    """
    First Quartile Numeric Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        return first_quartile(self._values)
    # End finalize method
# End _FirstQuartileNumericAggregate class


class _ThirdQuartileNumericAggregate(AbstractAggregate):
    """
    Third Quartile Numeric Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        return third_quartile(self._values)
    # End finalize method
# End _ThirdQuartileNumericAggregate class


class _FirstQuartileDateAggregate(AbstractAggregate):
    """
    First Quartile Date Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        if (result := first_quartile(self._values)) is None:
            return result
        return str(datetime.fromtimestamp(result, tz=timezone.utc))
    # End finalize method
# End _FirstQuartileDateAggregate class


class _ThirdQuartileDateAggregate(AbstractAggregate):
    """
    Third Quartile Date Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        if (result := third_quartile(self._values)) is None:
            return result
        return str(datetime.fromtimestamp(result, tz=timezone.utc))
    # End finalize method
# End _ThirdQuartileDateAggregate class


class _InterquartileRangeAggregate(AbstractAggregate):
    """
    Interquartile Range Numeric Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        return interquartile_range(self._values)
    # End finalize method
# End _InterquartileRangeAggregate class


class _CountOutlierAggregate(AbstractAggregate):
    """
    Count Outlier Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        return count_outlier(self._values)
    # End finalize method
# End _CountOutlierAggregate class


class _LeastCommonAggregate(AbstractAggregate):
    """
    Least Common Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        return least_common(self._values)
    # End finalize method
# End _LeastCommonAggregate class


class _MostCommonAggregate(AbstractAggregate):
    """
    Most Common Aggregate for SQLite
    """
    def finalize(self) -> Any:
        """
        Finalize
        """
        return most_common(self._values)
    # End finalize method
# End _MostCommonAggregate class


STATS_FUNCS: dict[str, Callable] = {
    'mode': _ModeAggregate,
    'stdev': _StandardDeviationAggregate,
    'var': _VarianceAggregate,
    'median': _MedianAggregate,
    'first': _FirstAggregate,
    'last': _LastAggregate,
    'kurtosis': _KurtAggregate,
    'skewness': _SkewAggregate,
    'variation': _VariationAggregate,
    'first_quartile': _FirstQuartileNumericAggregate,
    'third_quartile': _ThirdQuartileNumericAggregate,
    'first_quartile_date': _FirstQuartileDateAggregate,
    'third_quartile_date': _ThirdQuartileDateAggregate,
    'interquartile_range': _InterquartileRangeAggregate,
    'count_outlier': _CountOutlierAggregate,
    'least_common': _LeastCommonAggregate,
    'most_common': _MostCommonAggregate,
}


class AbstractStatisticField(metaclass=ABCMeta):
    """
    Abstract Statistic Field
    """
    def __init__(self, field: Field | str, stat: Statistic) -> None:
        """
        Initialize the AbstractStatisticField class
        """
        super().__init__()
        self._field: Field | str = field
        self._stat: Statistic = stat
    # End init built-in

    def __eq__(self, other: Self) -> bool:
        """
        Equals Override
        """
        if not isinstance(other, self.__class__):  # pragma: no cover
            return NotImplemented
        return self.field == other.field and self.statistic == other.statistic
    # End eq built-in

    def __hash__(self) -> int:
        """
        Hash Implementation
        """
        return hash((self.field, self.statistic))
    # End hash built-in

    def __repr__(self) -> str:
        """
        Representation Override
        """
        return self.aggregate
    # End repr built-in

    @property
    def field(self) -> Field | str:
        """
        Field
        """
        return self._field

    @field.setter
    def field(self, value: Field) -> None:
        if not isinstance(value, Field):
            return
        self._field = value
    # End field property

    @property
    def output_field(self) -> Field:
        """
        Output Field
        """
        # noinspection PyUnresolvedReferences
        return Field(name=self.output_name, data_type=self.data_type,
                     size=self.field.size)
    # End output_field property

    @property
    def statistic(self) -> Statistic:
        """
        Statistic
        """
        return self._stat
    # End statistic property

    def _is_field(self) -> None:
        """
        Is Field
        """
        if not isinstance(self.field, Field):
            raise TypeError('Expected field to be a Field object')
    # End _is_field method

    def _get_data_type(self) -> str:
        """
        Get Data Type
        """
        # noinspection PyTypeChecker
        return get_data_type(self.field)
    # End _get_data_type method

    def validate(self) -> None:
        """
        Validate
        """
        self._is_field()
    # End validate method

    @property
    @abstractmethod
    def aggregate(self) -> str:  # pragma: no cover
        """
        Function Stub
        """
        pass
    # End aggregate property

    @property
    def prefix(self) -> str:
        """
        Prefix
        """
        return f'{str(self.statistic).upper()}'
    # End prefix property

    @property
    def output_name(self) -> str:
        """
        Output Name
        """
        # noinspection PyUnresolvedReferences
        return f'{self.prefix}{UNDERSCORE}{self.field.name}'
    # End output_name property

    @property
    def data_type(self) -> str:
        """
        Data Type
        """
        return self._get_data_type()
    # End data_type property
# End AbstractStatisticField class


class _BaseStatisticField(AbstractStatisticField):
    """
    Base Statistic Field
    """
    @property
    def aggregate(self) -> str:
        """
        Function Stub
        """
        # noinspection PyUnresolvedReferences
        return f'{self.prefix}({self.field.escaped_name})'
    # End aggregate property
# End _BaseStatisticField class


class _NumericStatisticField(_BaseStatisticField):
    """
    Numeric Statistic Field
    """
    def validate(self) -> None:
        """
        Validate
        """
        super().validate()
        if (data_type := self._get_data_type()) in NUMBERS:
            return
        # noinspection PyUnresolvedReferences
        raise ValueError(
            f'Expected {self.field.name} field to be numeric, got {data_type}')
    # End validate method
# End _NumericStatisticField class


class _NumericDateStatisticField(_BaseStatisticField):
    """
    Numeric or Date Statistic Field
    """
    @property
    def _is_date(self) -> bool:
        """
        Is Date
        """
        return self._get_data_type() in DATES
    # End _is_date property

    def validate(self) -> None:
        """
        Validate
        """
        super().validate()
        data_type = self._get_data_type()
        if data_type in NUMBERS or self._is_date:
            return
        # noinspection PyUnresolvedReferences
        raise ValueError(
            f'Expected {self.field.name} field to be numeric or date, '
            f'got {data_type}')
    # End validate method
# End _NumericDateStatisticField class


class _FunctionStatisticField(AbstractStatisticField):
    """
    Function Statistic Field
    """
    @property
    def aggregate(self) -> str:
        """
        Function Stub
        """
        name = f'{SPYOPS}{UNDERSCORE}{self.prefix.casefold()}'
        # noinspection PyUnresolvedReferences
        return f'{name}({self.field.escaped_name})'
    # End aggregate property
# End _FunctionStatisticField class


class _FunctionStatisticNumericDateField(_NumericDateStatisticField):
    """
    Function Statistic Field for Numeric or Date Fields
    """
    @property
    def aggregate(self) -> str:
        """
        Function Stub
        """
        # noinspection PyUnresolvedReferences
        escaped_name = self.field.escaped_name
        name = f'{SPYOPS}{UNDERSCORE}{self.prefix.casefold()}'
        if not self._is_date:
            return f'{name}({escaped_name})'
        # noinspection PyUnresolvedReferences
        return f"{name}_date(unixepoch({escaped_name}, 'subsecond'))"
    # End aggregate property
# End _FunctionStatisticNumericDateField class


class _FunctionNumericStatisticField(_NumericStatisticField):
    """
    Function-based Numeric Statistic Field
    """
    @property
    def aggregate(self) -> str:
        """
        Function Stub
        """
        name = f'{SPYOPS}{UNDERSCORE}{self.prefix.casefold()}'
        # noinspection PyUnresolvedReferences
        return f'{name}({self.field.escaped_name})'
    # End aggregate property
# End _FunctionNumericStatisticField class


class Average(_NumericDateStatisticField):
    """
    Average Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Average class
        """
        super().__init__(field, stat=Statistic.AVERAGE)
    # End init built-in

    @property
    def prefix(self) -> str:
        """
        Prefix
        """
        return 'AVG'
    # End prefix property

    @property
    def aggregate(self) -> str:
        """
        Aggregate
        """
        if not self._is_date:
            return super().aggregate
        # noinspection PyUnresolvedReferences
        return (f"datetime({self.prefix}(unixepoch({self.field.escaped_name}, "
                f"'subsecond')), 'unixepoch')")
    # End aggregate property
# End Average class


class Median(_FunctionStatisticNumericDateField):
    """
    Median Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Median class
        """
        super().__init__(field, stat=Statistic.MEDIAN)
    # End init built-in

    @property
    def aggregate(self) -> str:
        """
        Aggregate
        """
        if not self._is_date:
            return super().aggregate
        # noinspection PyUnresolvedReferences
        escaped_name = self.field.escaped_name
        name = f'{SPYOPS}{UNDERSCORE}{self.prefix.casefold()}'
        agg = f"{name}(unixepoch({escaped_name}, 'subsecond'))"
        return f"datetime({agg}, 'unixepoch')"
    # End aggregate property
# End Median class


class Minimum(_BaseStatisticField):
    """
    Minimum Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Minimum class
        """
        super().__init__(field, stat=Statistic.MINIMUM)
    # End init built-in

    @property
    def prefix(self) -> str:
        """
        Prefix
        """
        return 'MIN'
    # End prefix property
# End Minimum class


class Maximum(_BaseStatisticField):
    """
    Maximum Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Maximum class
        """
        super().__init__(field, stat=Statistic.MAXIMUM)
    # End init built-in

    @property
    def prefix(self) -> str:
        """
        Prefix
        """
        return 'MAX'
    # End prefix property
# End Maximum class


class Range(_NumericDateStatisticField):
    """
    Range Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Range class
        """
        super().__init__(field, stat=Statistic.RANGE)
    # End init built-in

    @property
    def aggregate(self) -> str:
        """
        Function Stub
        """
        # noinspection PyUnresolvedReferences
        name = self.field.escaped_name
        if not self._is_date:
            return f'(MAX({name}) - MIN({name}))'
        return (f"(MAX(unixepoch({name}, 'subsecond')) - "
                f" MIN(unixepoch({name}, 'subsecond')))")
    # End aggregate property
# End Range class


class StandardDeviation(_FunctionNumericStatisticField):
    """
    Standard Deviation Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Standard Deviation class
        """
        super().__init__(field, stat=Statistic.STANDARD_DEVIATION)
    # End init built-in

    @property
    def prefix(self) -> str:
        """
        Prefix
        """
        return 'STDEV'
    # End prefix property
# End StandardDeviation class


class Variance(_FunctionNumericStatisticField):
    """
    Variance Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Variance class
        """
        super().__init__(field, stat=Statistic.VARIANCE)
    # End init built-in

    @property
    def prefix(self) -> str:
        """
        Prefix
        """
        return 'VAR'
    # End prefix property
# End StandardDeviation class


class Summation(_NumericStatisticField):
    """
    Summation Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Summation class
        """
        super().__init__(field, stat=Statistic.SUMMATION)
    # End init built-in

    @property
    def prefix(self) -> str:
        """
        Prefix
        """
        return 'SUM'
    # End prefix property
# End Summation class


class Count(_BaseStatisticField):
    """
    Count Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Count class
        """
        super().__init__(field, stat=Statistic.COUNT)
    # End init built-in
# End Count class


class CountNull(_BaseStatisticField):
    """
    Count Null Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the CountNull class
        """
        super().__init__(field, stat=Statistic.COUNT_NULL)
    # End init built-in

    @property
    def aggregate(self) -> str:
        """
        Function Stub
        """
        # noinspection PyUnresolvedReferences
        name = self.field.escaped_name
        return f'SUM(CASE WHEN {name} IS NULL THEN 1 ELSE 0 END)'
    # End aggregate property
# End CountNull class


class CountNonNull(_BaseStatisticField):
    """
    Count Non-Null Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the CountNonNull class
        """
        super().__init__(field, stat=Statistic.COUNT_NON_NULL)
    # End init built-in

    @property
    def aggregate(self) -> str:
        """
        Function Stub
        """
        # noinspection PyUnresolvedReferences
        name = self.field.escaped_name
        return f'SUM(CASE WHEN {name} IS NOT NULL THEN 1 ELSE 0 END)'
    # End aggregate property
# End CountNonNull class


class Frequency(Count):
    """
    Frequency Statistics Field
    """
    def __init__(self) -> None:
        """
        Initialize the Count class
        """
        super().__init__(ROWID)
        self._output_name: str = FREQUENCY.name
    # End init built-in

    @property
    def aggregate(self) -> str:
        """
        Function Stub
        """
        return f'{self.prefix}({ROWID})'
    # End aggregate property

    @property
    def output_name(self) -> str:
        """
        Output Name
        """
        return self._output_name

    @output_name.setter
    def output_name(self, value: str) -> None:
        self._output_name = value
    # End output_name property

    @property
    def output_field(self) -> Field:
        """
        Output Field
        """
        return Field(self.output_name, data_type=FREQUENCY.data_type)
    # End output_field property

    @property
    def data_type(self) -> str:
        """
        Data Type
        """
        return FREQUENCY.data_type
    # End data_type property
# End Frequency class


class Unique(AbstractStatisticField):
    """
    Unique Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Unique class
        """
        super().__init__(field, stat=Statistic.UNIQUE)
    # End init built-in

    @property
    def aggregate(self) -> str:
        """
        Function Stub
        """
        # noinspection PyUnresolvedReferences
        return f'COUNT(DISTINCT {self.field.escaped_name})'
    # End aggregate property

    @property
    def prefix(self) -> str:
        """
        Prefix
        """
        return 'UNIQUE'
    # End prefix property
# End Unique class


class Mode(_FunctionStatisticField):
    """
    Mode Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Mode class
        """
        super().__init__(field, stat=Statistic.MODE)
    # End init built-in
# End Mode class


class First(_FunctionStatisticField):
    """
    First Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the First class
        """
        super().__init__(field, stat=Statistic.FIRST)
    # End init built-in
# End First class


class Last(_FunctionStatisticField):
    """
    Last Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Last class
        """
        super().__init__(field, stat=Statistic.LAST)
    # End init built-in
# End Last class


class Kurtosis(_FunctionNumericStatisticField):
    """
    Kurtosis Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Kurtosis class
        """
        super().__init__(field, stat=Statistic.KURTOSIS)
    # End init built-in
# End Kurtosis class


class Skewness(_FunctionNumericStatisticField):
    """
    Skewness Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Skewness class
        """
        super().__init__(field, stat=Statistic.SKEWNESS)
    # End init built-in
# End Skewness class


class Variation(_FunctionNumericStatisticField):
    """
    Variation Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Variation class
        """
        super().__init__(field, stat=Statistic.VARIATION)
    # End init built-in
# End Variation class


class FirstQuartile(_FunctionStatisticNumericDateField):
    """
    First Quartile Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the FirstQuartile class
        """
        super().__init__(field, stat=Statistic.FIRST_QUARTILE)
    # End init built-in
# End FirstQuartile class


class ThirdQuartile(_FunctionStatisticNumericDateField):
    """
    Third Quartile Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the ThirdQuartile class
        """
        super().__init__(field, stat=Statistic.THIRD_QUARTILE)
    # End init built-in
# End ThirdQuartile class


class InterquartileRange(_FunctionNumericStatisticField):
    """
    Interquartile Range Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the InterquartileRange class
        """
        super().__init__(field, stat=Statistic.INTERQUARTILE_RANGE)
    # End init built-in
# End InterquartileRange class


class CountOutlier(_FunctionNumericStatisticField):
    """
    Count Outlier Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the CountOutlier class
        """
        super().__init__(field, stat=Statistic.COUNT_OUTLIER)
    # End init built-in
# End CountOutlier class


class LeastCommon(_FunctionStatisticField):
    """
    Least Common Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the LeastCommon class
        """
        super().__init__(field, stat=Statistic.LEAST_COMMON)
    # End init built-in
# End LeastCommon class


class MostCommon(_FunctionStatisticField):
    """
    Most Common Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the MostCommon class
        """
        super().__init__(field, stat=Statistic.MOST_COMMON)
    # End init built-in
# End MostCommon class


class Concatenate(AbstractStatisticField):
    """
    Concatenate Statistics Field
    """
    def __init__(self, field: Field | str, delimiter: str = COMMA) -> None:
        """
        Initialize the Concatenate class
        """
        super().__init__(field, stat=Statistic.CONCATENATE)
        self._delimiter: str = str(delimiter)
    # End init built-in

    @property
    def aggregate(self) -> str:
        """
        Function Stub
        """
        # noinspection PyUnresolvedReferences
        return f"group_concat({self.field.escaped_name}, '{self._delimiter}')"
    # End aggregate property

    @property
    def prefix(self) -> str:
        """
        Prefix
        """
        return 'CONCAT'
    # End prefix property

    @property
    def data_type(self) -> str:
        """
        Data Type
        """
        return FieldType.text
    # End data_type property

    @property
    def output_field(self) -> Field:
        """
        Output Field
        """
        return Field(name=self.output_name, data_type=self.data_type)
    # End output_field property
# End Concatenate class


# aliases
Avg = Average
CV = Variation
CoefficientOfVariation = Variation
Concat = Concatenate
IQR = InterquartileRange
Kurt = Kurtosis
Least = LeastCommon
Max = Maximum
Mean = Average
Min = Minimum
Most = MostCommon
Outliers = CountOutlier
Q1 = FirstQuartile
Q3 = ThirdQuartile
Skew = Skewness
StdDev = StandardDeviation
Sum = Summation
Var = Variance


STAT_NAME_ALIASES: dict[Statistic, tuple[str, str]] = {
    # NOTE numeric and date
    Statistic.AVERAGE: ('MEAN', 'Mean'),
    Statistic.MEDIAN: ('MEDIAN', 'Median'),
    Statistic.MINIMUM: ('MINIMUM', 'Minimum'),
    Statistic.MAXIMUM: ('MAXIMUM', 'Maximum'),
    Statistic.RANGE: ('RANGE_', 'Range'),

    Statistic.COUNT: ('COUNT_', 'Count'),
    Statistic.COUNT_NULL: ('COUNT_NULL', 'Null Count'),
    Statistic.COUNT_NON_NULL: ('COUNT_NON_NULL', 'Non Null Count'),
    Statistic.UNIQUE: ('UNIQUE_', 'Unique Count'),

    Statistic.FIRST_QUARTILE: ('FIRST_QUARTILE', 'First Quartile'),
    Statistic.THIRD_QUARTILE: ('THIRD_QUARTILE', 'Third Quartile'),

    # NOTE numeric only
    Statistic.SUMMATION: ('SUM_', 'Sum'),
    Statistic.STANDARD_DEVIATION: ('STD_DEV', 'Standard Deviation'),
    Statistic.VARIANCE: ('VARIANCE', 'Variance'),

    Statistic.SKEWNESS: ('SKEWNESS', 'Skewness'),
    Statistic.KURTOSIS: ('KURTOSIS', 'Kurtosis'),
    Statistic.VARIATION: ('VARIATION', 'Coefficient of Variation'),
    Statistic.INTERQUARTILE_RANGE: (
        'INTERQUARTILE_RANGE', 'Interquartile Range'),
    Statistic.COUNT_OUTLIER: ('COUNT_OUTLIER', 'Outlier Count'),

    # NOTE shared
    Statistic.MODE: ('MODE', 'Mode'),
    Statistic.LEAST_COMMON: ('LEAST_COMMON', 'Least Common'),
}

COUNT_STATS: tuple[tuple[Type, str], ...] = (
    (Count, FieldType.integer),
    (CountNull, FieldType.integer),
    (CountNonNull, FieldType.integer),
    (Unique, FieldType.integer),
)

NUMERIC_STATS: tuple[tuple[Type, str], ...] = (
    *COUNT_STATS,
    (Mean, FieldType.real),
    (StandardDeviation, FieldType.real),
    (Median, FieldType.real),
    (Mode, FieldType.real),
    (LeastCommon, FieldType.real),
    (Minimum, FieldType.real),
    (Maximum, FieldType.real),
    (Range, FieldType.real),
    (Summation, FieldType.real),
    (FirstQuartile, FieldType.real),
    (ThirdQuartile, FieldType.real),
    (InterquartileRange, FieldType.real),
    (CountOutlier, FieldType.integer),
    (Variation, FieldType.real),
    (Skewness, FieldType.real),
    (Kurtosis, FieldType.real),
)
DATE_STATS: tuple[tuple[Type, str], ...] = (
    *COUNT_STATS,
    (Mean, FieldType.timestamp),
    (Median, FieldType.timestamp),
    (Mode, FieldType.timestamp),
    (LeastCommon, FieldType.timestamp),
    (Minimum, FieldType.timestamp),
    (Maximum, FieldType.timestamp),
    (Range, FieldType.real),
    (FirstQuartile, FieldType.timestamp),
    (ThirdQuartile, FieldType.timestamp),
)
TEXT_STATS: tuple[tuple[Type, str], ...] = (
    *COUNT_STATS,
    (Mode, FieldType.text),
    (LeastCommon, FieldType.text),
    (Minimum, FieldType.text),
    (Maximum, FieldType.text),
)


if __name__ == '__main__':  # pragma: no cover
    pass
