# -*- coding: utf-8 -*-
"""
Tests for Geometry Module
"""

from fudgeo.geometry.point import Point
from pytest import approx, mark, raises
from shapely import (
    MultiLineString as ShapelyMultiLineString, MultiPoint as ShapelyMultiPoint,
    MultiPolygon as ShapelyMultiPolygon, Point as ShapelyPoint,
    Polygon as ShapelyPolygon)

from gisworks.shared.enumeration import OutputTypeOption
from gisworks.shared.exception import OperationsError
from gisworks.shared.geometry import (
    _use_boundary_factory, _as_lines, _nada, build_multi, check_dimension,
    check_polygon, extent_from_feature_class, geometry_config,
    get_geometry_converters, get_geometry_dimension)


pytestmark = [mark.geometry]


def test_build_multi_polygon(inputs):
    """
    Test build multi polygon
    """
    fc = inputs['updater_a']
    assert len(fc) == 5
    polygon = build_multi(fc)
    assert isinstance(polygon, ShapelyMultiPolygon)
    assert approx(polygon.bounds, abs=0.0001) == (
        6.74573, 46.13702, 16.47727, 52.52511)
# End test_build_multi_polygon function


def test_build_multi_line_string(world_features):
    """
    Test build multi line string
    """
    fc = world_features['rivers_l']
    assert len(fc) == 136
    line = build_multi(fc)
    assert isinstance(line, ShapelyMultiLineString)
    assert approx(line.bounds, abs=0.0001) == (-164.88743, -36.96944, 160.76359, 71.39248)
# End test_build_multi_line_string function


def test_build_multi_point(world_features):
    """
    Test build multi point
    """
    fc = world_features['airports_p']
    assert len(fc) == 3500
    line = build_multi(fc)
    assert isinstance(line, ShapelyMultiPoint)
    assert approx(line.bounds, abs=0.0001) == (-177.38063, -54.84327, 178.55922, 78.24611)
# End test_build_multi_line_string function


def test_geometry_config(inputs, world_features):
    """
    Test geometry config
    """
    fc = world_features['cities_p']
    config = geometry_config(fc)
    assert config.geometry_cls is Point
    assert config.is_multi is False
    assert config.filter_types == (ShapelyPoint, ShapelyMultiPoint)
    assert config.srs_id == 4326
# End test_geometry_config function


@mark.parametrize('name, expected', [
    ('admin_a', (-180.0, -90, 180, 83.6654911040001)),
    ('airports_p', (-177.38063597699997, -54.84327804999998, 178.5592279430001, 78.24611103500007)),
    ('roads_l', (-166.52854919433594, -54.97826385498047, 178.56739807128906, 70.48219299316406)),
])
def test_extent_from_feature_class(world_features, name, expected):
    """
    Test extent from feature class
    """
    fc = world_features[name]
    extent = extent_from_feature_class(fc)
    assert approx(extent, abs=0.000001) == expected
# End test_extent_from_feature_class function


def test_extent_from_feature_class_sans_extent(crs_geopackage):
    """
    Test extent from feature class sans extent in table
    """
    fc = crs_geopackage['test_32138_p']
    extent = extent_from_feature_class(fc)
    assert approx(extent, abs=0.1) == (971616.26, 2039110.0, 1023849.47, 2087677.50)
# End test_extent_from_feature_class_sans_extent function


@mark.parametrize('polygon, type_', [
    (ShapelyPolygon([(0, 0), (0, 1), (1, 1), (1, 0)]), ShapelyPolygon),
    (ShapelyPolygon([(0, 0), (1, 1), (1, 2), (1, 1), (0, 0)]), type(None)),
    (ShapelyPolygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)]), ShapelyMultiPolygon),
    (ShapelyMultiPolygon([ShapelyPolygon([(0, 0), (0, 1), (1, 1), (1, 0)]),
                          ShapelyPolygon([(0, 0), (0, 1), (1, 1), (1, 0)])]), ShapelyPolygon),
    (ShapelyMultiPolygon([ShapelyPolygon([(0, 0), (0, 1), (1, 1), (1, 0)]),
                          ShapelyPolygon([(10, 10), (10, 11), (11, 11), (11, 10)])]), ShapelyMultiPolygon),
    (ShapelyPolygon([(0, 0), (0, 0), (0, 0), (0, 0)]), type(None)),
])
def test_check_polygon(polygon, type_):
    """
    Test check_polygon
    """
    assert isinstance(check_polygon(polygon), type_)
# End test_check_polygon function


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
            check_dimension(a, name_a='aa', b=b, name_b='bb', same_dimension=is_same)
    else:
        assert check_dimension(a, name_a='aa', b=b, name_b='bb', same_dimension=is_same) is None
# End test_check_dimension function


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
    (OutputTypeOption.SAME, 'utmzone_sparse_a', 'intersect_a', (_nada, _nada)),
    (OutputTypeOption.LINE, 'utmzone_sparse_a', 'intersect_a', (_as_lines, _as_lines)),
    (OutputTypeOption.POINT, 'utmzone_sparse_a', 'intersect_a', (_as_lines, _as_lines)),
    (OutputTypeOption.SAME, 'rivers_portion_l', 'intersect_a', (_nada, _nada)),
    (OutputTypeOption.LINE, 'rivers_portion_l', 'intersect_a', (_nada, _nada)),
    (OutputTypeOption.POINT, 'rivers_portion_l', 'intersect_a', (_nada, _as_lines)),
    (OutputTypeOption.SAME, 'river_p', 'intersect_a', (_nada, _nada)),
    (OutputTypeOption.POINT, 'river_p', 'intersect_a', (_nada, _nada)),

    (OutputTypeOption.SAME, 'rivers_portion_l', 'rivers_portion_l', (_nada, _nada)),
    (OutputTypeOption.LINE, 'rivers_portion_l', 'rivers_portion_l', (_nada, _nada)),
    (OutputTypeOption.POINT, 'rivers_portion_l', 'rivers_portion_l', (_nada, _nada)),
    (OutputTypeOption.POINT, 'river_p', 'rivers_portion_l', (_nada, _nada)),

    (OutputTypeOption.SAME, 'river_p', 'river_p', (_nada, _nada)),
    (OutputTypeOption.POINT, 'river_p', 'river_p', (_nada, _nada)),
])
def test_get_geometry_converters(inputs, output_type_option, source_name, operator_name, expected):
    """
    Test get_geometry_converters
    """
    source = inputs[source_name]
    operator = inputs[operator_name]
    assert get_geometry_converters(source, operator=operator, output_type_option=output_type_option) == expected
# End test_get_geometry_converters function


if __name__ == '__main__':  # pragma: no cover
    pass
