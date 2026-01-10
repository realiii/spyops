# -*- coding: utf-8 -*-
"""
Tests for Geometry Convert Module
"""


from math import nan

from fudgeo.constant import WGS84
from fudgeo.geometry.linestring import (
    LineString, LineStringM, LineStringZ, LineStringZM, MultiLineString,
    MultiLineStringM, MultiLineStringZ, MultiLineStringZM)
from fudgeo.geometry.point import (
    MultiPoint, MultiPointM, MultiPointZ, MultiPointZM, Point, PointM,
    PointZ, PointZM)
from fudgeo.geometry.polygon import (
    MultiPolygon, MultiPolygonM, MultiPolygonZ, MultiPolygonZM, Polygon,
    PolygonM, PolygonZ, PolygonZM)
from numpy import array, isnan, ndarray
from pytest import approx, mark
from shapely.io import from_wkb

from gisworks.geometry.convert import (
    _as_lines, _find_slice_indexes, _update_z_values, _use_boundary_factory,
    cast_linestrings, cast_multi_linestrings, cast_multi_points,
    cast_multi_polygons, cast_points, cast_polygons, get_geometry_converters)
from gisworks.geometry.util import nada
from gisworks.shared.enumeration import OutputTypeOption
from gisworks.environment.enumeration import Setting
from gisworks.environment.context import Swap


pytestmark = [mark.geometry]


def _summer(values: list | ndarray):
    """
    Sum list
    """
    if hasattr(values, 'tolist'):
        values = values.tolist()
    return sum(values, [])
# End _summer function


@mark.parametrize('output_type_option, source_name, operator_name, expected', [
    (OutputTypeOption.SAME, 'utmzone_sparse_a', 'intersect_a', (False, False)),
    (OutputTypeOption.LINE, 'utmzone_sparse_a', 'intersect_a', (True, True)),
    (OutputTypeOption.POINT, 'utmzone_sparse_a', 'intersect_a', (True, True)),
    (OutputTypeOption.SAME, 'rivers_portion_l', 'intersect_a', (False, False)),
    (OutputTypeOption.LINE, 'rivers_portion_l', 'intersect_a', (False, False)),
    (OutputTypeOption.POINT, 'rivers_portion_l', 'intersect_a', (False, True)),
    (OutputTypeOption.SAME, 'river_p', 'intersect_a', (False, False)),
    (OutputTypeOption.POINT, 'river_p', 'intersect_a', (False, False)),

    (OutputTypeOption.SAME, 'rivers_portion_l', 'rivers_portion_l', (False, False)),
    (OutputTypeOption.LINE, 'rivers_portion_l', 'rivers_portion_l', (False, False)),
    (OutputTypeOption.POINT, 'rivers_portion_l', 'rivers_portion_l', (False, False)),
    (OutputTypeOption.POINT, 'river_p', 'rivers_portion_l', (False, False)),

    (OutputTypeOption.SAME, 'river_p', 'river_p', (False, False)),
    (OutputTypeOption.POINT, 'river_p', 'river_p', (False, False)),
])
def test_use_boundary_factory(inputs, output_type_option, source_name, operator_name, expected):
    """
    Test _use_boundary_factory, not all cases are tested here because
    there is a reliance on validate_output_type to prevent invalid combinations
    from getting into the factory.
    """
    source = inputs[source_name]
    operator = inputs[operator_name]
    assert _use_boundary_factory(
        source.shape_type, operator_shape_type=operator.shape_type,
        output_type_option=output_type_option) == expected
# End test_use_boundary_factory function


@mark.parametrize('output_type_option, source_name, operator_name, expected', [
    (OutputTypeOption.SAME, 'utmzone_sparse_a', 'intersect_a', (nada, nada)),
    (OutputTypeOption.LINE, 'utmzone_sparse_a', 'intersect_a', (_as_lines, _as_lines)),
    (OutputTypeOption.POINT, 'utmzone_sparse_a', 'intersect_a', (_as_lines, _as_lines)),
    (OutputTypeOption.SAME, 'rivers_portion_l', 'intersect_a', (nada, nada)),
    (OutputTypeOption.LINE, 'rivers_portion_l', 'intersect_a', (nada, nada)),
    (OutputTypeOption.POINT, 'rivers_portion_l', 'intersect_a', (nada, _as_lines)),
    (OutputTypeOption.SAME, 'river_p', 'intersect_a', (nada, nada)),
    (OutputTypeOption.POINT, 'river_p', 'intersect_a', (nada, nada)),

    (OutputTypeOption.SAME, 'rivers_portion_l', 'rivers_portion_l', (nada, nada)),
    (OutputTypeOption.LINE, 'rivers_portion_l', 'rivers_portion_l', (nada, nada)),
    (OutputTypeOption.POINT, 'rivers_portion_l', 'rivers_portion_l', (nada, nada)),
    (OutputTypeOption.POINT, 'river_p', 'rivers_portion_l', (nada, nada)),

    (OutputTypeOption.SAME, 'river_p', 'river_p', (nada, nada)),
    (OutputTypeOption.POINT, 'river_p', 'river_p', (nada, nada)),
])
def test_get_geometry_converters(inputs, output_type_option, source_name, operator_name, expected):
    """
    Test get_geometry_converters
    """
    source = inputs[source_name]
    operator = inputs[operator_name]
    assert get_geometry_converters(source, operator=operator, output_type_option=output_type_option) == expected
