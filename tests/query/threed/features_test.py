# -*- coding: utf-8 -*-
"""
Tests for the Features Query Classes
"""

from math import log, nan
from warnings import catch_warnings, simplefilter

from fudgeo import FeatureClass, Field
from fudgeo.enumeration import FieldType, ShapeType
from numpy import cumsum, isfinite
from pyproj import CRS
from pyproj.crs import CompoundCRS
from pytest import mark, approx
from shapely.geometry.linestring import LineString
from shapely.geometry.multilinestring import MultiLineString
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon
from shapely.measurement import length

from spyops.crs.constant import WGS84
from spyops.crs.unit import DecimalDegrees, Feet, Kilometers, Meters
from spyops.crs.util import crs_from_srs
from spyops.geometry.convert import GEOMETRY_AS_MULTILINE
from spyops.geometry.util import get_geoms
from spyops.query.threed.features import (
    QueryGeneratePointsAlong3DLinesDistance,
    QueryGeneratePointsAlong3DLinesField,
    QueryGeneratePointsAlong3DLinesPercentage)
from spyops.shared.enumeration import DistanceTypeOption
from spyops.shared.exception import DistanceCalculationWarning


pytestmark = [mark.sampling, mark.query, mark.management]


class TestQueryGeneratePointsAlong3DLinesPercentage:
    """
    Test Query Generate Points Along Lines using Percentage
    """
    @staticmethod
    def _get_query(ntdb_zm_small):
        source = ntdb_zm_small['transmission_l']
        return QueryGeneratePointsAlong3DLinesPercentage(
            source, target=None, placement=33, include_ends=False,
            where_clause='', distance_type=DistanceTypeOption.GEODESIC)
    # End _get_query method

    @mark.parametrize('epsg_code, expected', [
        (4326, 1),
        (6654, 1),
        (8370, 1),
        (7407, 1),
    ])
    def test_get_z_factor(self, ntdb_zm_small, epsg_code, expected):
        """
        Test get Z factor
        """
        crs = CRS(epsg_code)
        query = self._get_query(ntdb_zm_small)
        assert query._get_z_factor(crs) == expected
    # End test_get_z_factor method

    @mark.parametrize('horiz_code, vert_code, expected', [
        (32076, 115809, 1),
        (32076, 115807, 3.2808),
        (32628, 115809, 0.3048),
        (32628, 115807, 1),
        (4326, 115809, 0.3048),
        (4326, 115807, 1),
    ])
    def test_mixed_units_get_z_factor(self, ntdb_zm_small, horiz_code, vert_code, expected):
        """
        Test mixed units
        """
        crs = CRS(horiz_code)
        vertical_crs = CRS.from_authority('ESRI', vert_code)
        compound = CompoundCRS(
            name=f'{crs.name} + {vertical_crs.name}',
            components=[crs, vertical_crs])
        query = self._get_query(ntdb_zm_small)
        assert approx(query._get_z_factor(compound), abs=0.0001) == expected
    # End test_mixed_units_get_z_factor method

    def test_is_2d(self, ntdb_zm_small):
        """
        Test is 2D
        """
        assert not self._get_query(ntdb_zm_small)._is_2d
    # End test_is_2d method

    def test_get_unique_fields(self, ntdb_zm_small):
        """
        Test get unique fields
        """
        query = self._get_query(ntdb_zm_small)
        assert [f.name for f in query._get_unique_fields()] == ['ORIG_FID', 'SEQ_NUM', 'ALONG']
    # End test_get_unique_fields method

    def test_get_select_fields(self, ntdb_zm_small):
        """
        Test get select fields
        """
        query = self._get_query(ntdb_zm_small)
        assert [f.name for f in query._get_select_fields(query.source)] == ['fid', 'fid']
    # End test_get_select_fields method

    def test_get_target_shape_type(self, ntdb_zm_small):
        """
        Test get target shape type
        """
        query = self._get_query(ntdb_zm_small)
        assert query._get_target_shape_type() == ShapeType.point
    # End test_get_target_shape_type method

    def test_field_names_and_count(self, ntdb_zm_small):
        """
        Test field names and count
        """
        query = self._get_query(ntdb_zm_small)
        count, insert, select = query._field_names_and_count(query.source)
        assert count == 4
        assert insert == 'SHAPE, ORIG_FID, SEQ_NUM, ALONG'
        assert select == 'SHAPE "[LineString]", fid, fid'
    # End test_field_names_and_count method

    @mark.parametrize('name, distance_type, expected', [
        ('transmission_l', DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_l', DistanceTypeOption.PLANAR, DistanceTypeOption.GEODESIC),
        ('transmission_utm11_l', DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_utm11_l', DistanceTypeOption.PLANAR, DistanceTypeOption.PLANAR),
    ])
    def test_distance_type(self, ntdb_zm_small, name, distance_type, expected):
        """
        Test distance type
        """
        source = ntdb_zm_small[name]
        query = QueryGeneratePointsAlong3DLinesPercentage(
            source, target=None, placement=0.5, include_ends=False,
            where_clause='', distance_type=distance_type)
        assert query.distance_type == expected
    # End test_distance_type method

    @mark.parametrize('shape_type, geom, expected', [
        (ShapeType.linestring, LineString([(0, 0), (0, 20)]), (6.6, 13.2, 19.8)),
        (ShapeType.multi_linestring, LineString([(0, 0), (0, 20)]), (6.6, 13.2, 19.8)),
        (ShapeType.multi_linestring, MultiLineString(
            [LineString([(0, 0), (0, 10)]), LineString([(0, 10), (0, 20)])]), (6.6, 13.2, 19.8)),
        (ShapeType.polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), (6.6, 13.2, 19.8)),
        (ShapeType.multi_polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), (6.6, 13.2, 19.8)),
        (ShapeType.multi_polygon, MultiPolygon(
            [Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]),
             Polygon([(10, 10), (10, 15), (15, 15), (15, 10)])]), (13.2, 26.4, 39.6)),
    ])
    def test_get_values(self, ntdb_zm_small, shape_type, geom, expected):
        """
        Test get values
        """
        query = self._get_query(ntdb_zm_small)
        lines = get_geoms(GEOMETRY_AS_MULTILINE[shape_type](geom))
        lengths = cumsum(length(lines))
        crs = crs_from_srs(query.spatial_reference_system)
        result = query._get_values(
            lines, total_length=lengths[-1], crs=crs, distance=None)
        assert approx(result, abs=0.1) == expected
    # End test_get_values method

    @mark.parametrize('placement, expected', [
        (10, 0),
        (nan, 1),
        (0, 1),
        (-10, 1),
        (100, 1),
        (110, 1),
    ])
    def test_get_values_counter(self, placement, expected):
        """
        Test get values, checking counter is incremented
        """
        query = QueryGeneratePointsAlong3DLinesPercentage(
            None, target=None, placement=placement,
            include_ends=False, where_clause='',
            distance_type=DistanceTypeOption.GEODESIC)
        query._get_values([], total_length=123, crs=WGS84, distance=None)
        assert query._counter == expected
    # End test_get_values_counter method

    def test_show_warning(self, ntdb_zm_small):
        """
        Test show warning
        """
        query = self._get_query(ntdb_zm_small)
        with catch_warnings(record=True) as ws:
            simplefilter('always')
            query.show_warning()
            assert len(ws) == 0
        query._counter = 1
        with catch_warnings(record=True) as ws:
            simplefilter('always')
            query.show_warning()
            assert len(ws) == 1
            w, = ws
            assert issubclass(w.category, DistanceCalculationWarning)
    # End test_show_warning method

    def test_insert(self, ntdb_zm_small, mem_gpkg,):
        """
        Test insert
        """
        source = ntdb_zm_small['transmission_l']
        target = FeatureClass(mem_gpkg, 'output_fc')
        query = QueryGeneratePointsAlong3DLinesPercentage(
            source, target=target, placement=33, include_ends=False,
            where_clause='', distance_type=DistanceTypeOption.GEODESIC)
        assert 'INTO output_fc(SHAPE, ORIG_FID, SEQ_NUM, ALONG)' in query.insert
    # End test_insert method

    @mark.parametrize('distance_type, name, expected', [
        (DistanceTypeOption.PLANAR, 'transmission_10tm_z_l', (129.27, 258.54, 387.82, 389.52, 779.05, 1168.58, 62.03, 124.06, 186.10, 2102.76, 4205.53, 6308.30)),
        (DistanceTypeOption.PLANAR, 'transmission_10tm_zm_l', (129.27, 258.54, 387.82, 389.52, 779.05, 1168.58, 62.03, 124.06, 186.10, 2102.76, 4205.53, 6308.30)),
        (DistanceTypeOption.PLANAR, 'transmission_6654_z_l', (129.37, 258.75, 388.13, 389.84, 779.69, 1169.54, 62.08, 124.16, 186.25, 2104.50, 4209.00, 6313.50)),
        (DistanceTypeOption.PLANAR, 'transmission_6654_zm_l', (129.37, 258.75, 388.13, 389.84, 779.69, 1169.54, 62.08, 124.16, 186.25, 2104.50, 4209.00, 6313.50)),
        (DistanceTypeOption.PLANAR, 'transmission_utm11_z_l', (129.37, 258.75, 388.13, 389.84, 779.69, 1169.54, 62.08, 124.16, 186.25, 2104.50, 4209.00, 6313.50)),
        (DistanceTypeOption.PLANAR, 'transmission_utm11_zm_l', (129.37, 258.75, 388.13, 389.84, 779.69, 1169.54, 62.08, 124.16, 186.25, 2104.50, 4209.00, 6313.50)),
        (DistanceTypeOption.GEODESIC, 'transmission_10tm_z_l', (129.42, 258.84, 388.27, 389.97, 779.94, 1169.92, 62.10, 124.20, 186.31, 2104.41, 4208.83, 6313.25)),
        (DistanceTypeOption.GEODESIC, 'transmission_10tm_zm_l', (129.42, 258.84, 388.27, 389.97, 779.94, 1169.92, 62.10, 124.20, 186.31, 2104.41, 4208.83, 6313.25)),
        (DistanceTypeOption.GEODESIC, 'transmission_6654_z_l', (129.42, 258.84, 388.26, 389.97, 779.94, 1169.92, 62.10, 124.20, 186.30, 2104.40, 4208.81, 6313.22)),
        (DistanceTypeOption.GEODESIC, 'transmission_6654_zm_l', (129.42, 258.84, 388.26, 389.97, 779.94, 1169.92, 62.10, 124.20, 186.30, 2104.40, 4208.81, 6313.22)),
        (DistanceTypeOption.GEODESIC, 'transmission_utm11_z_l', (129.42, 258.84, 388.26, 389.97, 779.94, 1169.92, 62.10, 124.20, 186.30, 2104.40, 4208.81, 6313.22)),
        (DistanceTypeOption.GEODESIC, 'transmission_utm11_zm_l', (129.42, 258.84, 388.26, 389.97, 779.94, 1169.92, 62.10, 124.20, 186.30, 2104.40, 4208.81, 6313.22)),
    ])
    def test_generate_features_projected(self, ntdb_zm_small, mem_gpkg, distance_type, name, expected):
        """
        Test generate_features using projected source
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        placement = 33
        include = False
        query = QueryGeneratePointsAlong3DLinesPercentage(
            source, target=target, placement=placement,
            include_ends=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_features(features)
            assert len(points) == (int((100 / placement)) + (2 * int(include))) * count
            points, attrs = zip(*points)
            fids, seqs, alongs = zip(*attrs)
            assert all(isinstance(p, Point) for p in points)
            assert set(fids) == {1, 2, 3, 4}
            assert all(p.has_z == source.has_z for p in points)
            if source.has_z:
                assert isfinite([p.z for p in points]).all()
            assert all(p.has_m == source.has_m for p in points)
            if source.has_m:
                assert isfinite([p.m for p in points]).all()
            assert seqs == (1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3)
            assert approx(alongs, abs=0.1) == expected
            assert all(p.x > 1000 for p in points)
            assert all(p.y > 1000 for p in points)
    # End test_generate_features_projected method

    @mark.parametrize('name, expected', [
        ('transmission_z_l', (129.42, 258.84, 388.26, 389.97, 779.94, 1169.92, 62.10, 124.20, 186.30, 2104.40, 4208.81, 6313.22)),
        ('transmission_zm_l', (129.42, 258.84, 388.26, 389.97, 779.94, 1169.92, 62.10, 124.20, 186.30, 2104.40, 4208.81, 6313.22)),
        ('transmission_4617_z_l', (129.42, 258.84, 388.26, 389.97, 779.94, 1169.92, 62.10, 124.20, 186.30, 2104.40, 4208.81, 6313.22)),
        ('transmission_4617_zm_l', (129.42, 258.84, 388.26, 389.97, 779.94, 1169.92, 62.10, 124.20, 186.30, 2104.40, 4208.81, 6313.22)),
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC
    ])
    def test_generate_features_geographic(self, ntdb_zm_small, mem_gpkg, name, expected, distance_type):
        """
        Test generate_features using geographic source
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        placement = 33
        include = False
        query = QueryGeneratePointsAlong3DLinesPercentage(
            source, target=target, placement=placement,
            include_ends=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_features(features)
            assert len(points) == (int((100 / placement)) + (2 * int(include))) * count
            points, attrs = zip(*points)
            fids, seqs, alongs = zip(*attrs)
            assert all(isinstance(p, Point) for p in points)
            assert set(fids) == {1, 2, 3, 4}
            assert all(p.has_z == source.has_z for p in points)
            if source.has_z:
                assert isfinite([p.z for p in points]).all()
            assert all(p.has_m == source.has_m for p in points)
            if source.has_m:
                assert isfinite([p.m for p in points]).all()
            assert seqs == (1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3)
            assert approx(alongs, abs=0.1) == expected
            assert all(p.x < 180 for p in points)
            assert all(p.y < 90 for p in points)
    # End test_generate_features_geographic method

    @mark.parametrize('distance_type, name, expected', [
        (DistanceTypeOption.PLANAR, 'transmission_10tm_z_l', (0.0, 129.27, 258.54, 387.82, 391.74, 0.0, 389.52, 779.05, 1168.58, 1180.38, 0.0, 62.03, 124.06, 186.10, 187.98, 0.0, 2102.76, 4205.53, 6308.30, 6372.02)),
        (DistanceTypeOption.GEODESIC, 'transmission_10tm_z_l', (0.0, 129.42, 258.84, 388.27, 392.19, 0.0, 389.97, 779.94, 1169.92, 1181.74, 0.0, 62.10, 124.20, 186.31, 188.19, 0.0, 2104.41, 4208.83, 6313.25, 6377.02)),
        (DistanceTypeOption.PLANAR, 'transmission_z_l', (0.0, 129.42, 258.84, 388.26, 392.18, 0.0, 389.97, 779.94, 1169.92, 1181.74, 0.0, 62.10, 124.20, 186.30, 188.18, 0.0, 2104.40, 4208.81, 6313.22, 6376.99)),
        (DistanceTypeOption.GEODESIC, 'transmission_z_l', (0.0, 129.42, 258.84, 388.26, 392.18, 0.0, 389.97, 779.94, 1169.92, 1181.74, 0.0, 62.10, 124.20, 186.30, 188.18, 0.0, 2104.40, 4208.81, 6313.22, 6376.99)),
    ])
    def test_generate_features_include_ends(self, ntdb_zm_small, mem_gpkg, distance_type, name, expected):
        """
        Test generate points include ends
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        placement = 33
        include = True
        query = QueryGeneratePointsAlong3DLinesPercentage(
            source, target=target, placement=placement,
            include_ends=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_features(features)
            assert len(points) == (int((100 / placement)) + (2 * int(include))) * count
            points, attrs = zip(*points)
            fids, seqs, alongs = zip(*attrs)
            assert all(isinstance(p, Point) for p in points)
            assert set(fids) == {1, 2, 3, 4}
            assert all(p.has_z == source.has_z for p in points)
            if source.has_z:
                assert isfinite([p.z for p in points]).all()
            assert all(p.has_m == source.has_m for p in points)
            if source.has_m:
                assert isfinite([p.m for p in points]).all()
            assert seqs == (1, 2, 3, 4, 5) * count
            assert approx(alongs, abs=0.1) == expected
    # End test_generate_features_include_ends method
# End TestQueryGeneratePointsAlong3DLinesPercentage class


class TestQueryGeneratePointsAlong3DLinesDistance:
    """
    Test Query Generate Points Along Lines 3D using Distance
    """
    @mark.parametrize('name, unit, distance_type, expected', [
        ('transmission_z_l', Meters(200), DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_z_l', Meters(200), DistanceTypeOption.PLANAR, DistanceTypeOption.GEODESIC),
        ('transmission_utm11_z_l', Meters(200), DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_utm11_z_l', Meters(200), DistanceTypeOption.PLANAR, DistanceTypeOption.PLANAR),
        ('transmission_z_l', DecimalDegrees(0.1), DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_z_l', DecimalDegrees(0.1), DistanceTypeOption.PLANAR, DistanceTypeOption.GEODESIC),
        ('transmission_utm11_z_l', DecimalDegrees(0.1), DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_utm11_z_l', DecimalDegrees(0.1), DistanceTypeOption.PLANAR, DistanceTypeOption.GEODESIC),
    ])
    def test_distance_type(self, ntdb_zm_small, name, unit, distance_type, expected):
        """
        Test distance type
        """
        source = ntdb_zm_small[name]
        query = QueryGeneratePointsAlong3DLinesDistance(
            source, target=None, placement=unit, include_ends=False,
            where_clause='', distance_type=distance_type)
        assert query.distance_type == expected
    # End test_distance_type method

    @mark.parametrize('shape_type, geom, expected', [
        (ShapeType.linestring, LineString([(0, 0), (0, 20)]), (5, 10, 15)),
        (ShapeType.multi_linestring, LineString([(0, 0), (0, 20)]), (5, 10, 15)),
        (ShapeType.multi_linestring, MultiLineString([LineString([(0, 0), (0, 10)]), LineString([(0, 10), (0, 20)])]), (5, 10, 15)),
        (ShapeType.polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), (5, 10, 15)),
        (ShapeType.multi_polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), (5, 10, 15)),
        (ShapeType.multi_polygon, MultiPolygon(
            [Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]),
             Polygon([(10, 10), (10, 15), (15, 15), (15, 10)])]), (5, 10, 15, 20, 25, 30, 35)),
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC
    ])
    def test_get_values_linear_unit(self, ntdb_zm_small, shape_type, distance_type, geom, expected):
        """
        Test get values using linear unit
        """
        unit = Meters(5)
        source = ntdb_zm_small['transmission_10tm_l']
        query = QueryGeneratePointsAlong3DLinesDistance(
            source, target=None, placement=unit, include_ends=False,
            where_clause='', distance_type=distance_type)
        lines = get_geoms(GEOMETRY_AS_MULTILINE[shape_type](geom))
        lengths = cumsum(length(lines))
        crs = crs_from_srs(query.spatial_reference_system)
        result = query._get_values(
            lines, total_length=lengths[-1], crs=crs, distance=None)
        assert approx(result, abs=0.1) == expected
    # End test_get_values_linear_unit method

    @mark.parametrize('shape_type, geom, expected', [
        (ShapeType.linestring, LineString([(0, 0), (0, 20)]), (5.54, 11.09, 16.64)),
        (ShapeType.multi_linestring, LineString([(0, 0), (0, 20)]), (5.54, 11.09, 16.64)),
        (ShapeType.multi_linestring, MultiLineString([LineString([(0, 0), (0, 10)]), LineString([(0, 10), (0, 20)])]), (5.54, 11.09, 16.64)),
        (ShapeType.polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), (5.54, 11.09, 16.64)),
        (ShapeType.multi_polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), (5.54, 11.09, 16.64)),
        (ShapeType.multi_polygon, MultiPolygon(
            [Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]),
             Polygon([(10, 10), (10, 15), (15, 15), (15, 10)])]),
         (5.54, 11.09, 16.64, 22.18, 27.73, 33.28, 38.83)),
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC
    ])
    def test_get_values_dd(self, ntdb_zm_small, shape_type, distance_type, geom, expected):
        """
        Test get values using decimal degrees
        """
        unit = DecimalDegrees(0.00005)
        source = ntdb_zm_small['transmission_10tm_l']
        query = QueryGeneratePointsAlong3DLinesDistance(
            source, target=None, placement=unit, include_ends=False,
            where_clause='', distance_type=distance_type)
        lines = get_geoms(GEOMETRY_AS_MULTILINE[shape_type](geom))
        lengths = cumsum(length(lines))
        crs = crs_from_srs(query.spatial_reference_system)
        result = query._get_values(
            lines, total_length=lengths[-1], crs=crs, distance=None)
        assert approx(result, abs=0.1) == expected
    # End test_get_values_dd method

    @mark.parametrize('placement, expected', [
        (Meters(10), 0),
        (Meters(nan), 1),
        (Meters(0), 1),
        (Meters(-10), 1),
        (Meters(150), 1),
    ])
    def test_get_values_counter(self, ntdb_zm_small, placement, expected):
        """
        Test get values, checking counter is incremented
        """
        source = ntdb_zm_small['transmission_10tm_l']
        query = QueryGeneratePointsAlong3DLinesDistance(
            source, target=None, placement=placement,
            include_ends=False, where_clause='',
            distance_type=DistanceTypeOption.GEODESIC)
        query._get_values([], total_length=123, crs=WGS84, distance=None)
        assert query._counter == expected
    # End test_get_values_counter method

    def test_show_warning(self, ntdb_zm_small):
        """
        Test show warning
        """
        source = ntdb_zm_small['transmission_10tm_l']
        query = QueryGeneratePointsAlong3DLinesDistance(
            source, target=None, placement=Meters(10),
            include_ends=False, where_clause='',
            distance_type=DistanceTypeOption.GEODESIC)
        with catch_warnings(record=True) as ws:
            simplefilter('always')
            query.show_warning()
            assert len(ws) == 0
        query._counter = 1
        with catch_warnings(record=True) as ws:
            simplefilter('always')
            query.show_warning()
            assert len(ws) == 1
            w, = ws
            assert issubclass(w.category, DistanceCalculationWarning)
    # End test_show_warning method

    @mark.parametrize('distance_type, placement, name', [
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_10tm_z_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_10tm_zm_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_6654_z_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_6654_zm_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_utm11_z_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_utm11_zm_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_10tm_z_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_10tm_zm_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_6654_z_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_6654_zm_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_utm11_z_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_utm11_zm_l'),
    ])
    def test_generate_features_projected_linear(self, ntdb_zm_small, mem_gpkg, distance_type, placement, name):
        """
        Test generate_features using projected source with linear unit
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = False
        query = QueryGeneratePointsAlong3DLinesDistance(
            source, target=target, placement=placement,
            include_ends=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_features(features)
            points, attrs = zip(*points)
            fids, seqs, alongs = zip(*attrs)
            assert all(isinstance(p, Point) for p in points)
            assert set(fids) == {1, 2, 4}
            assert all(p.has_z == source.has_z for p in points)
            if source.has_z:
                assert isfinite([p.z for p in points]).all()
            assert all(p.has_m == source.has_m for p in points)
            if source.has_m:
                assert isfinite([p.m for p in points]).all()
            expected_seqs = (
                1, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31)
            assert seqs == expected_seqs
            assert approx(alongs, abs=0.1) == [placement.meters * i for i in expected_seqs]
            assert all(p.x > 1000 for p in points)
            assert all(p.y > 1000 for p in points)
    # End test_generate_features_projected_linear method

    @mark.parametrize('distance_type, placement, name', [
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_z_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_zm_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_4617_z_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_4617_zm_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_z_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_zm_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_4617_z_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_4617_zm_l'),
    ])
    def test_generate_features_geographic_linear(self, ntdb_zm_small, mem_gpkg, distance_type, placement, name):
        """
        Test generate_features using geographic source with linear unit
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = False
        query = QueryGeneratePointsAlong3DLinesDistance(
            source, target=target, placement=placement,
            include_ends=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_features(features)
            points, attrs = zip(*points)
            fids, seqs, alongs = zip(*attrs)
            assert all(isinstance(p, Point) for p in points)
            assert set(fids) == {1, 2, 4}
            assert all(p.has_z == source.has_z for p in points)
            if source.has_z:
                assert isfinite([p.z for p in points]).all()
            assert all(p.has_m == source.has_m for p in points)
            if source.has_m:
                assert isfinite([p.m for p in points]).all()
            expected_seqs = (
                1, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31)
            assert seqs == expected_seqs
            assert approx(alongs, abs=0.1) == [placement.meters * i for i in expected_seqs]
            assert all(p.x < 1000 for p in points)
            assert all(p.y < 1000 for p in points)
    # End test_generate_features_geographic_linear method

    @mark.parametrize('distance_type, placement, name', [
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_10tm_z_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_10tm_zm_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_6654_z_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_6654_zm_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_utm11_z_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_utm11_zm_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_10tm_z_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_10tm_zm_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_6654_z_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_6654_zm_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_utm11_z_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_utm11_zm_l'),
    ])
    def test_generate_features_projected_dd(self, ntdb_zm_small, mem_gpkg, distance_type, placement, name):
        """
        Test generate_features using projected source with decimal degrees
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = False
        query = QueryGeneratePointsAlong3DLinesDistance(
            source, target=target, placement=placement,
            include_ends=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_features(features)
            points, attrs = zip(*points)
            fids, seqs, alongs = zip(*attrs)
            assert all(isinstance(p, Point) for p in points)
            assert set(fids) == {1, 2, 4}
            assert all(p.has_z == source.has_z for p in points)
            if source.has_z:
                assert isfinite([p.z for p in points]).all()
            assert all(p.has_m == source.has_m for p in points)
            if source.has_m:
                assert isfinite([p.m for p in points]).all()
            expected_seqs = (
                1, 1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23)
            assert seqs == expected_seqs
            assert approx(alongs, abs=2) == [s * 272 for s in expected_seqs]
            assert all(p.x > 1000 for p in points)
            assert all(p.y > 1000 for p in points)
    # End test_generate_features_projected_dd method

    @mark.parametrize('distance_type, placement, name', [
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_z_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_zm_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_4617_z_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_4617_zm_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_z_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_zm_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_4617_z_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_4617_zm_l'),
    ])
    def test_generate_features_geographic_dd(self, ntdb_zm_small, mem_gpkg, distance_type, placement, name):
        """
        Test generate_features using geographic source with decimal degrees
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = False
        query = QueryGeneratePointsAlong3DLinesDistance(
            source, target=target, placement=placement,
            include_ends=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_features(features)
            points, attrs = zip(*points)
            fids, seqs, alongs = zip(*attrs)
            assert all(isinstance(p, Point) for p in points)
            assert set(fids) == {1, 2, 4}
            assert all(p.has_z == source.has_z for p in points)
            if source.has_z:
                assert isfinite([p.z for p in points]).all()
            assert all(p.has_m == source.has_m for p in points)
            if source.has_m:
                assert isfinite([p.m for p in points]).all()
            expected_seqs = (
                1, 1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23)
            assert seqs == expected_seqs
            assert approx(alongs, abs=2) == [s * 272 for s in expected_seqs]
            assert all(p.x < 1000 for p in points)
            assert all(p.y < 1000 for p in points)
    # End test_generate_features_geographic_dd method

    @mark.parametrize('distance_type, name, expected', [
        (DistanceTypeOption.PLANAR, 'transmission_10tm_z_l', (0.0, 391.74, 0.0, 1180.39, 0.0, 187.98, 0.0, 6372.03)),
        (DistanceTypeOption.GEODESIC, 'transmission_10tm_z_l', (0.0, 392.19, 0.0, 1181.74, 0.0, 188.19, 0.0, 6377.02)),
        (DistanceTypeOption.PLANAR, 'transmission_z_l', (0.0, 392.18, 0.0, 1181.74, 0.0, 188.18, 0.0, 6376.99)),
        (DistanceTypeOption.GEODESIC, 'transmission_z_l', (0.0, 392.18, 0.0, 1181.74, 0.0, 188.18, 0.0, 6376.99)),
    ])
    def test_generate_features_include_ends(self, ntdb_zm_small, mem_gpkg, distance_type, name, expected):
        """
        Test generate points include only ends by using a large
        placement distance
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = True
        query = QueryGeneratePointsAlong3DLinesDistance(
            source, target=target, placement=Kilometers(10),
            include_ends=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_features(features)
            assert len(points) == 2 * count
            points, attrs = zip(*points)
            fids, seqs, alongs = zip(*attrs)
            assert all(isinstance(p, Point) for p in points)
            assert set(fids) == {1, 2, 3, 4}
            assert all(p.has_z == source.has_z for p in points)
            if source.has_z:
                assert isfinite([p.z for p in points]).all()
            assert all(p.has_m == source.has_m for p in points)
            if source.has_m:
                assert isfinite([p.m for p in points]).all()
            assert seqs == (1, 2) * count
            assert approx(alongs, abs=0.1) == expected
    # End test_generate_features_include_ends method
# End TestQueryGeneratePointsAlong3DLinesDistance class


class TestQueryGeneratePointsAlong3DLinesField:
    """
    Test Query Generate Points Along Lines 3D using Field
    """
    @mark.parametrize('name, distance_type, expected', [
        ('transmission_z_l', DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_z_l', DistanceTypeOption.PLANAR, DistanceTypeOption.GEODESIC),
        ('transmission_lcc_z_l', DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_lcc_z_l', DistanceTypeOption.PLANAR, DistanceTypeOption.PLANAR),
    ])
    @mark.parametrize('field', [
        Field('SINGLE_VALUE', data_type=FieldType.real),
        Field('SINGLE_UNIT', data_type=FieldType.text),
    ])
    def test_distance_type_singles(self, along_field, name, distance_type, expected, field):
        """
        Test distance type for single value and single unit
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 4'
        query = QueryGeneratePointsAlong3DLinesField(
            source, target=None, placement=field, include_ends=False,
            where_clause=where_clause, distance_type=distance_type)
        assert query.distance_type == expected
    # End test_distance_type_singles method

    @mark.parametrize('name, distance_type, expected', [
        ('transmission_z_l', DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_z_l', DistanceTypeOption.PLANAR, DistanceTypeOption.GEODESIC),
        ('transmission_lcc_z_l', DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_lcc_z_l', DistanceTypeOption.PLANAR, DistanceTypeOption.GEODESIC),
    ])
    @mark.parametrize('field', [
        Field('SINGLE_DD', data_type=FieldType.text),
        Field('DISTANCES', data_type=FieldType.text),
    ])
    def test_distance_type_dd_and_distances(self, along_field, name, distance_type, expected, field):
        """
        Test distance type for single dd and distances
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 4'
        query = QueryGeneratePointsAlong3DLinesField(
            source, target=None, placement=field, include_ends=False,
            where_clause=where_clause, distance_type=distance_type)
        assert query.distance_type == expected
    # End test_distance_type_dd_and_distances method

    @mark.parametrize('shape_type, geom, expected', [
        (ShapeType.linestring, LineString([(0, 0), (0, 20)]), (5, 10, 15)),
        (ShapeType.multi_linestring, LineString([(0, 0), (0, 20)]), (5, 10, 15)),
        (ShapeType.multi_linestring, MultiLineString([LineString([(0, 0), (0, 10)]), LineString([(0, 10), (0, 20)])]), (5, 10, 15)),
        (ShapeType.polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), (5, 10, 15)),
        (ShapeType.multi_polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), (5, 10, 15)),
        (ShapeType.multi_polygon, MultiPolygon(
            [Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]),
             Polygon([(10, 10), (10, 15), (15, 15), (15, 10)])]), (5, 10, 15, 20, 25, 30, 35)),
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC
    ])
    @mark.parametrize('distance, field', [
        (5, Field('SINGLE_VALUE', data_type=FieldType.real)),
        ('5 m', Field('SINGLE_UNIT', data_type=FieldType.text)),
    ])
    def test_get_values_linear_unit(self, along_field, shape_type, geom, expected, distance_type, distance, field):
        """
        Test get values using linear unit
        """
        source = along_field['transmission_lcc_l']
        where_clause = f'{source.primary_key_field.name} <= 4'
        query = QueryGeneratePointsAlong3DLinesField(
            source, target=None, placement=field, include_ends=False,
            where_clause=where_clause, distance_type=distance_type)
        lines = get_geoms(GEOMETRY_AS_MULTILINE[shape_type](geom))
        lengths = cumsum(length(lines))
        crs = crs_from_srs(query.spatial_reference_system)
        result = query._get_values(
            lines, total_length=lengths[-1], crs=crs, distance=distance)
        assert approx(result, abs=0.1) == expected
    # End test_get_values_linear_unit method

    @mark.parametrize('shape_type, geom, expected', [
        (ShapeType.linestring, LineString([(0, 0), (0, 20)]), (4.91, 9.82, 14.73, 19.64)),
        (ShapeType.multi_linestring, LineString([(0, 0), (0, 20)]), (4.91, 9.82, 14.73, 19.64)),
        (ShapeType.multi_linestring, MultiLineString([LineString([(0, 0), (0, 10)]), LineString([(0, 10), (0, 20)])]), (4.91, 9.82, 14.73, 19.64)),
        (ShapeType.polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), (4.91, 9.82, 14.73, 19.64)),
        (ShapeType.multi_polygon, Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), (4.91, 9.82, 14.73, 19.64)),
        (ShapeType.multi_polygon, MultiPolygon(
            [Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]),
             Polygon([(10, 10), (10, 15), (15, 15), (15, 10)])]),
         (4.91, 9.82, 14.73, 19.64, 24.55, 29.45, 34.37, 39.28)),
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC
    ])
    @mark.parametrize('distance, field', [
        ('0.00005 dd', Field('SINGLE_DD', data_type=FieldType.text)),
    ])
    def test_get_values_dd(self, along_field, shape_type, geom, expected, distance_type, distance, field):
        """
        Test get values using decimal degrees
        """
        source = along_field['transmission_lcc_l']
        where_clause = f'{source.primary_key_field.name} <= 4'
        query = QueryGeneratePointsAlong3DLinesField(
            source, target=None, placement=field, include_ends=False,
            where_clause=where_clause, distance_type=distance_type)
        lines = get_geoms(GEOMETRY_AS_MULTILINE[shape_type](geom))
        lengths = cumsum(length(lines))
        crs = crs_from_srs(query.spatial_reference_system)
        result = query._get_values(
            lines, total_length=lengths[-1], crs=crs, distance=distance)
        assert approx(result, abs=0.1) == expected
    # End test_get_values_dd method

    @mark.parametrize('field_name, distance, expected', [
        ('SINGLE_VALUE', 10, 0),
        ('SINGLE_UNIT', '10 m', 0),
        ('DISTANCES', '10 m;20 ft', 0),
        ('SINGLE_VALUE', nan, 1),
        ('SINGLE_VALUE', None, 1),
        ('SINGLE_UNIT', None, 1),
        ('SINGLE_UNIT', '', 1),
        ('SINGLE_UNIT', 'nan', 1),
        ('SINGLE_UNIT', ' ', 1),
        ('DISTANCES', ';', 2),
        ('DISTANCES', ' ; ', 2),
        ('DISTANCES', '-10 m;20 ft', 1),
        ('DISTANCES', '0 m;20 ft', 1),
    ])
    def test_get_values_counter(self, along_field, field_name, distance, expected):
        """
        Test get values, checking counter is incremented
        """
        if field_name == 'SINGLE_VALUE':
            data_type = FieldType.real
        else:
            data_type = FieldType.text
        field = Field(field_name, data_type=data_type)
        source = along_field['transmission_lcc_l']
        where_clause = f'{source.primary_key_field.name} <= 4'
        query = QueryGeneratePointsAlong3DLinesField(
            source, target=None, placement=field,
            include_ends=False, where_clause=where_clause,
            distance_type=DistanceTypeOption.GEODESIC)
        query._get_values([], total_length=123, crs=WGS84, distance=distance)
        assert query._counter == expected
    # End test_get_values_counter method

    @mark.parametrize('distance_type, name', [
        (DistanceTypeOption.PLANAR, 'transmission_lcc_z_l'),
        (DistanceTypeOption.PLANAR, 'transmission_lcc_zm_l'),
        (DistanceTypeOption.PLANAR, 'transmission_6654_z_l'),
        (DistanceTypeOption.PLANAR, 'transmission_6654_zm_l'),
        (DistanceTypeOption.GEODESIC, 'transmission_lcc_z_l'),
        (DistanceTypeOption.GEODESIC, 'transmission_lcc_zm_l'),
        (DistanceTypeOption.GEODESIC, 'transmission_6654_z_l'),
        (DistanceTypeOption.GEODESIC, 'transmission_6654_zm_l'),
    ])
    @mark.parametrize('field', [
        Field('SINGLE_VALUE', data_type=FieldType.real),
        Field('SINGLE_UNIT', data_type=FieldType.text),
    ])
    def test_generate_features_projected_linear(self, along_field, mem_gpkg, distance_type, field, name):
        """
        Test generate_features using projected source with linear unit
        """
        count = 4
        source = along_field[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = False
        query = QueryGeneratePointsAlong3DLinesField(
            source, target=target, placement=field,
            include_ends=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_features(features)
            points, attrs = zip(*points)
            fids, seqs, alongs = zip(*attrs)
            assert all(isinstance(p, Point) for p in points)
            assert set(fids) == {1, 2, 4}
            assert all(p.has_z == source.has_z for p in points)
            if source.has_z:
                assert isfinite([p.z for p in points]).all()
            assert all(p.has_m == source.has_m for p in points)
            if source.has_m:
                assert isfinite([p.m for p in points]).all()
            expected_seqs = (
                1, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31)
            assert seqs == expected_seqs
            assert approx(alongs, abs=0.1) == [200 * i for i in expected_seqs]
            assert all(log(abs(p.x)) > 3 for p in points)
            assert all(log(abs(p.y)) > 3 for p in points)
    # End test_generate_features_projected_linear method

    @mark.parametrize('distance_type, name', [
        (DistanceTypeOption.PLANAR, 'transmission_z_l'),
        (DistanceTypeOption.PLANAR, 'transmission_zm_l'),
        (DistanceTypeOption.GEODESIC, 'transmission_z_l'),
        (DistanceTypeOption.GEODESIC, 'transmission_zm_l'),
    ])
    @mark.parametrize('field', [
        Field('SINGLE_UNIT', data_type=FieldType.text),
    ])
    def test_generate_features_geographic_linear(self, along_field, mem_gpkg, distance_type, name, field):
        """
        Test generate_features using geographic source with linear unit
        """
        count = 4
        source = along_field[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = False
        query = QueryGeneratePointsAlong3DLinesField(
            source, target=target, placement=field,
            include_ends=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_features(features)
            points, attrs = zip(*points)
            fids, seqs, alongs = zip(*attrs)
            assert all(isinstance(p, Point) for p in points)
            assert set(fids) == {1, 2, 4}
            assert all(p.has_z == source.has_z for p in points)
            if source.has_z:
                assert isfinite([p.z for p in points]).all()
            assert all(p.has_m == source.has_m for p in points)
            if source.has_m:
                assert isfinite([p.m for p in points]).all()
            expected_seqs = (
                1, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28,
                29, 30, 31)
            assert seqs == expected_seqs
            assert approx(alongs, abs=0.1) == [200 * i for i in expected_seqs]
            assert all(p.x < 1000 for p in points)
            assert all(p.y < 1000 for p in points)
    # End test_generate_features_geographic_linear method

    @mark.parametrize('distance_type, name', [
        (DistanceTypeOption.PLANAR, 'transmission_lcc_z_l'),
        (DistanceTypeOption.PLANAR, 'transmission_lcc_zm_l'),
        (DistanceTypeOption.PLANAR, 'transmission_6654_z_l'),
        (DistanceTypeOption.PLANAR, 'transmission_6654_zm_l'),
        (DistanceTypeOption.GEODESIC, 'transmission_lcc_z_l'),
        (DistanceTypeOption.GEODESIC, 'transmission_lcc_zm_l'),
        (DistanceTypeOption.GEODESIC, 'transmission_6654_z_l'),
        (DistanceTypeOption.GEODESIC, 'transmission_6654_zm_l'),
    ])
    @mark.parametrize('field', [
        Field('SINGLE_DD', data_type=FieldType.text),
    ])
    def test_generate_features_projected_dd(self, along_field, mem_gpkg, distance_type, name, field):
        """
        Test generate_features using projected source with decimal degrees
        """
        count = 4
        source = along_field[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = False
        query = QueryGeneratePointsAlong3DLinesField(
            source, target=target, placement=field,
            include_ends=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_features(features)
            points, attrs = zip(*points)
            fids, seqs, alongs = zip(*attrs)
            assert all(isinstance(p, Point) for p in points)
            assert set(fids) == {1, 2, 4}
            assert all(p.has_z == source.has_z for p in points)
            if source.has_z:
                assert isfinite([p.z for p in points]).all()
            assert all(p.has_m == source.has_m for p in points)
            if source.has_m:
                assert isfinite([p.m for p in points]).all()
            expected_seqs = (
                1, 1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23)
            assert seqs == expected_seqs
            assert approx(alongs, abs=2) == [s * 272 for s in expected_seqs]
            assert all(log(abs(p.x)) > 3 for p in points)
            assert all(log(abs(p.y)) > 3 for p in points)
    # End test_generate_features_projected_dd method

    @mark.parametrize('distance_type, name', [
        (DistanceTypeOption.PLANAR, 'transmission_z_l'),
        (DistanceTypeOption.PLANAR, 'transmission_zm_l'),
        (DistanceTypeOption.GEODESIC, 'transmission_z_l'),
        (DistanceTypeOption.GEODESIC, 'transmission_zm_l'),
    ])
    @mark.parametrize('field', [
        Field('SINGLE_VALUE', data_type=FieldType.real),
        Field('SINGLE_DD', data_type=FieldType.text),
    ])
    def test_generate_features_geographic_dd(self, along_field, mem_gpkg, distance_type, name, field):
        """
        Test generate_features using geographic source with decimal degrees
        """
        count = 4
        source = along_field[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = False
        query = QueryGeneratePointsAlong3DLinesField(
            source, target=target, placement=field,
            include_ends=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_features(features)
            points, attrs = zip(*points)
            fids, seqs, alongs = zip(*attrs)
            assert all(isinstance(p, Point) for p in points)
            assert set(fids) == {1, 2, 4}
            assert all(p.has_z == source.has_z for p in points)
            if source.has_z:
                assert isfinite([p.z for p in points]).all()
            assert all(p.has_m == source.has_m for p in points)
            if source.has_m:
                assert isfinite([p.m for p in points]).all()
            expected_seqs = (
                1, 1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23)
            assert seqs == expected_seqs
            assert approx(alongs, abs=2) == [s * 272 for s in expected_seqs]
            assert all(p.x < 1000 for p in points)
            assert all(p.y < 1000 for p in points)
    # End test_generate_features_geographic_dd method
# End TestQueryGeneratePointsAlong3DLinesField class


if __name__ == '__main__':  # pragma: no cover
    pass
