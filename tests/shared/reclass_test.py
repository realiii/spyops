# -*- coding: utf-8 -*-
"""
Test for reclass
"""


from pytest import mark, raises, approx

from spyops.environment import OutputZOption
from spyops.shared.enumeration import (
    ReclassificationMethod,
    StandardDeviationOptions)
from spyops.shared.reclass import (
    DefinedIntervalReclass, EqualIntervalReclass,
    ManualReclass, NaturalBreaksReclass, QuantileReclass,
    StandardDeviationReclass, _fisher_jenks)

pytestmark = [mark.reclass]


class TestDefinedIntervalReclass:
    """
    Test Defined Interval Reclass
    """
    @mark.parametrize('interval, exception', [
        (None, TypeError),
        (Ellipsis, TypeError),
        (0, ValueError),
        (-1, ValueError),
    ])
    def test_validate(self, interval, exception):
        """
        Test validate
        """
        with raises(exception):
            DefinedIntervalReclass(interval)
    # End test_validate method

    def test_method(self):
        """
        Test method
        """
        reclass = DefinedIntervalReclass(1)
        assert reclass.method == ReclassificationMethod.DEFINED_INTERVAL
    # End test_method method

    @mark.parametrize('interval, min_, max_, expected', [
        (1, 0, 10, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        (2.5, 0.5, 13.25, [0.5, 3.0, 5.5, 8.0, 10.5, 13.0, 15.5]),
    ])
    def test_build_breaks(self, interval, min_, max_, expected):
        """
        Test build breaks
        """
        reclass = DefinedIntervalReclass(interval)
        breaks = reclass._build_breaks(min_, max_)
        assert breaks == expected
    # End test_build_breaks method

    @mark.parametrize('breaks, expected', [
        ([0, 3, 6, 9], ['0.000000 - 3.000000', '3.000000 - 6.000000', '6.000000 - 9.000000']),
        ([0.5, 5.5, 10.5, 15.5], ['0.500000 - 5.500000', '5.500000 - 10.500000', '10.500000 - 15.500000']),
        ([10_000_000, 20_000_000.123456, 100_000_000.9876543], ['10000000.000000 - 20000000.123456', '20000000.123456 - 100000000.987654'] ),
    ])
    def test_build_labels(self, breaks, expected):
        """
        Test build labels
        """
        reclass = DefinedIntervalReclass()
        labels = reclass._build_labels(breaks)
        assert labels == expected
    # End test_build_labels method

    @mark.parametrize('breaks, truth, expected', [
        ([0, 3, 6, 9], (False, True), [0, 3, 6, 9, 10]),
        ([5.5, 10.5, 15.5], (True, False), [1, 5.5, 10.5, 15.5]),
    ])
    def test_add_min_max(self, breaks, truth, expected):
        """
        Test add min max
        """
        result = DefinedIntervalReclass._add_min_max(breaks, 1, 10)
        assert result == truth
        assert breaks == expected
    # End test_add_min_max method
# End TestDefinedIntervalReclass class


class TestEqualIntervalReclass:
    """
    Test Equal Interval Reclass
    """
    @mark.parametrize('classes, exception', [
        (None, TypeError),
        (Ellipsis, TypeError),
        (1.23, TypeError),
        (0, ValueError),
        (-1, ValueError),
        (500, ValueError),
    ])
    def test_validate(self, classes, exception):
        """
        Test validate
        """
        with raises(exception):
            EqualIntervalReclass(classes)
    # End test_validate method

    def test_method(self):
        """
        Test method
        """
        reclass = EqualIntervalReclass(1)
        assert reclass.method == ReclassificationMethod.EQUAL_INTERVAL
    # End test_method method

    @mark.parametrize('classes, min_, max_, expected', [
        (2, 0, 10, [0.0, 5.0, 10.0]),
        (5, 0.5, 13.25, [0.5, 3.05, 5.6, 8.15, 10.7, 13.25]),
    ])
    def test_build_breaks(self, classes, min_, max_, expected):
        """
        Test build breaks
        """
        reclass = EqualIntervalReclass(classes)
        breaks = reclass._build_breaks(min_, max_)
        assert approx(breaks, abs=0.01) == expected
    # End test_build_breaks method
# End TestEqualIntervalReclass class


class TestManualReclass:
    """
    Test Manual Reclass
    """
    @mark.parametrize('table, exception', [
        (None, TypeError),
        (Ellipsis, TypeError),
        ([], ValueError),
        (['a', 'b', 'c'], TypeError),
        ([[], []], TypeError),
        ([['a', 'b'], [1, 2]], TypeError),
        ([[1, None], [2, 'a']], TypeError),
        ([[1, 'b'], [1, 'a']], ValueError),
    ])
    def test_validate(self, table, exception):
        """
        Test validate
        """
        with raises(exception):
            ManualReclass(table)
    # End test_validate method

    def test_method(self):
        """
        Test method
        """
        reclass = ManualReclass([(1, 'a'), (2, 'b'), (3, 'c')])
        assert reclass.method == ReclassificationMethod.MANUAL
    # End test_method method

    def test_build_breaks(self):
        """
        Test build breaks
        """
        reclass = ManualReclass([(1, 'a'), (2, 'b'), (3, 'c')])
        breaks, labels = reclass._build_breaks(0, 4)
        assert breaks == [0, 1, 2, 3, 4]
        assert labels == ['', 'a', 'b', 'c', '']
    # End test_build_breaks method
# End TestManualReclass class


class TestNaturalBreaksReclass:
    """
    Test Natural Breaks Reclass
    """
    def test_method(self):
        """
        Test method
        """
        reclass = NaturalBreaksReclass(1)
        assert reclass.method == ReclassificationMethod.NATURAL_BREAKS
    # End test_method method

    @mark.parametrize('classes, expected', [
        (10, [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]),
        (5, [1, 20, 40, 60, 80, 100])
    ])
    def test_jenks(self, classes, expected):
        """
        Test jenks
        """
        values = list(range(1, 101))
        breaks = _fisher_jenks(values, classes)
        assert approx(breaks, abs=0.01) == expected
    # End test_jenks method
# End TestNaturalBreaksReclass class


class TestQuantileReclass:
    """
    Test Quantile Reclass
    """
    def test_method(self):
        """
        Test method
        """
        reclass = QuantileReclass(1)
        assert reclass.method == ReclassificationMethod.QUANTILE
    # End test_method method

    def test_build_breaks(self):
        """
        Test build breaks
        """
        values = list(range(1, 100))
        reclass = QuantileReclass(4)
        breaks = reclass._build_breaks(values)
        assert approx(breaks, abs=0.01) == [1, 25, 50, 75, 99]
    # End test_build_breaks method
# End TestQuantileReclass class


class TestStandardDeviationReclass:
    """
    Test Standard Deviation Reclass
    """
    @mark.parametrize('deviations, exception', [
        (None, ValueError),
        (OutputZOption.ENABLED, ValueError),
    ])
    def test_validate(self, deviations, exception):
        """
        Test validate
        """
        with raises(exception):
            StandardDeviationReclass(deviations)
    # End test_validate method

    def test_method(self):
        """
        Test method
        """
        reclass = StandardDeviationReclass()
        assert reclass.method == ReclassificationMethod.STANDARD_DEVIATION
    # End test_method method

    @mark.parametrize('deviations, expected', [
        (StandardDeviationOptions.ONE, (5, 1.)),
        (StandardDeviationOptions.HALF, (9, 1 / 2)),
        (StandardDeviationOptions.THIRD, (15, 1 / 3)),
        (StandardDeviationOptions.QUARTER, (17, 1 / 4)),
    ])
    def test_get_classes(self, deviations, expected):
        """
        Test get classes
        """
        reclass = StandardDeviationReclass(deviations)
        assert reclass._get_classes() == expected
    # End test_get_classes method

    def test_build_breaks(self):
        """
        Test build breaks
        """
        reclass = StandardDeviationReclass()
        count, size = reclass._get_classes()
        half_count = int((count - 1) / 2)
        breaks, devs = reclass._build_breaks(
            avg=5, dev=1, min_=1.234, max_=12.345,
            half_count=half_count, size=size)
        assert breaks == [1.234, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 12.345]
        assert devs == [-2.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 2.5]
    # End test_build_breaks method

    def test_build_labels(self):
        """
        Test build labels
        """
        reclass = StandardDeviationReclass()
        breaks = [1.234, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 12.345]
        devs = [-2.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 2.5]
        labels = reclass._build_extended_labels(breaks, devs)
        assert labels == [
            '1.234000 - 2.500000 (< -2.500 Std. Dev.)',
            '2.500000 - 3.500000 (-2.500 - -1.500 Std. Dev.)',
            '3.500000 - 4.500000 (-1.500 - -0.500 Std. Dev.)',
            '4.500000 - 5.500000 (-0.500 - 0.500 Std. Dev.)',
            '5.500000 - 6.500000 (0.500 - 1.500 Std. Dev.)',
            '6.500000 - 7.500000 (1.500 - 2.500 Std. Dev.)',
            '7.500000 - 12.345000 (> 2.500 Std. Dev.)']
    # End test_build_labels method
# End TestStandardDeviationReclass class


if __name__ == '__main__':  # pragma: no cover
    pass