# End test_get_geometry_converters function


@mark.parametrize('indexes, expected', [
    ([], ()),
    ([0, 0, 1, 1], (0, 2, 4)),
    ([0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2], (0, 3, 8, 12)),
])
def test_find_slice_indexes(indexes, expected):
    """
    Test _find_slice_indexes
    """
    assert _find_slice_indexes(array(indexes, dtype=int)) == expected
# End test_find_slice_indexes function


@mark.parametrize('has_z, z_value, expected', [
    (False, nan, True),
    (True, nan, True),
    (False, 1, True),
    (True, 1, False),
])
def test_update_z_values(has_z, z_value, expected):
    """
    Test update z value
    """
    data = array([(1, 2, nan), (3, 4, nan), (5, 6, nan)], dtype=float)
    with Swap(Setting.Z_VALUE, z_value):
        _update_z_values(data, has_z=has_z)
    assert bool(isnan(data[:, 2]).all()) is expected
# End test_update_z_value function


@mark.parametrize('pt, has_z, has_m, values', [
    (Point(x=1, y=2, srs_id=WGS84), False, False, (1, 2)),
    (Point(x=1, y=2, srs_id=WGS84), True, False, (1, 2, nan)),
    (Point(x=1, y=2, srs_id=WGS84), False, True, (1, 2, nan)),
    (Point(x=1, y=2, srs_id=WGS84), True, True, (1, 2, nan, nan)),
    (PointZ(x=1, y=2, z=3, srs_id=WGS84), False, False, (1, 2)),
    (PointZ(x=1, y=2, z=3, srs_id=WGS84), True, False, (1, 2, 3)),
    (PointZ(x=1, y=2, z=3, srs_id=WGS84), False, True, (1, 2, nan)),
    (PointZ(x=1, y=2, z=3, srs_id=WGS84), True, True, (1, 2, 3, nan)),
    (PointM(x=1, y=2, m=4, srs_id=WGS84), False, False, (1, 2)),
    (PointM(x=1, y=2, m=4, srs_id=WGS84), True, False, (1, 2, nan)),
    (PointM(x=1, y=2, m=4, srs_id=WGS84), False, True, (1, 2, 4)),
    (PointM(x=1, y=2, m=4, srs_id=WGS84), True, True, (1, 2, nan, 4)),
    (PointZM(x=1, y=2, z=3, m=4, srs_id=WGS84), False, False, (1, 2)),
    (PointZM(x=1, y=2, z=3, m=4, srs_id=WGS84), True, False, (1, 2, 3)),
    (PointZM(x=1, y=2, z=3, m=4, srs_id=WGS84), False, True, (1, 2, 4)),
    (PointZM(x=1, y=2, z=3, m=4, srs_id=WGS84), True, True, (1, 2, 3, 4)),
])
def test_cast_points(pt, has_z, has_m, values):
    """
    Test Point casting
    """
    spt = from_wkb(pt.wkb)
    results = cast_points([spt], srs_id=pt.srs_id, has_z=has_z, has_m=has_m)
    assert len(results) == 1
    cpt, = results
    if has_m:
        assert 'm' in cpt.__slots__
    if has_z:
        assert 'z' in cpt.__slots__
    coords = cpt.as_tuple()
    assert len(coords) == len(values)
    assert approx(coords, nan_ok=True) == values
# End test_cast_points function


