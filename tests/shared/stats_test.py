# -*- coding: utf-8 -*-
"""
Test Statistics
"""


from fudgeo import Field
from fudgeo.enumeration import FieldType
from pytest import mark, approx

from spyops.shared.enumeration import Statistic
from spyops.shared.stats import (
    Average, Avg, Concat, Concatenate, Count, First, Last, Max, Maximum, Mean,
    Median, Min, Minimum, Mode, Range, StandardDeviation, StdDev, Sum,
    Summation, Unique, Var, Variance, first, last, median, mode, stdev, var)


pytestmark = [mark.statistics]


class TestSQLiteStatisticsFunctions:
    """
    Test SQLite Statistics Functions
    """
    @mark.parametrize('values, expected', [
        ([], None),
        ([[]], None),
        ([1, 2, 3], 1),
        ([1, 2, 2, 3], 2),
        ([1, 2, 2, None, 3], 2),
        (['a', 'b', 'c', None, 'c'], 'c'),
    ])
    def test_mode(self, values, expected):
        """
        Test mode
        """
        assert mode(values) == expected
    # End test_mode method

    @mark.parametrize('values, expected', [
        ([], None),
        ([[]], None),
        ([1, 2, 3], 1.),
        ([1, 2, 3, 4, 5], 1.5811),
        ([1, 2, None, 3], 1.),
        (['a', 'b', 'c', None, 'c'], None),
    ])
    def test_stdev(self, values, expected):
        """
        Test standard deviation
        """
        assert approx(stdev(values), abs=0.001) == expected
    # End test_stdev method

    @mark.parametrize('values, expected', [
        ([], None),
        ([[]], None),
        ([1, 2, 3], 1.),
        ([1, 2, 3, 4, 5], 2.5),
        ([1, 2, None, 3], 1.),
        (['a', 'b', 'c', None, 'c'], None),
    ])
    def test_var(self, values, expected):
        """
        Test variance
        """
        assert approx(var(values), abs=0.001) == expected
    # End test_var method

    @mark.parametrize('values, expected', [
        ([], None),
        ([[]], None),
        ([1, 2, 3], 2),
        ([1, 2, 3, 4, 5], 3),
        ([1, 2, None, 3], 2),
        (['a', 'b', 'c', None, 'c'], None),
    ])
    def test_median(self, values, expected):
        """
        Test median
        """
        assert approx(median(values), abs=0.001) == expected
    # End test_median method

    @mark.parametrize('values, expected', [
        ([], None),
        ([1, 2, 3], 1),
        ([1, 2, 3, 4, 5], 1),
        ([1, 2, None, 3], 1),
        (['a', 'b', 'c', None, 'c'], 'a'),
    ])
    def test_first(self, values, expected):
        """
        Test first value
        """
        assert first(values) == expected
    # End test_first method

    @mark.parametrize('values, expected', [
        ([], None),
        ([1, 2, 3], 3),
        ([1, 2, 3, 4, 5], 5),
        ([1, 2, None, 3], 3),
        (['a', 'b', 'c', None, 'c'], 'c'),
    ])
    def test_last(self, values, expected):
        """
        Test last value
        """
        assert last(values) == expected
    # End test_last method
# End TestSQLiteStatisticsFunctions class


class TestStatisticField:
    """
    Test Statistic Fields
    """
    @mark.parametrize('cls, stat, stub, prefix', [
        (Average, Statistic.AVERAGE, 'AVG({})', 'AVG'),
        (Avg, Statistic.AVERAGE, 'AVG({})', 'AVG'),
        (Mean, Statistic.AVERAGE, 'AVG({})', 'AVG'),
        (Median, Statistic.MEDIAN, 'spyops_median({})', 'MEDIAN'),
        (Minimum, Statistic.MINIMUM, 'MIN({})', 'MIN'),
        (Min, Statistic.MINIMUM, 'MIN({})', 'MIN'),
        (Maximum, Statistic.MAXIMUM, 'MAX({})', 'MAX'),
        (Max, Statistic.MAXIMUM, 'MAX({})', 'MAX'),
        (Range, Statistic.RANGE, '(MAX({0}) - MIN({0}))', 'RANGE'),
        (StandardDeviation, Statistic.STANDARD_DEVIATION, 'spyops_stdev({})', 'STDEV'),
        (StdDev, Statistic.STANDARD_DEVIATION, 'spyops_stdev({})', 'STDEV'),
        (Variance, Statistic.VARIANCE, 'spyops_var({})', 'VAR'),
        (Var, Statistic.VARIANCE, 'spyops_var({})', 'VAR'),
        (Summation, Statistic.SUMMATION, 'SUM({})', 'SUM'),
        (Sum, Statistic.SUMMATION, 'SUM({})', 'SUM'),
        (Count, Statistic.COUNT, 'COUNT({})', 'COUNT'),
        (Unique, Statistic.UNIQUE, 'COUNT(DISTINCT {})', 'UNIQUE'),
        (Mode, Statistic.MODE, 'spyops_mode({})', 'MODE'),
        (First, Statistic.FIRST, 'spyops_first({})', 'FIRST'),
        (Last, Statistic.LAST, 'spyops_last({})', 'LAST'),
    ])
    def test_configuration(self, cls, stat, stub, prefix):
        """
        Test configuration / setup
        """
        field = Field(name='asdf', data_type='bigint')
        obj = cls(field)
        obj.validate()
        assert obj.field == field
        obj.field = 'lmno'
        obj.field = field
        assert obj.field == field
        assert obj.statistic == stat
        assert obj.aggregate == stub.format(field.escaped_name)
        assert obj.prefix == prefix
        assert obj.output_name == f'{prefix}_asdf'
        assert obj.data_type == FieldType.integer
    # End test_configuration method

    @mark.parametrize('cls', [
        Concatenate,
        Concat
    ])
    def test_concatenate(self, cls):
        """
        Test Concatenate
        """
        field = Field(name='asdf', data_type='bigint')
        obj = cls(field)
        obj.validate()
        assert obj.field == field
        obj.field = 'lmno'
        obj.field = field
        assert obj.field == field
        assert obj.statistic == Statistic.CONCATENATE
        assert obj.aggregate == "group_concat(asdf, ',')"
        assert obj.prefix == 'CONCAT'
        assert obj.output_name == 'CONCAT_asdf'
        assert obj.data_type == FieldType.text
    # End test_concatenate method

# End TestStatisticField class


if __name__ == '__main__':  # pragma: no cover
    pass
