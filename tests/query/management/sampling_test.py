# -*- coding: utf-8 -*-
"""
Tests for the Sampling Query Classes
"""

from math import nan
from warnings import catch_warnings, simplefilter

from fudgeo import FeatureClass
from fudgeo.enumeration import ShapeType
from numpy import cumsum, isfinite
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
from spyops.query.management.sampling import (
    QueryGeneratePointsAlongLinesDistance,
    QueryGeneratePointsAlongLinesPercentage)
from spyops.shared.enumeration import DistanceTypeOption
from spyops.shared.exception import DistanceCalculationWarning


pytestmark = [mark.sampling, mark.query, mark.management]


class TestQueryGeneratePointsAlongLinesPercentage:
    """
    Test Query Generate Points Along Lines using Percentage
    """
    @staticmethod
    def _get_query(ntdb_zm_small):
        source = ntdb_zm_small['transmission_l']
        return QueryGeneratePointsAlongLinesPercentage(
            source, target=None, placement=33, include_end_points=False,
            where_clause='', distance_type=DistanceTypeOption.GEODESIC)
    # End _get_query method

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
        query = QueryGeneratePointsAlongLinesPercentage(
            source, target=None, placement=0.5, include_end_points=False,
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
        query = QueryGeneratePointsAlongLinesPercentage(
            None, target=None, placement=placement,
            include_end_points=False, where_clause='',
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
        query = QueryGeneratePointsAlongLinesPercentage(
            source, target=target, placement=33, include_end_points=False,
            where_clause='', distance_type=DistanceTypeOption.GEODESIC)
        assert 'INTO output_fc(SHAPE, ORIG_FID, SEQ_NUM, ALONG)' in query.insert
    # End test_insert method

    @mark.parametrize('distance_type, name, expected', [
        (DistanceTypeOption.PLANAR, 'transmission_10tm_l', (129.27, 258.55, 387.82, 389.22, 778.44, 1167.66, 61.99, 123.99, 185.98, 2102.54, 4205.08, 6307.61)),
        (DistanceTypeOption.PLANAR, 'transmission_10tm_m_l', (129.27, 258.55, 387.82, 389.22, 778.44, 1167.66, 61.99, 123.99, 185.98, 2102.54, 4205.08, 6307.61)),
        (DistanceTypeOption.PLANAR, 'transmission_10tm_z_l', (129.27, 258.55, 387.82, 389.22, 778.44, 1167.66, 61.99, 123.99, 185.98, 2102.54, 4205.08, 6307.61)),
        (DistanceTypeOption.PLANAR, 'transmission_10tm_zm_l', (129.27, 258.55, 387.82, 389.22, 778.44, 1167.66, 61.99, 123.99, 185.98, 2102.54, 4205.08, 6307.61)),
        (DistanceTypeOption.PLANAR, 'transmission_6654_l', (129.38, 258.75, 388.13, 389.54, 779.08, 1168.62, 62.04, 124.09, 186.13, 2104.27, 4208.54, 6312.81)),
        (DistanceTypeOption.PLANAR, 'transmission_6654_m_l', (129.38, 258.75, 388.13, 389.54, 779.08, 1168.62, 62.04, 124.09, 186.13, 2104.27, 4208.54, 6312.81)),
        (DistanceTypeOption.PLANAR, 'transmission_6654_z_l', (129.38, 258.75, 388.13, 389.54, 779.08, 1168.62, 62.04, 124.09, 186.13, 2104.27, 4208.54, 6312.81)),
        (DistanceTypeOption.PLANAR, 'transmission_6654_zm_l', (129.38, 258.75, 388.13, 389.54, 779.08, 1168.62, 62.04, 124.09, 186.13, 2104.27, 4208.54, 6312.81)),
        (DistanceTypeOption.PLANAR, 'transmission_utm11_l', (129.38, 258.75, 388.13, 389.54, 779.08, 1168.62, 62.04, 124.09, 186.13, 2104.27, 4208.54, 6312.81)),
        (DistanceTypeOption.PLANAR, 'transmission_utm11_m_l', (129.38, 258.75, 388.13, 389.54, 779.08, 1168.62, 62.04, 124.09, 186.13, 2104.27, 4208.54, 6312.81)),
        (DistanceTypeOption.PLANAR, 'transmission_utm11_z_l', (129.38, 258.75, 388.13, 389.54, 779.08, 1168.62, 62.04, 124.09, 186.13, 2104.27, 4208.54, 6312.81)),
        (DistanceTypeOption.PLANAR, 'transmission_utm11_zm_l', (129.38, 258.75, 388.13, 389.54, 779.08, 1168.62, 62.04, 124.09, 186.13, 2104.27, 4208.54, 6312.81)),
        (DistanceTypeOption.GEODESIC, 'transmission_10tm_l', (129.42, 258.84, 388.26, 389.66, 779.33, 1169.00, 62.06, 124.12, 186.18, 2104.18, 4208.37, 6312.56)),
        (DistanceTypeOption.GEODESIC, 'transmission_10tm_m_l', (129.42, 258.84, 388.26, 389.66, 779.33, 1169.00, 62.06, 124.12, 186.18, 2104.18, 4208.37, 6312.56)),
        (DistanceTypeOption.GEODESIC, 'transmission_10tm_z_l', (129.42, 258.84, 388.26, 389.66, 779.33, 1169.00, 62.06, 124.12, 186.18, 2104.18, 4208.37, 6312.56)),
        (DistanceTypeOption.GEODESIC, 'transmission_10tm_zm_l', (129.42, 258.84, 388.26, 389.66, 779.33, 1169.00, 62.06, 124.12, 186.18, 2104.18, 4208.37, 6312.56)),
        (DistanceTypeOption.GEODESIC, 'transmission_6654_l', (129.42, 258.84, 388.26, 389.67, 779.33, 1169.0, 62.06, 124.12, 186.18, 2104.18, 4208.35, 6312.53)),
        (DistanceTypeOption.GEODESIC, 'transmission_6654_m_l', (129.42, 258.84, 388.26, 389.67, 779.33, 1169.0, 62.06, 124.12, 186.18, 2104.18, 4208.35, 6312.53)),
        (DistanceTypeOption.GEODESIC, 'transmission_6654_z_l', (129.42, 258.84, 388.26, 389.67, 779.33, 1169.0, 62.06, 124.12, 186.18, 2104.18, 4208.35, 6312.53)),
        (DistanceTypeOption.GEODESIC, 'transmission_6654_zm_l', (129.42, 258.84, 388.26, 389.67, 779.33, 1169.0, 62.06, 124.12, 186.18, 2104.18, 4208.35, 6312.53)),
        (DistanceTypeOption.GEODESIC, 'transmission_utm11_l', (129.42, 258.84, 388.26, 389.67, 779.33, 1169.0, 62.06, 124.12, 186.18, 2104.18, 4208.35, 6312.53)),
        (DistanceTypeOption.GEODESIC, 'transmission_utm11_m_l', (129.42, 258.84, 388.26, 389.67, 779.33, 1169.0, 62.06, 124.12, 186.18, 2104.18, 4208.35, 6312.53)),
        (DistanceTypeOption.GEODESIC, 'transmission_utm11_z_l', (129.42, 258.84, 388.26, 389.67, 779.33, 1169.0, 62.06, 124.12, 186.18, 2104.18, 4208.35, 6312.53)),
        (DistanceTypeOption.GEODESIC, 'transmission_utm11_zm_l', (129.42, 258.84, 388.26, 389.67, 779.33, 1169.0, 62.06, 124.12, 186.18, 2104.18, 4208.35, 6312.53)),
    ])
    def test_generate_points_projected(self, ntdb_zm_small, mem_gpkg, distance_type, name, expected):
        """
        Test generate_points using projected source
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        placement = 33
        include = False
        query = QueryGeneratePointsAlongLinesPercentage(
            source, target=target, placement=placement,
            include_end_points=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_points(features)
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
    # End test_generate_points_projected method

    @mark.parametrize('name, expected', [
        ('transmission_l', (129.42, 258.84, 388.26, 389.66, 779.33, 1169.00, 62.06, 124.12, 186.18, 2104.18, 4208.37, 6312.56)),
        ('transmission_m_l', (129.42, 258.84, 388.26, 389.66, 779.33, 1169.00, 62.06, 124.12, 186.18, 2104.18, 4208.37, 6312.56)),
        ('transmission_z_l', (129.42, 258.84, 388.26, 389.66, 779.33, 1169.00, 62.06, 124.12, 186.18, 2104.18, 4208.37, 6312.56)),
        ('transmission_zm_l', (129.42, 258.84, 388.26, 389.66, 779.33, 1169.00, 62.06, 124.12, 186.18, 2104.18, 4208.37, 6312.56)),
        ('transmission_4617_l', (129.42, 258.84, 388.26, 389.67, 779.33, 1169.0, 62.06, 124.12, 186.18, 2104.18, 4208.35, 6312.53)),
        ('transmission_4617_m_l', (129.42, 258.84, 388.26, 389.67, 779.33, 1169.0, 62.06, 124.12, 186.18, 2104.18, 4208.35, 6312.53)),
        ('transmission_4617_z_l', (129.42, 258.84, 388.26, 389.67, 779.33, 1169.0, 62.06, 124.12, 186.18, 2104.18, 4208.35, 6312.53)),
        ('transmission_4617_zm_l', (129.42, 258.84, 388.26, 389.67, 779.33, 1169.0, 62.06, 124.12, 186.18, 2104.18, 4208.35, 6312.53)),
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC
    ])
    def test_generate_points_geographic(self, ntdb_zm_small, mem_gpkg, name, expected, distance_type):
        """
        Test generate_points using geographic source
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        placement = 33
        include = False
        query = QueryGeneratePointsAlongLinesPercentage(
            source, target=target, placement=placement,
            include_end_points=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_points(features)
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
    # End test_generate_points_geographic method

    @mark.parametrize('distance_type, name, expected', [
        (DistanceTypeOption.PLANAR, 'transmission_10tm_l', (0.0, 129.27, 258.54, 387.82, 391.73, 0.0, 389.22, 778.44, 1167.66, 1179.45, 0.0, 61.99, 123.98, 185.97, 187.85, 0.0, 2102.53, 4205.07, 6307.61, 6371.32)),
        (DistanceTypeOption.GEODESIC, 'transmission_10tm_l', (0.0, 129.42, 258.84, 388.26, 392.19, 0.0, 389.66, 779.33, 1169.00, 1180.81, 0.0, 62.06, 124.12, 186.18, 188.06, 0.0, 2104.18, 4208.37, 6312.56, 6376.32)),
        (DistanceTypeOption.PLANAR, 'transmission_l', (0.0, 129.42, 258.84, 388.26, 392.18, 0.0, 389.66, 779.33, 1169.00, 1180.80, 0.0, 62.05, 124.11, 186.17, 188.05, 0.0, 2104.17, 4208.35, 6312.52, 6376.29)),
        (DistanceTypeOption.GEODESIC, 'transmission_l', (0.0, 129.42, 258.84, 388.26, 392.18, 0.0, 389.66, 779.33, 1169.00, 1180.80, 0.0, 62.05, 124.11, 186.17, 188.05, 0.0, 2104.17, 4208.35, 6312.52, 6376.29)),
    ])
    def test_generate_points_include_ends(self, ntdb_zm_small, mem_gpkg, distance_type, name, expected):
        """
        Test generate points include ends
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        placement = 33
        include = True
        query = QueryGeneratePointsAlongLinesPercentage(
            source, target=target, placement=placement,
            include_end_points=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_points(features)
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
    # End test_generate_points_include_ends method
# End TestQueryGeneratePointsAlongLinesPercentage class


class TestQueryGeneratePointsAlongLinesDistance:
    """
    Test Query Generate Points Along Lines using Distance
    """
    @mark.parametrize('name, unit, distance_type, expected', [
        ('transmission_l', Meters(200), DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_l', Meters(200), DistanceTypeOption.PLANAR, DistanceTypeOption.GEODESIC),
        ('transmission_utm11_l', Meters(200), DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_utm11_l', Meters(200), DistanceTypeOption.PLANAR, DistanceTypeOption.PLANAR),
        ('transmission_l', DecimalDegrees(0.1), DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_l', DecimalDegrees(0.1), DistanceTypeOption.PLANAR, DistanceTypeOption.GEODESIC),
        ('transmission_utm11_l', DecimalDegrees(0.1), DistanceTypeOption.GEODESIC, DistanceTypeOption.GEODESIC),
        ('transmission_utm11_l', DecimalDegrees(0.1), DistanceTypeOption.PLANAR, DistanceTypeOption.GEODESIC),
    ])
    def test_distance_type(self, ntdb_zm_small, name, unit, distance_type, expected):
        """
        Test distance type
        """
        source = ntdb_zm_small[name]
        query = QueryGeneratePointsAlongLinesDistance(
            source, target=None, placement=unit, include_end_points=False,
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
        query = QueryGeneratePointsAlongLinesDistance(
            source, target=None, placement=unit, include_end_points=False,
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
        query = QueryGeneratePointsAlongLinesDistance(
            source, target=None, placement=unit, include_end_points=False,
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
        query = QueryGeneratePointsAlongLinesDistance(
            source, target=None, placement=placement,
            include_end_points=False, where_clause='',
            distance_type=DistanceTypeOption.GEODESIC)
        query._get_values([], total_length=123, crs=WGS84, distance=None)
        assert query._counter == expected
    # End test_get_values_counter method

    def test_show_warning(self, ntdb_zm_small):
        """
        Test show warning
        """
        source = ntdb_zm_small['transmission_10tm_l']
        query = QueryGeneratePointsAlongLinesDistance(
            source, target=None, placement=Meters(10),
            include_end_points=False, where_clause='',
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
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_10tm_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_10tm_m_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_10tm_z_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_10tm_zm_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_6654_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_6654_m_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_6654_z_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_6654_zm_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_utm11_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_utm11_m_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_utm11_z_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_utm11_zm_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_10tm_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_10tm_m_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_10tm_z_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_10tm_zm_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_6654_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_6654_m_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_6654_z_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_6654_zm_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_utm11_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_utm11_m_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_utm11_z_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_utm11_zm_l'),
    ])
    def test_generate_points_projected_linear(self, ntdb_zm_small, mem_gpkg, distance_type, placement, name):
        """
        Test generate_points using projected source with linear unit
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = False
        query = QueryGeneratePointsAlongLinesDistance(
            source, target=target, placement=placement,
            include_end_points=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_points(features)
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
    # End test_generate_points_projected_linear method

    @mark.parametrize('distance_type, placement, name', [
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_m_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_z_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_zm_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_4617_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_4617_m_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_4617_z_l'),
        (DistanceTypeOption.PLANAR, Feet(200 / 0.3048), 'transmission_4617_zm_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_m_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_z_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_zm_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_4617_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_4617_m_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_4617_z_l'),
        (DistanceTypeOption.GEODESIC, Feet(200 / 0.3048), 'transmission_4617_zm_l'),
    ])
    def test_generate_points_geographic_linear(self, ntdb_zm_small, mem_gpkg, distance_type, placement, name):
        """
        Test generate_points using geographic source with linear unit
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = False
        query = QueryGeneratePointsAlongLinesDistance(
            source, target=target, placement=placement,
            include_end_points=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_points(features)
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
    # End test_generate_points_geographic_linear method

    @mark.parametrize('distance_type, placement, name', [
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_10tm_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_10tm_m_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_10tm_z_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_10tm_zm_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_6654_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_6654_m_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_6654_z_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_6654_zm_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_utm11_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_utm11_m_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_utm11_z_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_utm11_zm_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_10tm_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_10tm_m_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_10tm_z_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_10tm_zm_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_6654_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_6654_m_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_6654_z_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_6654_zm_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_utm11_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_utm11_m_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_utm11_z_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_utm11_zm_l'),
    ])
    def test_generate_points_projected_dd(self, ntdb_zm_small, mem_gpkg, distance_type, placement, name):
        """
        Test generate_points using projected source with decimal degrees
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = False
        query = QueryGeneratePointsAlongLinesDistance(
            source, target=target, placement=placement,
            include_end_points=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_points(features)
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
    # End test_generate_points_projected_dd method

    @mark.parametrize('distance_type, placement, name', [
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_m_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_z_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_zm_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_4617_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_4617_m_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_4617_z_l'),
        (DistanceTypeOption.PLANAR, DecimalDegrees(0.003), 'transmission_4617_zm_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_m_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_z_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_zm_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_4617_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_4617_m_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_4617_z_l'),
        (DistanceTypeOption.GEODESIC, DecimalDegrees(0.003), 'transmission_4617_zm_l'),
    ])
    def test_generate_points_geographic_dd(self, ntdb_zm_small, mem_gpkg, distance_type, placement, name):
        """
        Test generate_points using geographic source with decimal degrees
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = False
        query = QueryGeneratePointsAlongLinesDistance(
            source, target=target, placement=placement,
            include_end_points=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_points(features)
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
    # End test_generate_points_geographic_dd method

    @mark.parametrize('distance_type, name, expected', [
        (DistanceTypeOption.PLANAR, 'transmission_10tm_l', (0.0, 391.73, 0.0, 1179.45, 0.0, 187.85, 0.0, 6371.32)),
        (DistanceTypeOption.GEODESIC, 'transmission_10tm_l', (0.0, 392.19, 0.0, 1180.81, 0.0, 188.06, 0.0, 6376.32)),
        (DistanceTypeOption.PLANAR, 'transmission_l', (0.0, 392.18, 0.0, 1180.80, 0.0, 188.05, 0.0, 6376.29)),
        (DistanceTypeOption.GEODESIC, 'transmission_l', (0.0, 392.18, 0.0, 1180.80, 0.0, 188.05, 0.0, 6376.29)),
    ])
    def test_generate_points_include_ends(self, ntdb_zm_small, mem_gpkg, distance_type, name, expected):
        """
        Test generate points include only ends by using a large
        placement distance
        """
        count = 4
        source = ntdb_zm_small[name]
        target = FeatureClass(mem_gpkg, 'output_fc')
        include = True
        query = QueryGeneratePointsAlongLinesDistance(
            source, target=target, placement=Kilometers(10),
            include_end_points=include, where_clause=f'fid <= {count}',
            distance_type=distance_type)
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            features = cursor.fetchall()
            points = query.generate_points(features)
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
    # End test_generate_points_include_ends method
# End TestQueryGeneratePointsAlongLinesDistance class


if __name__ == '__main__':  # pragma: no cover
    pass