@mark.parametrize('cls, values, has_z, has_m, expected', [
    (MultiPoint, [[(0, 1)], [(10, 11), (20, 21)], [(100, 101), (200, 201), (300, 301)]], False, False,
     [[(0, 1)], [(10, 11), (20, 21)], [(100, 101), (200, 201), (300, 301)]]),
    (MultiPoint, [[(0, 1)], [(10, 11), (20, 21)], [(100, 101), (200, 201), (300, 301)]], True, False,
     [[(0, 1, nan)], [(10, 11, nan), (20, 21, nan)], [(100, 101, nan), (200, 201, nan), (300, 301, nan)]]),
    (MultiPoint, [[(0, 1)], [(10, 11), (20, 21)], [(100, 101), (200, 201), (300, 301)]], False, True,
     [[(0, 1, nan)], [(10, 11, nan), (20, 21, nan)], [(100, 101, nan), (200, 201, nan), (300, 301, nan)]]),
    (MultiPoint, [[(0, 1)], [(10, 11), (20, 21)], [(100, 101), (200, 201), (300, 301)]], True, True,
     [[(0, 1, nan, nan)], [(10, 11, nan, nan), (20, 21, nan, nan)], [(100, 101, nan, nan), (200, 201, nan, nan), (300, 301, nan, nan)]]),
    (MultiPointZ, [[(0, 1, 2)], [(10, 11, 12), (20, 21, 22)], [(100, 101, 102), (200, 201, 202), (300, 301, 302)]], False, False,
     [[(0, 1)], [(10, 11), (20, 21)], [(100, 101), (200, 201), (300, 301)]]),
    (MultiPointZ, [[(0, 1, 2)], [(10, 11, 12), (20, 21, 22)], [(100, 101, 102), (200, 201, 202), (300, 301, 302)]], True, False,
     [[(0, 1, 2)], [(10, 11, 12), (20, 21, 22)], [(100, 101, 102), (200, 201, 202), (300, 301, 302)]]),
    (MultiPointZ, [[(0, 1, 2)], [(10, 11, 12), (20, 21, 22)], [(100, 101, 102), (200, 201, 202), (300, 301, 302)]], False, True,
     [[(0, 1, nan)], [(10, 11, nan), (20, 21, nan)], [(100, 101, nan), (200, 201, nan), (300, 301, nan)]]),
    (MultiPointZ, [[(0, 1, 2)], [(10, 11, 12), (20, 21, 22)], [(100, 101, 102), (200, 201, 202), (300, 301, 302)]], True, True,
     [[(0, 1, 2, nan)], [(10, 11, 12, nan), (20, 21, 22, nan)], [(100, 101, 102, nan), (200, 201, 202, nan), (300, 301, 302, nan)]]),
    (MultiPointM, [[(0, 1, 3)], [(10, 11, 13), (20, 21, 23)], [(100, 101, 103), (200, 201, 203), (300, 301, 303)]], False, False,
     [[(0, 1)], [(10, 11), (20, 21)], [(100, 101), (200, 201), (300, 301)]]),
    (MultiPointM, [[(0, 1, 3)], [(10, 11, 13), (20, 21, 23)], [(100, 101, 103), (200, 201, 203), (300, 301, 303)]], True, False,
     [[(0, 1, nan)], [(10, 11, nan), (20, 21, nan)], [(100, 101, nan), (200, 201, nan), (300, 301, nan)]]),
    (MultiPointM, [[(0, 1, 3)], [(10, 11, 13), (20, 21, 23)], [(100, 101, 103), (200, 201, 203), (300, 301, 303)]], False, True,
     [[(0, 1, 3)], [(10, 11, 13), (20, 21, 23)], [(100, 101, 103), (200, 201, 203), (300, 301, 303)]]),
    (MultiPointM, [[(0, 1, 3)], [(10, 11, 13), (20, 21, 23)], [(100, 101, 103), (200, 201, 203), (300, 301, 303)]], True, True,
     [[(0, 1, nan, 3)], [(10, 11, nan, 13), (20, 21, nan, 23)], [(100, 101, nan, 103), (200, 201, nan, 203), (300, 301, nan, 303)]]),
    (MultiPointZM, [[(0, 1, 2, 3)], [(10, 11, 12, 13), (20, 21, 22, 23)], [(100, 101, 102, 103), (200, 201, 202, 203), (300, 301, 302, 303)]], False, False,
     [[(0, 1)], [(10, 11), (20, 21)], [(100, 101), (200, 201), (300, 301)]]),
    (MultiPointZM, [[(0, 1, 2, 3)], [(10, 11, 12, 13), (20, 21, 22, 23)], [(100, 101, 102, 103), (200, 201, 202, 203), (300, 301, 302, 303)]], True, False,
     [[(0, 1, 2)], [(10, 11, 12), (20, 21, 22)], [(100, 101, 102), (200, 201, 202), (300, 301, 302)]]),
    (MultiPointZM, [[(0, 1, 2, 3)], [(10, 11, 12, 13), (20, 21, 22, 23)], [(100, 101, 102, 103), (200, 201, 202, 203), (300, 301, 302, 303)]], False, True,
     [[(0, 1, 3)], [(10, 11, 13), (20, 21, 23)], [(100, 101, 103), (200, 201, 203), (300, 301, 303)]]),
    (MultiPointZM, [[(0, 1, 2, 3)], [(10, 11, 12, 13), (20, 21, 22, 23)], [(100, 101, 102, 103), (200, 201, 202, 203), (300, 301, 302, 303)]], True, True,
     [[(0, 1, 2, 3)], [(10, 11, 12, 13), (20, 21, 22, 23)], [(100, 101, 102, 103), (200, 201, 202, 203), (300, 301, 302, 303)]]),
])
def test_multi_point(cls, values, has_z, has_m, expected):
    """
    Test Multi Point Casting
    """
    geoms = [from_wkb(cls(coords, srs_id=WGS84).wkb) for coords in values]
    results = cast_multi_points(geoms, srs_id=WGS84, has_z=has_z, has_m=has_m)
    assert len(results) == 3
    multi_first, multi_second, multi_third = results
    values_first, values_second, values_third = expected
    assert approx(_summer(multi_first.coordinates), nan_ok=True) == _summer([list(v) for v in values_first])
    assert approx(_summer(multi_second.coordinates), nan_ok=True) == _summer([list(v) for v in values_second])
    assert approx(_summer(multi_third.coordinates), nan_ok=True) == _summer([list(v) for v in values_third])
