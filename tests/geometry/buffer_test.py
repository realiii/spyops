# -*- coding: utf-8 -*-
"""
Tests for Buffering
"""


from functools import partial

from fudgeo.enumeration import ShapeType
from numpy import array
from pyproj import CRS
from pytest import mark
from shapely import LineString, Polygon, Point, MultiPolygon, MultiPoint
from shapely.constructive import buffer
from shapely.geometry.multilinestring import MultiLineString

from spyops.geometry.buffer import (
    _get_side_settings, _equidistant_transformers, _to_multi,
    _dissolve_polygons, _outside_only, geodesic_buffer, planar_buffer)
from spyops.shared.enumeration import EndOption, SideOption

pytestmark = [mark.geometry]


@mark.parametrize('side, expected', [
    (SideOption.FULL, (1, False)),
    (SideOption.LEFT, (1, True)),
    (SideOption.RIGHT, (-1, True)),
    (SideOption.ONLY_OUTSIDE, (1, False)),
])
def test_get_side_settings(side, expected):
    """
    Test get side settings
    """
    assert _get_side_settings(side) == expected
# End test_get_side_settings function


@mark.parametrize('from_crs, to_crs, expected', [
    (CRS(4326), CRS(4326), None),
    (CRS(4326), CRS(4617), partial),
])
def test_equidistant_transformers(from_crs, to_crs, expected):
    """
    Test _equidistant_transformers
    """
    to_eqd, from_eqd = _equidistant_transformers(from_crs, to_crs, shape_type=ShapeType.polygon)
    if expected is None:
        assert to_eqd is expected
        assert from_eqd is expected
    else:
        assert isinstance(to_eqd, expected)
        assert isinstance(from_eqd, expected)
# End test_equidistant_transformers function


@mark.parametrize('geoms', [
    (Polygon(), Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])),
    (Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]), MultiPolygon([[[(0, 0), (0, 1), (1, 1), (1, 0)]]])),
    (MultiPolygon([]), MultiPolygon([Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])])),
])
def test_to_multi(geoms):
    """
    Test to multi
    """
    geoms = array(geoms)
    _to_multi(geoms)
    assert all(isinstance(geom, MultiPolygon) for geom in geoms)
# End test_to_multi function


@mark.parametrize('geoms', [
    (Polygon(), Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])),
    (Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]), MultiPolygon([[[(0, 0), (0, 1), (1, 1), (1, 0)]]])),
    (MultiPolygon([]), MultiPolygon([Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])])),
])
def test_dissolve_polygons(geoms):
    """
    Test _dissolve_polygons
    """
    geoms = _dissolve_polygons(array(geoms), xy_tolerance=None)
    assert len(geoms) == 2
    assert all(isinstance(geom, MultiPolygon) for geom in geoms)
# End test_dissolve_polygons function


class TestOutsideOnly:
    """
    Test Outside Only
    """
    @staticmethod
    def _get_data():
        """
        Get Data
        """
        distances = array([1, 2, -3])
        poly1 = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
        poly2 = Polygon([(10, 10), (10, 11), (11, 11), (11, 10)])
        poly3 = Polygon([(100, 100), (100, 110), (110, 110), (110, 100)])
        geoms = array([poly1, poly2, poly3])
        polygons = buffer(geoms, distance=distances)
        return geoms, polygons, polygons.copy(), distances
    # End _get_data method

    @mark.parametrize('side_option', [
        SideOption.FULL,
        SideOption.LEFT,
        SideOption.RIGHT,
    ])
    def test_options(self, side_option):
        """
        Test FULL
        """
        geoms, polygons, copied, distances = self._get_data()
        results = _outside_only(
            geoms, polygons=polygons, distances=distances,
            side_option=side_option, xy_tolerance=None)
        assert all(c == r for c, r in zip(copied, results))
    # End test_full method

    def test_only(self):
        """
        Test Only Outside
        """
        geoms, polygons, copied, distances = self._get_data()
        results = _outside_only(
            geoms, polygons=polygons, distances=distances,
            side_option=SideOption.ONLY_OUTSIDE, xy_tolerance=None)
        assert all(c != r for c, r in zip(copied, results))
        assert all(len(p.interiors) == 1 for p in results)
        *outers, inner = results
        assert all(c.area > r.area for c, r in zip(copied, outers))
        assert (inner.area + copied[-1].area) == geoms[-1].area
    # End test_only method
# End TestOutsideOnly class


