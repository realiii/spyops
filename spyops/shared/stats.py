# -*- coding: utf-8 -*-
"""
Statistics Functions for use within SQLite
"""


from abc import ABCMeta, abstractmethod
from math import isfinite
from statistics import (
    StatisticsError, median as _median, mode as _mode,
    stdev as _standard_deviation, variance)
from typing import Any, Callable, Self

from fudgeo import Field
from fudgeo.enumeration import FieldType

from spyops.shared.constant import COMMA, SPYOPS, UNDERSCORE
from spyops.shared.enumeration import Statistic
from spyops.shared.field import ALIAS_TYPE_LUT, NUMBERS


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


def median(values: list) -> float | None:
    """
    Calculate Median, ignoring Null values and non-finite values.
    If a non-number is encountered, the result is None.
    """
    return _calculate_stat(_median, values)
# End median function


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


STATS_FUNCS: dict[str, Callable] = {
    'mode': _ModeAggregate,
    'stdev': _StandardDeviationAggregate,
    'var': _VarianceAggregate,
    'median': _MedianAggregate,
    'first': _FirstAggregate,
    'last': _LastAggregate,
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
        data_type = self.field.data_type.casefold()
        return next((type_ for aliases, type_ in ALIAS_TYPE_LUT.items()
                     if data_type.startswith(aliases)), data_type)
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
        return f'{str(self._stat).upper()}'
    # End prefix property

    @property
    def output_name(self) -> str:
        """
        Output Name
        """
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


class _NumericStatisticField(AbstractStatisticField):
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
        raise ValueError(
            f'Expected {self.field.name} field to be numeric, got {data_type}')
    # End validate method

    @property
    def aggregate(self) -> str:
        """
        Function Stub
        """
        return f'{self.prefix}({self.field.escaped_name})'
    # End aggregate property
# End _NumericStatisticField class


class Average(_NumericStatisticField):
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
# End Average class


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
        return f'{name}({self.field.escaped_name})'
    # End aggregate property
# End _FunctionNumericStatisticField class


class Median(_FunctionNumericStatisticField):
    """
    Median Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Median class
        """
        super().__init__(field, stat=Statistic.MEDIAN)
    # End init built-in
# End Median class


class Minimum(_NumericStatisticField):
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


class Maximum(_NumericStatisticField):
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


class Range(_NumericStatisticField):
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
        name = self.field.escaped_name
        return f'(MAX({name}) - MIN({name}))'
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


class Count(AbstractStatisticField):
    """
    Count Statistics Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the Count class
        """
        super().__init__(field, stat=Statistic.COUNT)
    # End init built-in

    @property
    def aggregate(self) -> str:
        """
        Function Stub
        """
        return f'{self.prefix}({self.field.escaped_name})'
    # End aggregate property

    @property
    def prefix(self) -> str:
        """
        Prefix
        """
        return 'COUNT'
    # End prefix property
# End Count class


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
        return f'{name}({self.field.escaped_name})'
    # End aggregate property
# End _FunctionStatisticField class


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
Mean = Average
Min = Minimum
Max = Maximum
StdDev = StandardDeviation
Var = Variance
Sum = Summation
Concat = Concatenate


if __name__ == '__main__':  # pragma: no cover
    pass