# End test_multi_point function


@mark.parametrize('cls, values, has_z, has_m, expected', [
    (LineString, [(0, 1), (10, 11)], False, False, [(0, 1), (10, 11)]),
    (LineString, [(0, 1), (10, 11)], True, False, [(0, 1, nan), (10, 11, nan)]),
    (LineString, [(0, 1), (10, 11)], False, True, [(0, 1, nan), (10, 11, nan)]),
    (LineString, [(0, 1), (10, 11)], True, True, [(0, 1, nan, nan), (10, 11, nan, nan)]),
    (LineStringZ, [(0, 1, 2), (10, 11, 12)], False, False, [(0, 1), (10, 11)]),
    (LineStringZ, [(0, 1, 2), (10, 11, 12)], True, False, [(0, 1, 2), (10, 11, 12)]),
    (LineStringZ, [(0, 1, 2), (10, 11, 12)], False, True, [(0, 1, nan), (10, 11, nan)]),
    (LineStringZ, [(0, 1, 2), (10, 11, 12)], True, True, [(0, 1, 2, nan), (10, 11, 12, nan)]),
    (LineStringM, [(0, 1, 3), (10, 11, 13)], False, False, [(0, 1), (10, 11)]),
    (LineStringM, [(0, 1, 3), (10, 11, 13)], True, False, [(0, 1, nan), (10, 11, nan)]),
    (LineStringM, [(0, 1, 3), (10, 11, 13)], False, True, [(0, 1, 3), (10, 11, 13)]),
    (LineStringM, [(0, 1, 3), (10, 11, 13)], True, True, [(0, 1, nan, 3), (10, 11, nan, 13)]),
    (LineStringZM, [(0, 1, 2, 3), (10, 11, 12, 13)], False, False, [(0, 1), (10, 11)]),
    (LineStringZM, [(0, 1, 2, 3), (10, 11, 12, 13)], True, False, [(0, 1, 2), (10, 11, 12)]),
    (LineStringZM, [(0, 1, 2, 3), (10, 11, 12, 13)], False, True, [(0, 1, 3), (10, 11, 13)]),
    (LineStringZM, [(0, 1, 2, 3), (10, 11, 12, 13)], True, True, [(0, 1, 2, 3), (10, 11, 12, 13)]),
])
def test_line_string(cls, values, has_z, has_m, expected):
    """
    Test line string casting
    """
    geom = from_wkb(cls(values, srs_id=WGS84).wkb)
    results = cast_linestrings([geom], srs_id=WGS84, has_z=has_z, has_m=has_m)
    assert len(results) == 1
    line, = results
    assert approx(_summer(line.coordinates), nan_ok=True) == _summer([list(v) for v in expected])
# End test_line_string function