class TestPlanarBuffer:
    """
    Test Planar Buffer
    """
    @mark.parametrize('side_option', [
        SideOption.FULL,
        SideOption.ONLY_OUTSIDE,
    ])
    @mark.parametrize('end_option', [
        EndOption.ROUND,
        EndOption.FLAT,
        EndOption.SQUARE,
    ])
    def test_polygons(self, side_option, end_option):
        """
        Test Polygons
        """
        distances = array([1, 2, -3])
        poly1 = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
        poly2 = Polygon([(10, 10), (10, 11), (11, 11), (11, 10)])
        poly3 = Polygon([(100, 100), (100, 110), (110, 110), (110, 100)])
        geoms = array([poly1, poly2, poly3])
        results = planar_buffer(
            geoms, distances=distances, side_option=side_option,
            end_option=end_option, resolution=16, xy_tolerance=None)
        assert all(isinstance(r, MultiPolygon) for r in results)
    # End test_polygons method

    @mark.parametrize('side_option', [
        SideOption.FULL,
        SideOption.ONLY_OUTSIDE,
    ])
    @mark.parametrize('end_option', [
        EndOption.ROUND,
        EndOption.FLAT,
        EndOption.SQUARE,
    ])
    def test_multipolygons(self, side_option, end_option):
        """
        Test MultiPolygons
        """
        distances = array([1, 2, -3])
        poly1 = MultiPolygon([Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])])
        poly2 = MultiPolygon([Polygon([(10, 10), (10, 11), (11, 11), (11, 10)])])
        poly3 = MultiPolygon([Polygon([(100, 100), (100, 110), (110, 110), (110, 100)])])
        geoms = array([poly1, poly2, poly3])
        results = planar_buffer(
            geoms, distances=distances, side_option=side_option,
            end_option=end_option, resolution=16, xy_tolerance=None)
        assert all(isinstance(r, MultiPolygon) for r in results)
    # End test_multipolygons method

    @mark.parametrize('side_option', [
        SideOption.FULL,
        SideOption.LEFT,
        SideOption.RIGHT,
    ])
    @mark.parametrize('end_option', [
        EndOption.ROUND,
        EndOption.FLAT,
        EndOption.SQUARE,
    ])
    def test_lines(self, side_option, end_option):
        """
        Test lines
        """
        distances = array([1, 2, -3])
        line1 = LineString([(0, 0), (0, 1), (1, 1), (1, 0)])
        line2 = LineString([(10, 10), (10, 11), (11, 11), (11, 10)])
        line3 = LineString([(100, 100), (100, 110), (110, 110), (110, 100)])
        geoms = array([line1, line2, line3])
        results = planar_buffer(
            geoms, distances=distances, side_option=side_option,
            end_option=end_option, resolution=16, xy_tolerance=None)
        assert all(isinstance(r, MultiPolygon) for r in results)
    # End test_lines method

    @mark.parametrize('side_option', [
        SideOption.FULL,
        SideOption.LEFT,
        SideOption.RIGHT,
    ])
    @mark.parametrize('end_option', [
        EndOption.ROUND,
        EndOption.FLAT,
        EndOption.SQUARE,
    ])
    def test_multilines(self, side_option, end_option):
        """
        Test MultiLines
        """
        distances = array([1, 2, -3])
        line1 = MultiLineString([LineString([(0, 0), (0, 1), (1, 1), (1, 0)])])
        line2 = MultiLineString([LineString([(10, 10), (10, 11), (11, 11), (11, 10)])])
        line3 = MultiLineString([LineString([(100, 100), (100, 110), (110, 110), (110, 100)])])
        geoms = array([line1, line2, line3])
        results = planar_buffer(
            geoms, distances=distances, side_option=side_option,
            end_option=end_option, resolution=16, xy_tolerance=None)
        assert all(isinstance(r, MultiPolygon) for r in results)
    # End test_multilines method

    @mark.parametrize('side_option', [
        SideOption.FULL,
    ])
    @mark.parametrize('end_option', [
        EndOption.ROUND,
        EndOption.FLAT,
        EndOption.SQUARE,
    ])
    def test_multipoints(self, side_option, end_option):
        """
        Test multipoints
        """
        distances = array([1, 2, -3])
        mp1 = MultiPoint([(0, 0), (0, 1), (1, 1), (1, 0)])
        mp2 = MultiPoint([(10, 10), (10, 11), (11, 11), (11, 10)])
        mp3 = MultiPoint([(100, 100), (100, 110), (110, 110), (110, 100)])
        geoms = array([mp1, mp2, mp3])
        results = planar_buffer(
            geoms, distances=distances, side_option=side_option,
            end_option=end_option, resolution=16, xy_tolerance=None)
        assert all(isinstance(r, MultiPolygon) for r in results)
    # End test_multipoints method

    @mark.parametrize('side_option', [
        SideOption.FULL,
    ])
    @mark.parametrize('end_option', [
        EndOption.ROUND,
        EndOption.FLAT,
        EndOption.SQUARE,
    ])
    def test_points(self, side_option, end_option):
        """
        Test points
        """
        distances = array([1, 2, -3])
        pt1 = Point(0, 0)
        pt2 = Point(10, 10)
        pt3 = Point(100, 100)
        geoms = array([pt1, pt2, pt3])
        results = planar_buffer(
            geoms, distances=distances, side_option=side_option,
            end_option=end_option, resolution=16, xy_tolerance=None)
        assert all(isinstance(r, MultiPolygon) for r in results)
    # End test_points method
