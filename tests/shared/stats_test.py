# -*- coding: utf-8 -*-
"""
Test Statistics
"""


from pytest import mark, approx

from spyops.shared.stats import first, last, median, mode, stdev, var

pytestmark = [mark.statistics]


@mark.parametrize('values, expected', [
    ([], None),
    ([[]], None),
    ([1, 2, 3], 1),
    ([1, 2, 2, 3], 2),
    ([1, 2, 2, None, 3], 2),
    (['a', 'b', 'c', None, 'c'], 'c'),
])
def test_mode(values, expected):
    """
    Test mode
    """
    assert mode(values) == expected
# End test_mode function


@mark.parametrize('values, expected', [
    ([], None),
    ([[]], None),
    ([1, 2, 3], 1.),
    ([1, 2, 3, 4, 5], 1.5811),
    ([1, 2, None, 3], 1.),
    (['a', 'b', 'c', None, 'c'], None),
])
def test_stdev(values, expected):
    """
    Test standard deviation
    """
    assert approx(stdev(values), abs=0.001) == expected
# End test_stdev function


@mark.parametrize('values, expected', [
    ([], None),
    ([[]], None),
    ([1, 2, 3], 1.),
    ([1, 2, 3, 4, 5], 2.5),
    ([1, 2, None, 3], 1.),
    (['a', 'b', 'c', None, 'c'], None),
])
def test_var(values, expected):
    """
    Test variance
    """
    assert approx(var(values), abs=0.001) == expected
# End test_var function


@mark.parametrize('values, expected', [
    ([], None),
    ([[]], None),
    ([1, 2, 3], 2),
    ([1, 2, 3, 4, 5], 3),
    ([1, 2, None, 3], 2),
    (['a', 'b', 'c', None, 'c'], None),
])
def test_median(values, expected):
    """
    Test median
    """
    assert approx(median(values), abs=0.001) == expected
# End test_median function


@mark.parametrize('values, expected', [
    ([], None),
    ([1, 2, 3], 1),
    ([1, 2, 3, 4, 5], 1),
    ([1, 2, None, 3], 1),
    (['a', 'b', 'c', None, 'c'], 'a'),
])
def test_first(values, expected):
    """
    Test first value
    """
    assert first(values) == expected
# End test_first function


@mark.parametrize('values, expected', [
    ([], None),
    ([1, 2, 3], 3),
    ([1, 2, 3, 4, 5], 5),
    ([1, 2, None, 3], 3),
    (['a', 'b', 'c', None, 'c'], 'c'),
])
def test_last(values, expected):
    """
    Test last value
    """
    assert last(values) == expected
# End test_last function


if __name__ == '__main__':  # pragma: no cover
    pass