@mark.parametrize('cls, values, has_z, has_m, expected', [
    (MultiLineString, [[(0, 0), (1, 1)], [(10, 11), (15, 16)], [(45, 55), (75, 85)], [(4.4, 5.5), (7.7, 8.8)]], False, False,
     [[(0, 0), (1, 1)], [(10, 11), (15, 16)], [(45, 55), (75, 85)], [(4.4, 5.5), (7.7, 8.8)]]),
    (MultiLineString, [[(0, 0), (1, 1)], [(10, 11), (15, 16)], [(45, 55), (75, 85)], [(4.4, 5.5), (7.7, 8.8)]], True, False,
     [[(0, 0, nan), (1, 1, nan)], [(10, 11, nan), (15, 16, nan)], [(45, 55, nan), (75, 85, nan)], [(4.4, 5.5, nan), (7.7, 8.8, nan)]]),
    (MultiLineString, [[(0, 0), (1, 1)], [(10, 11), (15, 16)], [(45, 55), (75, 85)], [(4.4, 5.5), (7.7, 8.8)]], False, True,
     [[(0, 0, nan), (1, 1, nan)], [(10, 11, nan), (15, 16, nan)], [(45, 55, nan), (75, 85, nan)], [(4.4, 5.5, nan), (7.7, 8.8, nan)]]),
    (MultiLineString, [[(0, 0), (1, 1)], [(10, 11), (15, 16)], [(45, 55), (75, 85)], [(4.4, 5.5), (7.7, 8.8)]], True, True,
     [[(0, 0, nan, nan), (1, 1, nan, nan)], [(10, 11, nan, nan), (15, 16, nan, nan)], [(45, 55, nan, nan), (75, 85, nan, nan)], [(4.4, 5.5, nan, nan), (7.7, 8.8, nan, nan)]]),
    (MultiLineStringZ, [[(0, 0, 0), (1, 1, 1)], [(10, 11, 12), (15, 16, 17)], [(45, 55, 65), (75, 85, 95)], [(4.4, 5.5, 6.6), (7.7, 8.8, 9.9)]], False, False,
     [[(0, 0), (1, 1)], [(10, 11), (15, 16)], [(45, 55), (75, 85)], [(4.4, 5.5), (7.7, 8.8)]]),
    (MultiLineStringZ, [[(0, 0, 0), (1, 1, 1)], [(10, 11, 12), (15, 16, 17)], [(45, 55, 65), (75, 85, 95)], [(4.4, 5.5, 6.6), (7.7, 8.8, 9.9)]], True, False,
     [[(0, 0, 0), (1, 1, 1)], [(10, 11, 12), (15, 16, 17)], [(45, 55, 65), (75, 85, 95)], [(4.4, 5.5, 6.6), (7.7, 8.8, 9.9)]]),
    (MultiLineStringZ, [[(0, 0, 0), (1, 1, 1)], [(10, 11, 12), (15, 16, 17)], [(45, 55, 65), (75, 85, 95)], [(4.4, 5.5, 6.6), (7.7, 8.8, 9.9)]], False, True,
     [[(0, 0, nan), (1, 1, nan)], [(10, 11, nan), (15, 16, nan)], [(45, 55, nan), (75, 85, nan)], [(4.4, 5.5, nan), (7.7, 8.8, nan)]]),
    (MultiLineStringZ, [[(0, 0, 0), (1, 1, 1)], [(10, 11, 12), (15, 16, 17)], [(45, 55, 65), (75, 85, 95)], [(4.4, 5.5, 6.6), (7.7, 8.8, 9.9)]], True, True,
     [[(0, 0, 0, nan), (1, 1, 1, nan)], [(10, 11, 12, nan), (15, 16, 17, nan)], [(45, 55, 65, nan), (75, 85, 95, nan)], [(4.4, 5.5, 6.6, nan), (7.7, 8.8, 9.9, nan)]]),
    (MultiLineStringM, [[(0, 0, 0), (1, 1, 1)], [(10, 11, 13), (15, 16, 18)], [(45, 55, 75), (75, 85, 105)], [(4.4, 5.5, 7.7), (7.7, 8.8, 10.1)]], False, False,
     [[(0, 0), (1, 1)], [(10, 11), (15, 16)], [(45, 55), (75, 85)], [(4.4, 5.5), (7.7, 8.8)]]),
    (MultiLineStringM, [[(0, 0, 0), (1, 1, 1)], [(10, 11, 13), (15, 16, 18)], [(45, 55, 75), (75, 85, 105)], [(4.4, 5.5, 7.7), (7.7, 8.8, 10.1)]], True, False,
     [[(0, 0, nan), (1, 1, nan)], [(10, 11, nan), (15, 16, nan)], [(45, 55, nan), (75, 85, nan)], [(4.4, 5.5, nan), (7.7, 8.8, nan)]]),
    (MultiLineStringM, [[(0, 0, 0), (1, 1, 1)], [(10, 11, 13), (15, 16, 18)], [(45, 55, 75), (75, 85, 105)], [(4.4, 5.5, 7.7), (7.7, 8.8, 10.1)]], False, True,
     [[(0, 0, 0), (1, 1, 1)], [(10, 11, 13), (15, 16, 18)], [(45, 55, 75), (75, 85, 105)], [(4.4, 5.5, 7.7), (7.7, 8.8, 10.1)]]),
    (MultiLineStringM, [[(0, 0, 0), (1, 1, 1)], [(10, 11, 13), (15, 16, 18)], [(45, 55, 75), (75, 85, 105)], [(4.4, 5.5, 7.7), (7.7, 8.8, 10.1)]], True, True,
     [[(0, 0, nan, 0), (1, 1, nan, 1)], [(10, 11, nan, 13), (15, 16, nan, 18)], [(45, 55, nan, 75), (75, 85, nan, 105)], [(4.4, 5.5, nan, 7.7), (7.7, 8.8, nan, 10.1)]]),
    (MultiLineStringZM, [[(0, 0, 0, 0), (1, 1, 1, 1)], [(10, 11, 12, 13), (15, 16, 17, 18)], [(45, 55, 65, 75), (75, 85, 95, 105)], [(4.4, 5.5, 6.6, 7.7), (7.7, 8.8, 9.9, 10.1)]], False, False,
     [[(0, 0), (1, 1)], [(10, 11), (15, 16)], [(45, 55), (75, 85)], [(4.4, 5.5), (7.7, 8.8)]]),
    (MultiLineStringZM, [[(0, 0, 0, 0), (1, 1, 1, 1)], [(10, 11, 12, 13), (15, 16, 17, 18)], [(45, 55, 65, 75), (75, 85, 95, 105)], [(4.4, 5.5, 6.6, 7.7), (7.7, 8.8, 9.9, 10.1)]], True, False,
     [[(0, 0, 0), (1, 1, 1)], [(10, 11, 12), (15, 16, 17)], [(45, 55, 65), (75, 85, 95)], [(4.4, 5.5, 6.6), (7.7, 8.8, 9.9)]]),
    (MultiLineStringZM, [[(0, 0, 0, 0), (1, 1, 1, 1)], [(10, 11, 12, 13), (15, 16, 17, 18)], [(45, 55, 65, 75), (75, 85, 95, 105)], [(4.4, 5.5, 6.6, 7.7), (7.7, 8.8, 9.9, 10.1)]], False, True,
     [[(0, 0, 0), (1, 1, 1)], [(10, 11, 13), (15, 16, 18)], [(45, 55, 75), (75, 85, 105)], [(4.4, 5.5, 7.7), (7.7, 8.8, 10.1)]]),
    (MultiLineStringZM, [[(0, 0, 0, 0), (1, 1, 1, 1)], [(10, 11, 12, 13), (15, 16, 17, 18)], [(45, 55, 65, 75), (75, 85, 95, 105)], [(4.4, 5.5, 6.6, 7.7), (7.7, 8.8, 9.9, 10.1)]], True, True,
     [[(0, 0, 0, 0), (1, 1, 1, 1)], [(10, 11, 12, 13), (15, 16, 17, 18)], [(45, 55, 65, 75), (75, 85, 95, 105)], [(4.4, 5.5, 6.6, 7.7), (7.7, 8.8, 9.9, 10.1)]]),
])
def test_multi_line_string(cls, values, has_z, has_m, expected):
    """
    Test multi line string casting
    """
    geom = from_wkb(cls(values, srs_id=WGS84).wkb)
    results = cast_multi_linestrings([geom], srs_id=WGS84, has_z=has_z, has_m=has_m)
    assert len(results) == 1
    multi, = results
    line1, line2, line3, line4 = multi.lines
    values1, values2, values3, values4 = expected

    assert approx(_summer(line1.coordinates), nan_ok=True) == _summer([list(v) for v in values1])
    assert approx(_summer(line2.coordinates), nan_ok=True) == _summer([list(v) for v in values2])
    assert approx(_summer(line3.coordinates), nan_ok=True) == _summer([list(v) for v in values3])
    assert approx(_summer(line4.coordinates), nan_ok=True) == _summer([list(v) for v in values4])
