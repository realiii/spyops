# -*- coding: utf-8 -*-
"""
Test utilities
"""


from pytest import mark
from shapely import LineString, Polygon
from shapely.io import from_wkt

from spyops.geometry.util import get_coords_and_slices
from spyops.geometry.wa.util import (
    check_has_measure, ensure_iterable,
    get_shape_type_from_geom, get_slicer, linestring_measures_to_zs,
    polygon_measures_to_zs)

pytestmark = [mark.geometry]


@mark.parametrize('value, is_iterable', [
    (None, False),
    (1, False),
    ('test', False),
    ([], True),
    ((), True),
    ((1, 2, 3), True),
    (LineString([(0, 0), (10, 10)]), False)
])
def test_ensure_iterable(value, is_iterable):
    """
    Test ensure iterable
    """
    a, b = ensure_iterable(value)
    assert a == is_iterable
    assert isinstance(b, (list, tuple))
# End test_ensure_iterable function


@mark.parametrize('has_z, has_m, expected', [
    (False, False, 'operator.itemgetter(0, 1)'),
    (True, False, 'operator.itemgetter(0, 1, 2)'),
    (False, True, 'operator.itemgetter(0, 1, 2)'),
    (True, True, 'operator.itemgetter(0, 1, 2, 3)'),
])
def test_get_slicer(has_z, has_m, expected):
    """
    Test get slicer
    """
    getter = get_slicer(has_z=has_z, has_m=has_m)
    assert repr(getter) == expected
# End test_get_slicer function


def test_linestring_measures_to_zs():
    """
    Test linestring measures to zs
    """
    line = from_wkt('LineString M (0 0 0, 10 10 12)')
    assert line.has_m
    assert not line.has_z
    line, = linestring_measures_to_zs([line])
    assert not line.has_m
    assert line.has_z
    coords, _ = get_coords_and_slices([line], include_z=True, include_m=False)
    assert coords.tolist() == [[0, 0, 0], [10, 10, 12]]
# End test_linestring_measures_to_zs function


def test_polygon_measures_to_zs():
    """
    Test polygon measures to zs
    """
    poly = from_wkt('Polygon M ((0 0 0, 10 0 1, 10 10 2, 0 10 3, 0 0 0), (3 3 50, 6 3 100, 6 6 200, 3 6 300, 3 3 50))')
    assert poly.has_m
    assert not poly.has_z
    poly, = polygon_measures_to_zs([poly])
    assert not poly.has_m
    assert poly.has_z
    coords, _ = get_coords_and_slices([poly], include_z=True, include_m=False)
    assert coords.tolist() == [
        [0, 0, 0], [10, 0, 1], [10, 10, 2], [0, 10, 3], [0, 0, 0],
        [3, 3, 50], [6, 3, 100], [6, 6, 200], [3, 6, 300], [3, 3, 50]]
# End test_polygon_measures_to_zs function


@mark.parametrize('geom, expected', [
    (LineString([(0, 0), (10, 10)]), 'LINESTRING'),
    (Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]), 'POLYGON')
])
def test_get_shape_type_from_geom(geom, expected):
    """
    Test get_shape_type_from_geom
    """
    geoms = [geom] * 10
    assert get_shape_type_from_geom(geoms) == expected
# End test_get_shape_type_from_geom function


@mark.parametrize('geom, expected', [
    (from_wkt('LineString M (0 0 0, 10 10 12)'), True),
    (from_wkt('Polygon M ((0 0 0, 10 0 2, 10 10 5, 0 10 11, 0 0 0))'), True),
    ([from_wkt('LineString M (0 0 0, 10 10 12)')], True),
    ([from_wkt('Polygon M ((0 0 0, 10 0 2, 10 10 5, 0 10 11, 0 0 0))')], True),
    (from_wkt('LineString Z (0 0 0, 10 10 12)'), False),
    (from_wkt('Polygon Z ((0 0 0, 10 0 2, 10 10 5, 0 10 11, 0 0 0))'), False),
    ([from_wkt('LineString Z (0 0 0, 10 10 12)')], False),
    ([from_wkt('Polygon Z ((0 0 0, 10 0 2, 10 10 5, 0 10 11, 0 0 0))')], False),
    ([], False),
])
def test_check_has_measures(geom, expected):
    """
    Test check has measures
    """
    assert check_has_measure(geom) == expected
# End test_check_has_measures function


if __name__ == '__main__':  # pragma: no cover
    pass
