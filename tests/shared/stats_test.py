# -*- coding: utf-8 -*-
"""
Test Statistics
"""


from fudgeo import Field
from fudgeo.enumeration import FieldType
from pytest import mark, approx, raises

from spyops.shared.enumeration import Statistic
from spyops.shared.stats import (
    Average, Avg, CV, CoefficientOfVariation, Concat, Concatenate, Count,
    CountNonNull, CountNull, CountOutlier, First, FirstQuartile, IQR,
    InterquartileRange, Kurt, Kurtosis, Last, Least, LeastCommon, Max, Maximum,
    Mean, Median, Min, Minimum, Mode, Most, MostCommon, Outliers, Q1, Q3, Range,
    Skew, Skewness, StandardDeviation, StdDev, Sum, Summation, ThirdQuartile,
    Unique, Var, Variance, Variation, first, first_quartile, last, median, mode,
    stdev, third_quartile, var, kurtosis, skewness, least_common, most_common,
    interquartile_range, count_outlier, coefficient_of_variation)


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
    
    def test_kurtosis(self):
        """
        Test kurtosis
        """
        assert approx(kurtosis(list(range(1, 100))), abs=0.001) == -1.2364
    # End test_kurtosis method
    
    def test_skewness(self):
        """
        Test Skewness
        """
        assert skewness(list(range(1, 100))) == 0
    # End test_skewness method
    
    def test_interquartile_range(self):
        """
        Test Interquartile Range
        """
        assert interquartile_range(list(range(1, 100))) == 50
    # End test_interquartile_range method

    def test_first_quartile(self):
        """
        Test First Quartile
        """
        assert first_quartile(list(range(1, 100))) == 25
    # End test_first_quartile method

    def test_third_quartile(self):
        """
        Test Third Quartile
        """
        assert third_quartile(list(range(1, 100))) == 75
    # End test_third_quartile method
    
    def test_least_common(self):
        """
        Test least common
        """
        assert least_common([1, 2, 2, 3, 3, 3]) == 1
    # End test_least_common method

    def test_most_common(self):
        """
        Test most common
        """
        assert most_common([1, 2, 2, 3, 3, 3]) == 3
    # End test_most_common method

    def test_coefficient_of_variation(self):
        """
        Test coefficient of variation
        """
        assert approx(coefficient_of_variation(list(range(1, 100))), abs=0.001) == 57.4456
    # End test_coefficient_of_variation method

    def test_outlier_count(self):
        """
        Test outlier count
        """
        values = [1000, 1000, -1000, -1000, *range(1, 100)]
        assert count_outlier(values) == 4
    # End test_outlier_count method
# End TestSQLiteStatisticsFunctions class


