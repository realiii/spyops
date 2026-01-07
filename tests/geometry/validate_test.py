# -*- coding: utf-8 -*-
"""
Tests for Geometry Validation
"""

from pytest import mark, raises
from shapely import MultiPolygon, Polygon

from gisworks.geometry.validate import (
    check_dimension, check_polygon, check_zm,
    get_geometry_dimension, get_geometry_zm)
from gisworks.shared.exception import OperationsError

pytestmark = [mark.geometry]


@mark.parametrize('polygon, type_', [
    (Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]), Polygon),
    (Polygon([(0, 0), (1, 1), (1, 2), (1, 1), (0, 0)]), type(None)),
    (Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)]), MultiPolygon),
    (MultiPolygon([Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]),
                   Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])]), Polygon),
    (MultiPolygon([Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]),
                   Polygon([(10, 10), (10, 11), (11, 11), (11, 10)])]), MultiPolygon),
    (Polygon([(0, 0), (0, 0), (0, 0), (0, 0)]), type(None)),
])
def test_check_polygon(polygon, type_):
    """
    Test check_polygon
    """
    assert isinstance(check_polygon(polygon), type_)
# End test_check_polygon function


@mark.parametrize('a, b, is_same, throws', [
    (0, 1, False, False),
    (1, 1, False, False),
    (1, 2, False, False),
    (2, 2, False, False),
    (2, 1, False, True),
    (0, 1, True, True),
    (1, 1, True, False),
    (1, 2, True, True),
    (2, 2, True, False),
    (2, 1, True, True),
])
def test_check_dimension(a, b, is_same, throws):
    """
    Test check_dimension
    """
    if throws:
        with raises(OperationsError):
            check_dimension(a, name_a='aa', b=b, name_b='bb', same=is_same)
    else:
        assert check_dimension(a, name_a='aa', b=b, name_b='bb', same=is_same) is None
# End test_check_dimension function


@mark.parametrize('a, b, throws', [
    ((True, False), (True, False), False),
    ((True, False), (False, False), True),
])
def test_check_zm(a, b, throws):
    """
    Test check_zm
    """
    if throws:
        with raises(OperationsError):
            check_zm(a=a, name_a='aa', b=b, name_b='bb')
    else:
        assert check_zm(a=a, name_a='aa', b=b, name_b='bb') is None
# End test_check_zm function


@mark.parametrize('name, dimension', [
    ('airports_p', 0),
    ('airports_mp_p', 0),
    ('roads_l', 1),
    ('roads_mp_l', 1),
    ('admin_a', 2),
    ('admin_mp_a', 2),
])
def test_get_geometry_dimension(world_features, name, dimension):
    """
    Test get_geometry_dimension
    """
    fc = world_features[name]
    assert get_geometry_dimension(fc) == dimension
# End test_get_geometry_dimension function


@mark.parametrize('name, zm', [
    ('airports_p', (False, False)),
    ('airports_mp_p', (False, False)),
    ('roads_l', (False, False)),
    ('roads_mp_l', (False, False)),
    ('admin_a', (False, False)),
    ('admin_mp_a', (False, False)),
])
def test_get_geometry_zm(world_features, name, zm):
    """
    Test get_geometry_zm
    """
    fc = world_features[name]
    assert get_geometry_zm(fc) == zm
# End test_get_geometry_zm function


if __name__ == '__main__':  # pragma: no cover
    pass