# End test_multi_line_string function


@mark.parametrize('cls, values, has_z, has_m, expected', [
    (Polygon, [[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)], [(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]], False, False,
     [[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)], [(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]]),
    (Polygon, [[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)], [(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]], True, False,
     [[(0, 0, nan), (0, 1, nan), (1, 1, nan), (1, 0, nan), (0, 0, nan)], [(5, 5, nan), (5, 15, nan), (15, 15, nan), (15, 5, nan), (5, 5, nan)]]),
    (Polygon, [[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)], [(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]], False, True,
     [[(0, 0, nan), (0, 1, nan), (1, 1, nan), (1, 0, nan), (0, 0, nan)], [(5, 5, nan), (5, 15, nan), (15, 15, nan), (15, 5, nan), (5, 5, nan)]]),
    (Polygon, [[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)], [(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]], True, True,
     [[(0, 0, nan, nan), (0, 1, nan, nan), (1, 1, nan, nan), (1, 0, nan, nan), (0, 0, nan, nan)], [(5, 5, nan, nan), (5, 15, nan, nan), (15, 15, nan, nan), (15, 5, nan, nan), (5, 5, nan, nan)]]),
    (PolygonZ, [[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)], [(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]], False, False,
     [[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)], [(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]]),
    (PolygonZ, [[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)], [(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]], True, False,
     [[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)], [(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]),
    (PolygonZ, [[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)], [(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]], False, True,
     [[(0, 0, nan), (0, 1, nan), (1, 1, nan), (1, 0, nan), (0, 0, nan)], [(5, 5, nan), (5, 15, nan), (15, 15, nan), (15, 5, nan), (5, 5, nan)]]),
    (PolygonZ, [[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)], [(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]], True, True,
     [[(0, 0, 0, nan), (0, 1, 1, nan), (1, 1, 1, nan), (1, 0, 1, nan), (0, 0, 0, nan)], [(5, 5, 5, nan), (5, 15, 10, nan), (15, 15, 15, nan), (15, 5, 20, nan), (5, 5, 5, nan)]]),
    (PolygonM, [[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)], [(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]], False, False,
     [[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)], [(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]]),
    (PolygonM, [[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)], [(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]], True, False,
     [[(0, 0, nan), (0, 1, nan), (1, 1, nan), (1, 0, nan), (0, 0, nan)], [(5, 5, nan), (5, 15, nan), (15, 15, nan), (15, 5, nan), (5, 5, nan)]]),
    (PolygonM, [[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)], [(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]], False, True,
     [[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)], [(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]),
    (PolygonM, [[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)], [(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]], True, True,
     [[(0, 0, nan, 0), (0, 1, nan, 1), (1, 1, nan, 1), (1, 0, nan, 1), (0, 0, nan, 0)], [(5, 5, nan, 5), (5, 15, nan, 10), (15, 15, nan, 15), (15, 5, nan, 20), (5, 5, nan, 5)]]),
    (PolygonZM, [[(0, 0, 0, 0), (0, 1, 1, 10), (1, 1, 1, 20), (1, 0, 1, 30), (0, 0, 0, 40)], [(5, 5, 5, 50), (5, 15, 10, 60), (15, 15, 15, 70), (15, 5, 20, 80), (5, 5, 5, 90)]], False, False,
     [[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)], [(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]]),
    (PolygonZM, [[(0, 0, 0, 0), (0, 1, 1, 10), (1, 1, 1, 20), (1, 0, 1, 30), (0, 0, 0, 40)], [(5, 5, 5, 50), (5, 15, 10, 60), (15, 15, 15, 70), (15, 5, 20, 80), (5, 5, 5, 90)]], True, False,
     [[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)], [(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]),
    (PolygonZM, [[(0, 0, 0, 0), (0, 1, 1, 10), (1, 1, 1, 20), (1, 0, 1, 30), (0, 0, 0, 40)], [(5, 5, 5, 50), (5, 15, 10, 60), (15, 15, 15, 70), (15, 5, 20, 80), (5, 5, 5, 90)]], False, True,
     [[(0, 0, 0), (0, 1, 10), (1, 1, 20), (1, 0, 30), (0, 0, 40)], [(5, 5, 50), (5, 15, 60), (15, 15, 70), (15, 5, 80), (5, 5, 90)]]),
    (PolygonZM, [[(0, 0, 0, 0), (0, 1, 1, 10), (1, 1, 1, 20), (1, 0, 1, 30), (0, 0, 0, 40)], [(5, 5, 5, 50), (5, 15, 10, 60), (15, 15, 15, 70), (15, 5, 20, 80), (5, 5, 5, 90)]], True, True,
     [[(0, 0, 0, 0), (0, 1, 1, 10), (1, 1, 1, 20), (1, 0, 1, 30), (0, 0, 0, 40)], [(5, 5, 5, 50), (5, 15, 10, 60), (15, 15, 15, 70), (15, 5, 20, 80), (5, 5, 5, 90)]]),
])
def test_polygon(cls, values, has_z, has_m, expected):
    """
    Test polygon casting
    """
    geom = from_wkb(cls(values, srs_id=WGS84).wkb)
    results = cast_polygons([geom], srs_id=WGS84, has_z=has_z, has_m=has_m)
    assert len(results) == 1
    poly, = results
    ring1, ring2 = poly.rings
    values1, values2 = expected

    assert approx(_summer(ring1.coordinates), nan_ok=True) == _summer([list(v) for v in values1])
    assert approx(_summer(ring2.coordinates), nan_ok=True) == _summer([list(v) for v in values2])
# End test_polygon function


@mark.parametrize('cls, values, has_z, has_m, expected', [
    (MultiPolygon, [[[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]], [[(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]]], False, False,
     [[[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]], [[(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]]]),
    (MultiPolygon, [[[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]], [[(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]]], True, False,
     [[[(0, 0, nan), (0, 1, nan), (1, 1, nan), (1, 0, nan), (0, 0, nan)]], [[(5, 5, nan), (5, 15, nan), (15, 15, nan), (15, 5, nan), (5, 5, nan)]]]),
    (MultiPolygon, [[[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]], [[(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]]], False, True,
     [[[(0, 0, nan), (0, 1, nan), (1, 1, nan), (1, 0, nan), (0, 0, nan)]], [[(5, 5, nan), (5, 15, nan), (15, 15, nan), (15, 5, nan), (5, 5, nan)]]]),
    (MultiPolygon, [[[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]], [[(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]]], True, True,
     [[[(0, 0, nan, nan), (0, 1, nan, nan), (1, 1, nan, nan), (1, 0, nan, nan), (0, 0, nan, nan)]], [[(5, 5, nan, nan), (5, 15, nan, nan), (15, 15, nan, nan), (15, 5, nan, nan), (5, 5, nan, nan)]]]),
    (MultiPolygonZ, [[[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)]], [[(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]], False, False,
     [[[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]], [[(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]]]),
    (MultiPolygonZ, [[[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)]], [[(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]], True, False,
     [[[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)]], [[(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]]),
    (MultiPolygonZ, [[[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)]], [[(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]], False, True,
     [[[(0, 0, nan), (0, 1, nan), (1, 1, nan), (1, 0, nan), (0, 0, nan)]], [[(5, 5, nan), (5, 15, nan), (15, 15, nan), (15, 5, nan), (5, 5, nan)]]]),
    (MultiPolygonZ, [[[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)]], [[(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]], True, True,
     [[[(0, 0, 0, nan), (0, 1, 1, nan), (1, 1, 1, nan), (1, 0, 1, nan), (0, 0, 0, nan)]], [[(5, 5, 5, nan), (5, 15, 10, nan), (15, 15, 15, nan), (15, 5, 20, nan), (5, 5, 5, nan)]]]),
    (MultiPolygonM, [[[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)]], [[(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]], False, False,
     [[[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]], [[(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]]]),
    (MultiPolygonM, [[[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)]], [[(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]], True, False,
     [[[(0, 0, nan), (0, 1, nan), (1, 1, nan), (1, 0, nan), (0, 0, nan)]], [[(5, 5, nan), (5, 15, nan), (15, 15, nan), (15, 5, nan), (5, 5, nan)]]]),
    (MultiPolygonM, [[[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)]], [[(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]], False, True,
     [[[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)]], [[(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]]),
    (MultiPolygonM, [[[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)]], [[(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]], True, True,
     [[[(0, 0, nan, 0), (0, 1, nan, 1), (1, 1, nan, 1), (1, 0, nan, 1), (0, 0, nan, 0)]], [[(5, 5, nan, 5), (5, 15, nan, 10), (15, 15, nan, 15), (15, 5, nan, 20), (5, 5, nan, 5)]]]),
    (MultiPolygonZM, [[[(0, 0, 0, 10), (0, 1, 1, 20), (1, 1, 1, 30), (1, 0, 1, 40), (0, 0, 0, 50)]], [[(5, 5, 5, 60), (5, 15, 10, 70), (15, 15, 15, 80), (15, 5, 20, 90), (5, 5, 5, 100)]]], False, False,
     [[[(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]], [[(5, 5), (5, 15), (15, 15), (15, 5), (5, 5)]]]),
    (MultiPolygonZM, [[[(0, 0, 0, 10), (0, 1, 1, 20), (1, 1, 1, 30), (1, 0, 1, 40), (0, 0, 0, 50)]], [[(5, 5, 5, 60), (5, 15, 10, 70), (15, 15, 15, 80), (15, 5, 20, 90), (5, 5, 5, 100)]]], True, False,
     [[[(0, 0, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 0)]], [[(5, 5, 5), (5, 15, 10), (15, 15, 15), (15, 5, 20), (5, 5, 5)]]]),
    (MultiPolygonZM, [[[(0, 0, 0, 10), (0, 1, 1, 20), (1, 1, 1, 30), (1, 0, 1, 40), (0, 0, 0, 50)]], [[(5, 5, 5, 60), (5, 15, 10, 70), (15, 15, 15, 80), (15, 5, 20, 90), (5, 5, 5, 100)]]], False, True,
     [[[(0, 0, 10), (0, 1, 20), (1, 1, 30), (1, 0, 40), (0, 0, 50)]], [[(5, 5, 60), (5, 15, 70), (15, 15, 80), (15, 5, 90), (5, 5, 100)]]]),
    (MultiPolygonZM, [[[(0, 0, 0, 10), (0, 1, 1, 20), (1, 1, 1, 30), (1, 0, 1, 40), (0, 0, 0, 50)]], [[(5, 5, 5, 60), (5, 15, 10, 70), (15, 15, 15, 80), (15, 5, 20, 90), (5, 5, 5, 100)]]], True, True,
     [[[(0, 0, 0, 10), (0, 1, 1, 20), (1, 1, 1, 30), (1, 0, 1, 40), (0, 0, 0, 50)]], [[(5, 5, 5, 60), (5, 15, 10, 70), (15, 15, 15, 80), (15, 5, 20, 90), (5, 5, 5, 100)]]]),
])
def test_multi_polygon(cls, values, has_z, has_m, expected):
    """
    Test multi polygon casting
    """
    geom = from_wkb(cls(values, srs_id=WGS84).wkb)
    results = cast_multi_polygons([geom], srs_id=WGS84, has_z=has_z, has_m=has_m)
    assert len(results) == 1
    multi, = results
    poly1, poly2 = multi.polygons
    ring1, = poly1.rings
    ring2, = poly2.rings
    values1, values2 = expected

    assert approx(_summer(ring1.coordinates), nan_ok=True) == sum(_summer([list(v) for v in values1]), ())
    assert approx(_summer(ring2.coordinates), nan_ok=True) == sum(_summer([list(v) for v in values2]), ())
# End test_multi_polygon function


if __name__ == '__main__':  # pragma: no cover
    pass