class TestStatisticField:
    """
    Test Statistic Fields
    """
    @mark.parametrize('cls, stat, stub, prefix', [
        (Average, Statistic.AVERAGE, 'AVG({})', 'AVG'),
        (Avg, Statistic.AVERAGE, 'AVG({})', 'AVG'),
        (CV, Statistic.VARIATION, 'spyops_variation({})', 'VARIATION'),
        (CoefficientOfVariation, Statistic.VARIATION, 'spyops_variation({})', 'VARIATION'),
        (Count, Statistic.COUNT, 'COUNT({})', 'COUNT'),
        (CountNonNull, Statistic.COUNT_NON_NULL, 'SUM(CASE WHEN {} IS NOT NULL THEN 1 ELSE 0 END)', 'COUNT_NON_NULL'),
        (CountNull, Statistic.COUNT_NULL, 'SUM(CASE WHEN {} IS NULL THEN 1 ELSE 0 END)', 'COUNT_NULL'),
        (CountOutlier, Statistic.COUNT_OUTLIER, 'spyops_count_outlier({})', 'COUNT_OUTLIER'),
        (First, Statistic.FIRST, 'spyops_first({})', 'FIRST'),
        (FirstQuartile, Statistic.FIRST_QUARTILE, 'spyops_first_quartile({})', 'FIRST_QUARTILE'),
        (IQR, Statistic.INTERQUARTILE_RANGE, 'spyops_interquartile_range({})', 'INTERQUARTILE_RANGE'),
        (InterquartileRange, Statistic.INTERQUARTILE_RANGE, 'spyops_interquartile_range({})', 'INTERQUARTILE_RANGE'),
        (Kurt, Statistic.KURTOSIS, 'spyops_kurtosis({})', 'KURTOSIS'),
        (Kurtosis, Statistic.KURTOSIS, 'spyops_kurtosis({})', 'KURTOSIS'),
        (Last, Statistic.LAST, 'spyops_last({})', 'LAST'),
        (Least, Statistic.LEAST_COMMON, 'spyops_least_common({})', 'LEAST_COMMON'),
        (LeastCommon, Statistic.LEAST_COMMON, 'spyops_least_common({})', 'LEAST_COMMON'),
        (Max, Statistic.MAXIMUM, 'MAX({})', 'MAX'),
        (Maximum, Statistic.MAXIMUM, 'MAX({})', 'MAX'),
        (Mean, Statistic.AVERAGE, 'AVG({})', 'AVG'),
        (Median, Statistic.MEDIAN, 'spyops_median({})', 'MEDIAN'),
        (Min, Statistic.MINIMUM, 'MIN({})', 'MIN'),
        (Minimum, Statistic.MINIMUM, 'MIN({})', 'MIN'),
        (Mode, Statistic.MODE, 'spyops_mode({})', 'MODE'),
        (Most, Statistic.MOST_COMMON, 'spyops_most_common({})', 'MOST_COMMON'),
        (MostCommon, Statistic.MOST_COMMON, 'spyops_most_common({})', 'MOST_COMMON'),
        (Outliers, Statistic.COUNT_OUTLIER, 'spyops_count_outlier({})', 'COUNT_OUTLIER'),
        (Q1, Statistic.FIRST_QUARTILE, 'spyops_first_quartile({})', 'FIRST_QUARTILE'),
        (Q3, Statistic.THIRD_QUARTILE, 'spyops_third_quartile({})', 'THIRD_QUARTILE'),
        (Range, Statistic.RANGE, '(MAX({0}) - MIN({0}))', 'RANGE'),
        (Skew, Statistic.SKEWNESS, 'spyops_skewness({})', 'SKEWNESS'),
        (Skewness, Statistic.SKEWNESS, 'spyops_skewness({})', 'SKEWNESS'),
        (StandardDeviation, Statistic.STANDARD_DEVIATION, 'spyops_stdev({})', 'STDEV'),
        (StdDev, Statistic.STANDARD_DEVIATION, 'spyops_stdev({})', 'STDEV'),
        (Sum, Statistic.SUMMATION, 'SUM({})', 'SUM'),
        (Summation, Statistic.SUMMATION, 'SUM({})', 'SUM'),
        (ThirdQuartile, Statistic.THIRD_QUARTILE, 'spyops_third_quartile({})', 'THIRD_QUARTILE'),
        (Unique, Statistic.UNIQUE, 'COUNT(DISTINCT {})', 'UNIQUE'),
        (Var, Statistic.VARIANCE, 'spyops_var({})', 'VAR'),
        (Variance, Statistic.VARIANCE, 'spyops_var({})', 'VAR'),
        (Variation, Statistic.VARIATION, 'spyops_variation({})', 'VARIATION'),
    ])
    def test_configuration_numeric(self, cls, stat, stub, prefix):
        """
        Test configuration / setup for numeric
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
    # End test_configuration_numeric method

    @mark.parametrize('cls, throws, stat, stub, prefix', [
        (Average, False, Statistic.AVERAGE, "datetime(AVG(unixepoch({}, 'subsecond')), 'unixepoch')", 'AVG'),
        (Avg, False, Statistic.AVERAGE, "datetime(AVG(unixepoch({}, 'subsecond')), 'unixepoch')", 'AVG'),
        (CV, True, Statistic.VARIATION, 'spyops_variation({})', 'VARIATION'),
        (CoefficientOfVariation, True, Statistic.VARIATION, 'spyops_variation({})', 'VARIATION'),
        (Count, False, Statistic.COUNT, 'COUNT({})', 'COUNT'),
        (CountNonNull, False, Statistic.COUNT_NON_NULL, 'SUM(CASE WHEN {} IS NOT NULL THEN 1 ELSE 0 END)', 'COUNT_NON_NULL'),
        (CountNull, False, Statistic.COUNT_NULL, 'SUM(CASE WHEN {} IS NULL THEN 1 ELSE 0 END)', 'COUNT_NULL'),
        (CountOutlier, True, Statistic.COUNT_OUTLIER, 'spyops_count_outlier({})', 'COUNT_OUTLIER'),
        (First, False, Statistic.FIRST, 'spyops_first({})', 'FIRST'),
        (FirstQuartile, False, Statistic.FIRST_QUARTILE, "spyops_first_quartile_date(unixepoch({}, 'subsecond'))", 'FIRST_QUARTILE'),
        (IQR, True, Statistic.INTERQUARTILE_RANGE, 'spyops_interquartile_range({})', 'INTERQUARTILE_RANGE'),
        (InterquartileRange, True, Statistic.INTERQUARTILE_RANGE, 'spyops_interquartile_range({})', 'INTERQUARTILE_RANGE'),
        (Kurt, True, Statistic.KURTOSIS, 'spyops_kurtosis({})', 'KURTOSIS'),
        (Kurtosis, True, Statistic.KURTOSIS, 'spyops_kurtosis({})', 'KURTOSIS'),
        (Last, False, Statistic.LAST, 'spyops_last({})', 'LAST'),
        (Least, False, Statistic.LEAST_COMMON, 'spyops_least_common({})', 'LEAST_COMMON'),
        (LeastCommon, False, Statistic.LEAST_COMMON, 'spyops_least_common({})', 'LEAST_COMMON'),
        (Max, False, Statistic.MAXIMUM, 'MAX({})', 'MAX'),
        (Maximum, False, Statistic.MAXIMUM, 'MAX({})', 'MAX'),
        (Mean, False, Statistic.AVERAGE, "datetime(AVG(unixepoch({}, 'subsecond')), 'unixepoch')", 'AVG'),
        (Median, False, Statistic.MEDIAN, "datetime(spyops_median(unixepoch({}, 'subsecond')), 'unixepoch')", 'MEDIAN'),
        (Min, False, Statistic.MINIMUM, 'MIN({})', 'MIN'),
        (Minimum, False, Statistic.MINIMUM, 'MIN({})', 'MIN'),
        (Mode, False, Statistic.MODE, 'spyops_mode({})', 'MODE'),
        (Most, False, Statistic.MOST_COMMON, 'spyops_most_common({})', 'MOST_COMMON'),
        (MostCommon, False, Statistic.MOST_COMMON, 'spyops_most_common({})', 'MOST_COMMON'),
        (Outliers, True, Statistic.COUNT_OUTLIER, 'spyops_count_outlier({})', 'COUNT_OUTLIER'),
        (Q1, False, Statistic.FIRST_QUARTILE, "spyops_first_quartile_date(unixepoch({}, 'subsecond'))", 'FIRST_QUARTILE'),
        (Q3, False, Statistic.THIRD_QUARTILE, "spyops_third_quartile_date(unixepoch({}, 'subsecond'))", 'THIRD_QUARTILE'),
        (Range, False, Statistic.RANGE, "(MAX(unixepoch({0}, 'subsecond')) -  MIN(unixepoch({0}, 'subsecond')))", 'RANGE'),
        (Skew, True, Statistic.SKEWNESS, 'spyops_skewness({})', 'SKEWNESS'),
        (Skewness, True, Statistic.SKEWNESS, 'spyops_skewness({})', 'SKEWNESS'),
        (StandardDeviation, True, Statistic.STANDARD_DEVIATION, 'spyops_stdev({})', 'STDEV'),
        (StdDev, True, Statistic.STANDARD_DEVIATION, 'spyops_stdev({})', 'STDEV'),
        (Sum, True, Statistic.SUMMATION, 'SUM({})', 'SUM'),
        (Summation, True, Statistic.SUMMATION, 'SUM({})', 'SUM'),
        (ThirdQuartile, False, Statistic.THIRD_QUARTILE, "spyops_third_quartile_date(unixepoch({}, 'subsecond'))", 'THIRD_QUARTILE'),
        (Unique, False, Statistic.UNIQUE, 'COUNT(DISTINCT {})', 'UNIQUE'),
        (Var, True, Statistic.VARIANCE, 'spyops_var({})', 'VAR'),
        (Variance, True, Statistic.VARIANCE, 'spyops_var({})', 'VAR'),
        (Variation, True, Statistic.VARIATION, 'spyops_variation({})', 'VARIATION'),
    ])
    def test_configuration_datetime(self, cls, throws, stat, stub, prefix):
        """
        Test configuration / setup for date time
        """
        field = Field(name='asdf', data_type=FieldType.datetime)
        obj = cls(field)
        if throws:
            with raises(ValueError):
                obj.validate()
        else:
            obj.validate()
            assert obj.field == field
            obj.field = 'lmno'
            obj.field = field
            assert obj.field == field
            assert obj.statistic == stat
            assert obj.aggregate == stub.format(field.escaped_name)
            assert obj.prefix == prefix
            assert obj.output_name == f'{prefix}_asdf'
            assert obj.data_type == FieldType.datetime
    # End test_configuration_datetime method

    @mark.parametrize('cls, throws, stat, stub, prefix', [
        (Average, True, Statistic.AVERAGE, "datetime(AVG(unixepoch({}, 'subsecond')), 'unixepoch')", 'AVG'),
        (Avg, True, Statistic.AVERAGE, "datetime(AVG(unixepoch({}, 'subsecond')), 'unixepoch')", 'AVG'),
        (CV, True, Statistic.VARIATION, 'spyops_variation({})', 'VARIATION'),
        (CoefficientOfVariation, True, Statistic.VARIATION, 'spyops_variation({})', 'VARIATION'),
        (Count, False, Statistic.COUNT, 'COUNT({})', 'COUNT'),
        (CountNonNull, False, Statistic.COUNT_NON_NULL, 'SUM(CASE WHEN {} IS NOT NULL THEN 1 ELSE 0 END)', 'COUNT_NON_NULL'),
        (CountNull, False, Statistic.COUNT_NULL, 'SUM(CASE WHEN {} IS NULL THEN 1 ELSE 0 END)', 'COUNT_NULL'),
        (CountOutlier, True, Statistic.COUNT_OUTLIER, 'spyops_count_outlier({})', 'COUNT_OUTLIER'),
        (First, False, Statistic.FIRST, 'spyops_first({})', 'FIRST'),
        (FirstQuartile, True, Statistic.FIRST_QUARTILE, "spyops_first_quartile_date(unixepoch({}, 'subsecond'))", 'FIRST_QUARTILE'),
        (IQR, True, Statistic.INTERQUARTILE_RANGE, 'spyops_interquartile_range({})', 'INTERQUARTILE_RANGE'),
        (InterquartileRange, True, Statistic.INTERQUARTILE_RANGE, 'spyops_interquartile_range({})', 'INTERQUARTILE_RANGE'),
        (Kurt, True, Statistic.KURTOSIS, 'spyops_kurtosis({})', 'KURTOSIS'),
        (Kurtosis, True, Statistic.KURTOSIS, 'spyops_kurtosis({})', 'KURTOSIS'),
        (Last, False, Statistic.LAST, 'spyops_last({})', 'LAST'),
        (Least, False, Statistic.LEAST_COMMON, 'spyops_least_common({})', 'LEAST_COMMON'),
        (LeastCommon, False, Statistic.LEAST_COMMON, 'spyops_least_common({})', 'LEAST_COMMON'),
        (Max, False, Statistic.MAXIMUM, 'MAX({})', 'MAX'),
        (Maximum, False, Statistic.MAXIMUM, 'MAX({})', 'MAX'),
        (Mean, True, Statistic.AVERAGE, "datetime(AVG(unixepoch({}, 'subsecond')), 'unixepoch')", 'AVG'),
        (Median, True, Statistic.MEDIAN, "datetime(spyops_median_date(unixepoch({}, 'subsecond')), 'unixepoch')", 'MEDIAN'),
        (Min, False, Statistic.MINIMUM, 'MIN({})', 'MIN'),
        (Minimum, False, Statistic.MINIMUM, 'MIN({})', 'MIN'),
        (Mode, False, Statistic.MODE, 'spyops_mode({})', 'MODE'),
        (Most, False, Statistic.MOST_COMMON, 'spyops_most_common({})', 'MOST_COMMON'),
        (MostCommon, False, Statistic.MOST_COMMON, 'spyops_most_common({})', 'MOST_COMMON'),
        (Outliers, True, Statistic.COUNT_OUTLIER, 'spyops_count_outlier({})', 'COUNT_OUTLIER'),
        (Q1, True, Statistic.FIRST_QUARTILE, "spyops_first_quartile_date(unixepoch({}, 'subsecond'))", 'FIRST_QUARTILE'),
        (Q3, True, Statistic.THIRD_QUARTILE, "spyops_third_quartile_date(unixepoch({}, 'subsecond'))", 'THIRD_QUARTILE'),
        (Range, True, Statistic.RANGE, "(MAX(unixepoch({0}, 'subsecond')) -  MIN(unixepoch({0}, 'subsecond')))", 'RANGE'),
        (Skew, True, Statistic.SKEWNESS, 'spyops_skewness({})', 'SKEWNESS'),
        (Skewness, True, Statistic.SKEWNESS, 'spyops_skewness({})', 'SKEWNESS'),
        (StandardDeviation, True, Statistic.STANDARD_DEVIATION, 'spyops_stdev({})', 'STDEV'),
        (StdDev, True, Statistic.STANDARD_DEVIATION, 'spyops_stdev({})', 'STDEV'),
        (Sum, True, Statistic.SUMMATION, 'SUM({})', 'SUM'),
        (Summation, True, Statistic.SUMMATION, 'SUM({})', 'SUM'),
        (ThirdQuartile, True, Statistic.THIRD_QUARTILE, "spyops_third_quartile_date(unixepoch({}, 'subsecond'))", 'THIRD_QUARTILE'),
        (Unique, False, Statistic.UNIQUE, 'COUNT(DISTINCT {})', 'UNIQUE'),
        (Var, True, Statistic.VARIANCE, 'spyops_var({})', 'VAR'),
        (Variance, True, Statistic.VARIANCE, 'spyops_var({})', 'VAR'),
        (Variation, True, Statistic.VARIATION, 'spyops_variation({})', 'VARIATION'),
    ])
    def test_configuration_text(self, cls, throws, stat, stub, prefix):
        """
        Test configuration / setup for text
        """
        field = Field(name='asdf', data_type='varchar(100)')
        obj = cls(field)
        if throws:
            with raises(ValueError):
                obj.validate()
        else:
            obj.validate()
            assert obj.field == field
            obj.field = 'lmno'
            obj.field = field
            assert obj.field == field
            assert obj.statistic == stat
            assert obj.aggregate == stub.format(field.escaped_name)
            assert obj.prefix == prefix
            assert obj.output_name == f'{prefix}_asdf'
            assert obj.data_type == FieldType.text
    # End test_configuration_text method

    @mark.parametrize('cls', [
        Concatenate,
        Concat
    ])
    @mark.parametrize('data_type', [
        FieldType.text,
        FieldType.integer,
        FieldType.real,
        FieldType.date,
        FieldType.timestamp,
    ])
    def test_concatenate(self, cls, data_type):
        """
        Test Concatenate
        """
        field = Field(name='asdf', data_type=data_type)
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