# End TestPlanarBuffer class


class TestGeodesicBuffer:
    """
    Test Geodesic Buffer
    """
    @mark.parametrize('side_option', [
        SideOption.FULL,
        SideOption.ONLY_OUTSIDE,
    ])
    @mark.parametrize('end_option', [
        EndOption.ROUND,
        EndOption.FLAT,
        EndOption.SQUARE,
    ])
    def test_polygons_wgs84(self, side_option, end_option):
        """
        Test Polygons using WGS84
        """
        crs = CRS(4326)
        distances = array([1000, 2000, -3000])
        poly1 = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
        poly2 = Polygon([(-115, 50), (-115, 60), (-110, 60), (-110, 50)])
        poly3 = Polygon([(-45, 45), (-45, 55), (-55, 55), (-55, 45)])
        geoms = array([poly1, poly2, poly3])
        results = geodesic_buffer(
            geoms, distances=distances,
            crs=crs, shape_type=ShapeType.polygon,
            side_option=side_option, end_option=end_option,
            resolution=16, xy_tolerance=None)
        assert all(isinstance(r, MultiPolygon) for r in results)
    # End test_polygons_wgs84 method

    @mark.parametrize('side_option', [
        SideOption.FULL,
        SideOption.ONLY_OUTSIDE,
    ])
    @mark.parametrize('end_option', [
        EndOption.ROUND,
        EndOption.FLAT,
        EndOption.SQUARE,
    ])
    def test_polygons_world_mercator(self, side_option, end_option):
        """
        Test Polygons using World Mercator
        """
        crs = CRS(3857)
        distances = array([1000, 2000, -3000])
        poly1 = Polygon([(0, 0), (0, 111_300), (111_300, 111_300), (111_300, 0)])
        poly2 = Polygon([(-12_801_000, 6_446_000), (-12_801_000, 8_400_000),
                         (-12_245_000, 8_400_000), (-12_245_000, 6_446_000)])
        poly3 = Polygon([(-5_010_000, 5_622_000), (-5_010_000, 7_362_000),
                         (-6_123_000, 7_362_000), (-6_123_000, 5_622_000)])
        geoms = array([poly1, poly2, poly3])
        results = geodesic_buffer(
            geoms, distances=distances,
            crs=crs, shape_type=ShapeType.polygon,
            side_option=side_option, end_option=end_option,
            resolution=16, xy_tolerance=None)
        assert all(isinstance(r, MultiPolygon) for r in results)
    # End test_polygons_world_mercator method

    @mark.parametrize('side_option', [
        SideOption.FULL,
        SideOption.ONLY_OUTSIDE,
    ])
    @mark.parametrize('end_option', [
        EndOption.ROUND,
        EndOption.FLAT,
        EndOption.SQUARE,
    ])
    def test_polygons_utm_z12_blm(self, side_option, end_option):
        """
        Test Polygons using UTM Zone 12N (BLM)
        """
        crs = CRS(4412)
        distances = array([1000, -3000])
        poly1 = Polygon([(865_000, 16_362_000), (906_000, 17_455_000),
                         (1_395_000, 17_443_000), (1_382_000, 16_350_000)])
        geoms = array([poly1, poly1])
        results = geodesic_buffer(
            geoms, distances=distances,
            crs=crs, shape_type=ShapeType.polygon,
            side_option=side_option, end_option=end_option,
            resolution=16, xy_tolerance=None)
        assert all(isinstance(r, MultiPolygon) for r in results)
    # End test_polygons_utm_z12_blm method
# End TestGeodesicBuffer class


if __name__ == '__main__':  # pragma: no cover
    pass
