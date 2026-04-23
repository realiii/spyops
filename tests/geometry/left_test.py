# -*- coding: utf-8 -*-
"""
Test cases for understanding operator order
"""

from pytest import fixture, mark

from shapely import intersection, difference, from_wkt
from shapely import force_2d
from shapely import LineString, Polygon, Point, MultiPoint


pytestmark = [mark.geometry]


@fixture(scope='module')
def poly_a() -> Polygon:
    """
    Polygon A
    """
    return from_wkt(
        'Polygon ((0 0 0 0, 0 10 1 1, 10 10 2 3, 10 0 4 5, 0 0 6 7))')
# End poly_a function


@fixture(scope='module')
def poly_b() -> Polygon:
    """
    Polygon B
    """
    return from_wkt(
        'Polygon ((2 2 0 10, 2 12 1 100, 12 12 2 300, 12 2 4 500, 2 2 0 10))')
# End poly_b function


@fixture(scope='module')
def line_a() -> LineString:
    """
    LineString A
    """
    return from_wkt(
        'LineString (0 0 0 0, 0 10 1 1, 10 10 2 3, 10 0 4 5, 0 0 6 7)')
# End line_a function


@fixture(scope='module')
def line_b() -> LineString:
    """
    LineString B
    """
    return from_wkt(
        'LineString (2 2 0 10, 2 12 1 100, 12 12 2 300, 12 2 4 500, 2 2 0 10)')
# End line_b function


@fixture(scope='module')
def multi_point_a() -> MultiPoint:
    """
    MultiPoint A
    """
    coords = ['0 0 0 0', '0 10 1 1', '10 10 2 3', '10 0 4 5', '0 0 6 7']
    return MultiPoint([from_wkt(f'Point ({c})') for c in coords])
# End multi_point_a function


@fixture(scope='module')
def multi_point_b() -> MultiPoint:
    """
    MultPoint B
    """
    coords = ['2 2 0 10', '2 12 1 100', '12 12 2 300', '12 2 4 500', '2 2 0 10']
    return MultiPoint([from_wkt(f'Point ({c})') for c in coords])
# End multi_point_b function


@fixture(scope='module')
def point_a() -> Point:
    """
    Point A
    """
    return from_wkt('Point (5 5 2 3)')
# End point_a function


@fixture(scope='module')
def point_b() -> Point:
    """
    Point B
    """
    return from_wkt('Point (0 5 2 300)')
# End point_b function


@mark.parametrize('a, b, expected', [
    ('poly_a', 'poly_b', 'POLYGON ZM ((2 2 0 10, 2 10 0.8 82, 10 10 2 NaN, 10 2 3.2 402, 2 2 0 10))'),
    ('poly_a', 'line_b', 'MULTILINESTRING ZM ((2 2 0 10, 10 2 3.2 402), (2 2 0 10, 2 10 0.8 82))'),
    ('poly_a', 'multi_point_a', 'MULTIPOINT ZM ((10 10 2 3), (10 0 4 5), (0 10 1 1), (0 0 0 0))'),
    ('poly_a', 'multi_point_b', 'POINT ZM (2 2 0 10)'),
    ('poly_a', 'point_a', 'POINT ZM (5 5 2 3)'),
    ('poly_a', 'point_b', 'POINT ZM (0 5 2 300)'),
    ('line_a', 'line_b', 'MULTIPOINT ZM ((10 2 3.2 402), (2 10 0.8 82))'),
    ('line_a', 'poly_b', 'LINESTRING ZM (2 10 0.8 82, 10 10 2 NaN, 10 2 3.2 402)'),
    ('line_a', 'multi_point_a', 'MULTIPOINT ZM ((10 10 2 3), (10 0 4 5), (0 10 1 1), (0 0 0 0))'),
    ('line_a', 'multi_point_b', 'POINT Z EMPTY'),
    ('line_a', 'point_a', 'POINT Z EMPTY'),
    ('line_a', 'point_b', 'POINT ZM (0 5 2 300)'),
])
def test_intersection_order(request, a, b, expected):
    """
    Test intersection order
    """
    a = request.getfixturevalue(a)
    a = force_2d(a)
    b = request.getfixturevalue(b)
    result_ab = intersection(a, b).normalize()
    assert result_ab.wkt == expected
    assert result_ab == intersection(b, a).normalize()
    assert result_ab == a.intersection(b).normalize()
    assert result_ab == b.intersection(a).normalize()
# End test_intersection_order function


if __name__ == '__main__':  # pragma: no cover
    pass
