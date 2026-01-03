# -*- coding: utf-8 -*-
"""
Tests for Geometry Module
"""

from fudgeo.geometry.point import Point
from pytest import approx, mark, raises
from shapely import (
    MultiPoint as ShapelyMultiPoint, Point as ShapelyPoint,
    Polygon as ShapelyPolygon, MultiPolygon as ShapelyMultiPolygon,
    MultiLineString as ShapelyMultiLineString)

from geomio.shared.exception import OperationsError
from geomio.shared.geometry import (
    build_multi, check_dimension, check_polygon,
    extent_from_feature_class,
    get_geometry_dimension, geometry_config)


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
    assert config.fudgeo_cls is Point
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


def test_check_dimension():
    """
    Test check_dimension
    """
    assert check_dimension(0, name_a='aa', b=1, name_b='bb') is None
    assert check_dimension(1, name_a='aa', b=1, name_b='bb') is None
    assert check_dimension(1, name_a='aa', b=2, name_b='bb') is None
    assert check_dimension(2, name_a='aa', b=2, name_b='bb') is None
    with raises(OperationsError):
        check_dimension(2, name_a='aa', b=1, name_b='bb')
# End test_check_dimension function


if __name__ == '__main__':  # pragma: no cover
    pass
