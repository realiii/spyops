# -*- coding: utf-8 -*-
"""
Extent tests
"""

from pytest import approx, mark
from shapely.geometry.linestring import LineString
from shapely.geometry.multilinestring import MultiLineString
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon

from spyops.geometry.extent import (
    extent_from_feature_class, extent_maximum,
    extent_minimum)

pytestmark = [mark.geometry]


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


@mark.parametrize('geom, expected', [
    (LineString([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)]), (0., 0., 0.)),
    (MultiLineString([LineString([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)])]), (0., 0., 0.)),
    (Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]]), (0., 0., 0.)),
    (MultiPolygon([Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]])]), (0., 0., 0.)),
])
def test_extent_minimum(geom, expected):
    """
    Test extent minimum
    """
    assert approx(extent_minimum([geom], has_z=True, has_m=False)[0], abs=0.001) == expected
# End test_extent_minimum function


@mark.parametrize('geom, expected', [
    (LineString([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)]), (10., 10., 6.)),
    (MultiLineString([LineString([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)])]), (10., 10., 6.)),
    (Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]]), (10., 10., 6.)),
    (MultiPolygon([Polygon([(0, 0, 0), (0, 10, 2), (10, 10, 5), (10, 0, 6)], holes=[[(2, 2, 0), (2, 4, 0), (4, 4, 0), (4, 2, 0)]])]), (10., 10., 6.)),
])
def test_extent_maximum(geom, expected):
    """
    Test extent maximum
    """
    assert approx(extent_maximum([geom], has_z=True, has_m=False)[0], abs=0.001) == expected
# End test_extent_maximum function


if __name__ == '__main__':  # pragma: no cover
    pass
