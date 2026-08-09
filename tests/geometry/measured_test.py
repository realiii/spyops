# -*- coding: utf-8 -*-
"""
Test module for Measured Line
"""


from math import sqrt

from numpy import arange, isnan
from pytest import approx, fixture, mark, raises

from spyops.geometry.measured import MeasuredLine

pytestmark = [mark.geometry]


@fixture(scope='session')
def straight_line() -> MeasuredLine:
    """
    Make a straight line
    """
    x = y = z = (arange(20) * 100).tolist()
    return MeasuredLine(xs=x, ys=y, zs=z)
# End straight_line function


@fixture(scope='session')
def threed_line() -> MeasuredLine:
    """
    Make a 3D line
    """
    x = y = z = (arange(20) * 100).tolist()
    z = z[:10] + [900, 1000, 800, 1200, 900, 1200, 1200, 1200, 1300, 1400]
    z = [-i for i in z]
    return MeasuredLine(xs=x, ys=y, zs=z)
# End threed_line function


def test_interpolate_straight_line(straight_line):
    """
    Round Trip Test on Straight Line
    """
    assert straight_line.interpolate(straight_line.measures).tolist() == straight_line.coordinates.tolist()
# End test_interpolate_straight_line function


def test_interpolate_3d_line(threed_line):
    """
    Round Trip Test on 3D Line
    """
    assert threed_line.interpolate(threed_line.measures).tolist() == threed_line.coordinates.tolist()
# End test_interpolate_3d_line function


def test_find_coordinate_no_measures(straight_line):
    """
    Test no measures
    """
    assert len(straight_line.interpolate([])) == 0
# End test_find_coordinate_no_measures function


@mark.parametrize('m_value', [
    -1000, 10_000
])
def test_find_coordinate_measures_out_of_bounds(straight_line, m_value):
    """
    Test bad measures
    """
    result = straight_line.interpolate([m_value])
    assert isnan(result).all()
# End test_find_coordinate_measures_out_of_bounds function


def test_provide_incorrect_length_measures():
    """
    Test that provides a measures list that has the correct length
    """
    x = y = z = (arange(20) * 100).tolist()
    m = (arange(20) * 100 * sqrt(3)).tolist()[:18]
    with raises(ValueError):
        MeasuredLine(xs=x, ys=y, zs=z, ms=m)
# End test_provide_incorrect_length_measures function


def test_provide_incorrect_length_coordinates():
    """
    Test that provides a measures list that has the correct length
    """
    x = y = z = (arange(20) * 100).tolist()
    with raises(ValueError):
        MeasuredLine(x, y, zs=z[:18])
# End test_provide_incorrect_length_coordinates function


@mark.parametrize('m_values', [
    [0, 1, 2, 3, 3, 4, 5, 6, 6, 7],
    [0, 1, 2, 5, 4, 3, 6, 7, 8, 9]
])
def test_validate_measures(m_values):
    """
    Test that an exception is thrown
    """
    with raises(ValueError):
        MeasuredLine._validate_measures(m_values)
# End test_validating_measures function


@mark.parametrize('m_value, snap, expected', [
    (0, False, 0),
    (0, True, 0),
    (-100, True, 0),
    (-100, False, None),
    (692.8203230275509, False, 400),
    (692.8203230275509 + (50 * sqrt(3)), False, 450),
    (3290.896534380868, False, 1900),
    (3300, False, None),
    (3390, True, 1900),
])
def test_find_z(straight_line, m_value, snap, expected):
    """
    Test getting z
    """
    assert approx(straight_line.find_z(m_value, snap=snap), abs=0.001) == expected
# End test_find_z function


@mark.parametrize('m_value, snap, expected', [
    (0, False, (0, 0, 0)),
    (0, True, (0, 0, 0)),
    (-100, True, (0, 0, 0)),
    (-100, False, None),
    (692.8203230275509, False, (400, 400, 400)),
    (692.8203230275509 + (50 * sqrt(3)), False, (450, 450, 450)),
    (3290.896534380868, False, (1900, 1900, 1900)),
    (3300, False, None),
    (3390, True, (1900, 1900, 1900)),
])
def test_find_xyz(straight_line, m_value, snap, expected):
    """
    Test getting xyz
    """
    assert approx(straight_line.find_xyz(m_value, snap=snap), abs=0.001) == expected
# End test_find_xyz function


@mark.parametrize('m_value, first, second', [
    (0, (0, 0, 0), (100, 100, 100)),
    (25, (0, 0, 0), (100, 100, 100)),
    (519.6152422706632, (200, 200, 200), (300, 300, 300)),
    (520.6152422706632, (300, 300, 300), (400, 400, 400)),
    (3200, (1800, 1800, 1800), (1900, 1900, 1900)),
    (3290.896534380868, (1800, 1800, 1800), (1900, 1900, 1900)),
])
def test_find_segment(straight_line, m_value, first, second):
    """
    Test finding segment based on small measure, should
    return the first segment
    """
    start, end = straight_line._find_segment(m_value)
    assert tuple(start[:-1]) == first
    assert tuple(end[:-1]) == second
# End test_find_segment function


@mark.parametrize('m_value', [
    -50, 5000
])
def test_find_segment_measure_out_of_bounds(straight_line, m_value):
    """
    Test that no segment is returned when measure is out of bounds
    """
    assert straight_line._find_segment(m_value) == (None, None)
# End test_find_segment_measure_out_of_bounds function


def test_vertical_line_measure_calculation():
    """
    Test measure calculations for vertical line
    """
    x = y = (0,) * 20
    z = tuple((arange(20) * 100).tolist())
    line = MeasuredLine(x, y, zs=z)
    xx, yy, zz, mm = zip(*line.coordinates)
    assert x == xx
    assert y == yy
    assert z == zz
    assert z == mm
# End test_vertical_line_measure_calculation function


def test_straight_line_measure_calculation():
    """
    Test measure calculations for a straight line
    """
    x = y = z = tuple((arange(20) * 100).tolist())
    m = tuple((arange(20) * 100 * sqrt(3)).tolist())
    line = MeasuredLine(x, y, zs=z)
    xx, yy, zz, mm = zip(*line.coordinates)
    assert x == xx
    assert y == yy
    assert z == zz
    assert approx(m, abs=10**-6) == mm
# End test_straight_line_measure_calculation function


def test_provide_correct_length_measures():
    """
    Test that provides a measures list that has the correct length
    """
    x = y = z = tuple((arange(20) * 100).tolist())
    m = tuple((arange(20) * 100 * sqrt(3)).tolist())
    line = MeasuredLine(xs=x, ys=y, zs=z, ms=m)
    xx, yy, zz, mm = zip(*line.coordinates)
    assert x == xx
    assert y == yy
    assert z == zz
    assert approx(m, abs=10**-6) == mm
# End test_provide_correct_length_measures function


if __name__ == '__main__':
    pass
