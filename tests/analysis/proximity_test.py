# -*- coding: utf-8 -*-
"""
Tests for Proximity
"""

from fudgeo import FeatureClass
from pyproj import CRS
from pytest import mark, param, approx

from spyops.analysis import buffer, multiple_buffer
from spyops.crs.enumeration import DistanceUnit
from spyops.crs.unit import DecimalDegrees, Kilometers, Meters, Miles
from spyops.environment import Extent, OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.shared.enumeration import (
    BufferTypeOption, DissolveOption, SideOption)

pytestmark = [mark.proximity, mark.analysis]


class TestBuffer:
    """
    Test Buffer
    """
    @mark.parametrize('fc_name, distance, expected', [
        ('admin_a', Kilometers(12.345), 6),
        ('admin_a', DecimalDegrees(1.2345), 6),
        ('admin_a', 'NUM_DIST', 6),
        param('admin_a', 'LIN_UNIT', 6, marks=mark.large),
        param('admin_a', 'ANG_UNIT', 6, marks=mark.large),
        ('admin_a', 'MIX_UNIT', 6),
        param('admin_mp_a', Kilometers(12.345), 6, marks=mark.slow),
        param('admin_mp_a', DecimalDegrees(1.2345), 6, marks=mark.slow),
        param('admin_mp_a', 'NUM_DIST', 6, marks=mark.slow),
        param('admin_mp_a', 'LIN_UNIT', 6, marks=mark.slow),
        param('admin_mp_a', 'ANG_UNIT', 6, marks=mark.slow),
        param('admin_mp_a', 'MIX_UNIT', 6, marks=mark.slow),
        param('admin_lcc_na_a', Kilometers(12.345), 6, marks=mark.slow),
        param('admin_lcc_na_a', DecimalDegrees(1.2345), 6, marks=mark.slow),
        param('admin_lcc_na_a', 'NUM_DIST', 6, marks=mark.slow),
        param('admin_lcc_na_a', 'LIN_UNIT', 6, marks=mark.slow),
        param('admin_lcc_na_a', 'ANG_UNIT', 6, marks=mark.slow),
        param('admin_lcc_na_a', 'MIX_UNIT', 6, marks=mark.slow),
        param('admin_lcc_na_mp_a', Kilometers(12.345), 6, marks=mark.slow),
        param('admin_lcc_na_mp_a', DecimalDegrees(1.2345), 6, marks=mark.slow),
        param('admin_lcc_na_mp_a', 'NUM_DIST', 6, marks=mark.slow),
        param('admin_lcc_na_mp_a', 'LIN_UNIT', 6, marks=mark.slow),
        param('admin_lcc_na_mp_a', 'ANG_UNIT', 6, marks=mark.slow),
        param('admin_lcc_na_mp_a', 'MIX_UNIT', 6, marks=mark.slow),
    ])
    @mark.parametrize('buffer_type', [
        param(BufferTypeOption.PLANAR, marks=mark.large),
        BufferTypeOption.GEODESIC,
    ])
    @mark.parametrize('side_option', [
        SideOption.FULL,
        param(SideOption.ONLY_OUTSIDE, marks=mark.large),
    ])
    def test_list_polygon(self, mem_gpkg, buffering, fc_name, distance, expected, buffer_type, side_option):
        """
        Test Dissolve List for Polygon
        """
        fields = 'COUNTRY', 'ADMINTYPE', 'LAND_RANK'
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_buffer')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = buffer(
                source, target=target, distance=distance,
                buffer_type=buffer_type, side_option=side_option,
                dissolve_option=DissolveOption.LIST, group_fields=fields)
            assert len(result) == expected
    # End test_list_polygon method

    def test_sans_attr(self, mem_gpkg, buffering):
        """
        Test Polygon with no Attributes
        """
        source = buffering['admin_sans_attr_a']
        target = FeatureClass(geopackage=mem_gpkg, name=f'sans_all_buffer')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = buffer(
                source, target=target, distance=Meters(1234.5),
                buffer_type=BufferTypeOption.PLANAR, side_option=SideOption.FULL,
                dissolve_option=DissolveOption.ALL)
            assert len(result) == 1

        target = FeatureClass(geopackage=mem_gpkg, name=f'sans_none_buffer')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = buffer(
                source, target=target, distance=Meters(1234.5),
                buffer_type=BufferTypeOption.PLANAR, side_option=SideOption.FULL,
                dissolve_option=DissolveOption.NONE)
            assert len(result) == 11
    # End test_sans_attr method

    @mark.zm
    @mark.parametrize('fc_name, distance, extent', [
        ('admin_a', Kilometers(12.345), (-2318644.25, 1008274.1875, -765862.3125, 2723458.75)),
        ('roads_l', Miles(12.345), (-1406919.0, 1003453.0, -872218.0625, 1636588.625)),
        ('airports_p', Meters(20_000), (-1377437.125, 984348.8125, -979955.375, 1559509.375)),
    ])
    @mark.parametrize('buffer_type', [
        BufferTypeOption.PLANAR,
        BufferTypeOption.GEODESIC,
    ])
    def test_output_settings(self, mem_gpkg, buffering, fc_name, distance, extent, buffer_type):
        """
        Test Buffering with Z output and M output + reprojecting features
        """
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_buffer')
        with (Swap(Setting.EXTENT, Extent.from_bounds(-116, 48, -110, 54, crs=CRS(4326))),
              Swap(Setting.OUTPUT_M_OPTION, OutputMOption.ENABLED),
              Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.ENABLED),
              Swap(Setting.Z_VALUE, 123.456),
              Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS.from_authority('ESRI', 102009))):
            result = buffer(
                source, target=target, distance=distance,
                buffer_type=buffer_type, side_option=SideOption.FULL,
                dissolve_option=DissolveOption.NONE)
            assert result.has_z
            assert result.has_m
            assert result.spatial_reference_system.srs_id == 102009
            assert approx(result.extent, abs=1) == extent
    # End test_output_settings method

    @mark.parametrize('fc_name, distance, expected', [
        ('roads_l', Kilometers(12.345), 4),
        ('roads_l', DecimalDegrees(1.2345), 4),
        ('roads_l', 'NUM_DIST', 4),
        param('roads_l', 'LIN_UNIT', 4, marks=mark.large),
        param('roads_l', 'ANG_UNIT', 4, marks=mark.large),
        ('roads_l', 'MIX_UNIT', 4),
    ])
    @mark.parametrize('buffer_type', [
        param(BufferTypeOption.PLANAR, marks=mark.large),
        BufferTypeOption.GEODESIC,
    ])
    @mark.parametrize('side_option', [
        SideOption.FULL,
        param(SideOption.LEFT, marks=mark.large),
        param(SideOption.RIGHT, marks=mark.large),
    ])
    def test_list_line(self, mem_gpkg, buffering, fc_name, distance, expected, buffer_type, side_option):
        """
        Test Dissolve List for line
        """
        if 'mp' in fc_name:
            fields = 'ISO_CC'
        else:
            fields = 'ISO_CC', 'RANK'
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_buffer')
        with Swap(Setting.EXTENT, Extent.from_bounds(27, 45, 56, 70, crs=CRS(4326))):
            result = buffer(
                source, target=target, distance=distance,
                buffer_type=buffer_type, side_option=side_option,
                dissolve_option=DissolveOption.LIST, group_fields=fields)
            assert len(result) == expected
    # End test_list_line method

    @mark.parametrize('fc_name, distance, expected', [
        param('airports_p', Meters(200), 101, marks=mark.large),
        param('airports_p', DecimalDegrees(0.01), 101, marks=mark.large),
        param('airports_p', 'NUM_DIST', 101, marks=mark.large),
        param('airports_p', 'LIN_UNIT', 101, marks=mark.large),
        param('airports_p', 'ANG_UNIT', 101, marks=mark.large),
        param('airports_p', 'MIX_UNIT', 101, marks=mark.large),
        param('airports_mp_p', Meters(200), 4, marks=mark.large),
        param('airports_mp_p', DecimalDegrees(0.01), 4, marks=mark.large),
        param('airports_mp_p', 'NUM_DIST', 4, marks=mark.large),
        param('airports_mp_p', 'LIN_UNIT', 4, marks=mark.large),
        param('airports_mp_p', 'ANG_UNIT', 4, marks=mark.large),
        param('airports_mp_p', 'MIX_UNIT', 4, marks=mark.large),
        ('airports_lcc_na_p', Meters(200), 103),
        ('airports_lcc_na_p', DecimalDegrees(0.01), 103),
        ('airports_lcc_na_p', 'NUM_DIST', 103),
        ('airports_lcc_na_p', 'LIN_UNIT', 103),
        ('airports_lcc_na_p', 'ANG_UNIT', 103),
        ('airports_lcc_na_p', 'MIX_UNIT', 103),
        param('airports_lcc_na_mp_p', Meters(200), 3, marks=mark.large),
        param('airports_lcc_na_mp_p', DecimalDegrees(0.01), 3, marks=mark.large),
        param('airports_lcc_na_mp_p', 'NUM_DIST', 3, marks=mark.large),
        param('airports_lcc_na_mp_p', 'LIN_UNIT', 3, marks=mark.large),
        param('airports_lcc_na_mp_p', 'ANG_UNIT', 3, marks=mark.large),
        param('airports_lcc_na_mp_p', 'MIX_UNIT', 3, marks=mark.large),
    ])
    @mark.parametrize('buffer_type', [
        param(BufferTypeOption.PLANAR, marks=mark.large),
        BufferTypeOption.GEODESIC,
    ])
    def test_list_point(self, mem_gpkg, buffering, fc_name, distance, expected, buffer_type):
        """
        Test Dissolve List Point
        """
        if 'mp' in fc_name:
            fields = 'ISO_CC'
        else:
            fields = 'ISO_CC', 'IATA'
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_buffer')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = buffer(
                source, target=target, distance=distance,
                buffer_type=buffer_type, side_option=SideOption.FULL,
                dissolve_option=DissolveOption.LIST, group_fields=fields)
            assert len(result) == expected
    # End test_list_point method

    @mark.parametrize('fc_name, distance', [
        ('admin_a', Kilometers(12.345)),
        ('admin_a', DecimalDegrees(1.2345)),
        ('admin_a', 'NUM_DIST'),
        param('admin_a', 'LIN_UNIT', marks=mark.large),
        param('admin_a', 'ANG_UNIT', marks=mark.large),
        ('admin_a', 'MIX_UNIT'),
        param('admin_mp_a', Kilometers(12.345), marks=mark.slow),
        param('admin_mp_a', DecimalDegrees(1.2345), marks=mark.slow),
        param('admin_mp_a', 'NUM_DIST', marks=mark.slow),
        param('admin_mp_a', 'LIN_UNIT', marks=mark.slow),
        param('admin_mp_a', 'ANG_UNIT', marks=mark.slow),
        param('admin_mp_a', 'MIX_UNIT', marks=mark.slow),
        param('admin_lcc_na_a', Kilometers(12.345), marks=mark.slow),
        param('admin_lcc_na_a', DecimalDegrees(1.2345), marks=mark.slow),
        param('admin_lcc_na_a', 'NUM_DIST', marks=mark.slow),
        param('admin_lcc_na_a', 'LIN_UNIT', marks=mark.slow),
        param('admin_lcc_na_a', 'ANG_UNIT', marks=mark.slow),
        param('admin_lcc_na_a', 'MIX_UNIT', marks=mark.slow),
        param('admin_lcc_na_mp_a', Kilometers(12.345), marks=mark.slow),
        param('admin_lcc_na_mp_a', DecimalDegrees(1.2345), marks=mark.slow),
        param('admin_lcc_na_mp_a', 'NUM_DIST', marks=mark.slow),
        param('admin_lcc_na_mp_a', 'LIN_UNIT', marks=mark.slow),
        param('admin_lcc_na_mp_a', 'ANG_UNIT', marks=mark.slow),
        param('admin_lcc_na_mp_a', 'MIX_UNIT', marks=mark.slow),
    ])
    @mark.parametrize('buffer_type', [
        param(BufferTypeOption.PLANAR, marks=mark.large),
        BufferTypeOption.GEODESIC,
    ])
    @mark.parametrize('side_option', [
        SideOption.FULL,
        param(SideOption.ONLY_OUTSIDE, marks=mark.large),
    ])
    def test_all_polygon(self, mem_gpkg, buffering, fc_name, distance, buffer_type, side_option):
        """
        Test Dissolve All for Polygon
        """
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_buffer')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = buffer(
                source, target=target, distance=distance,
                buffer_type=buffer_type, side_option=side_option,
                dissolve_option=DissolveOption.ALL)
            assert len(result) == 1
    # End test_all_polygon method

    @mark.parametrize('fc_name, distance', [
        ('roads_l', Kilometers(12.345)),
        ('roads_l', DecimalDegrees(1.2345)),
        ('roads_l', 'NUM_DIST'),
        param('roads_l', 'LIN_UNIT', marks=mark.large),
        param('roads_l', 'ANG_UNIT', marks=mark.large),
        ('roads_l', 'MIX_UNIT'),
    ])
    @mark.parametrize('buffer_type', [
        param(BufferTypeOption.PLANAR, marks=mark.large),
        BufferTypeOption.GEODESIC,
    ])
    @mark.parametrize('side_option', [
        SideOption.FULL,
        param(SideOption.LEFT, marks=mark.large),
        param(SideOption.RIGHT, marks=mark.large),
    ])
    def test_all_line(self, mem_gpkg, buffering, fc_name, distance, buffer_type, side_option):
        """
        Test Dissolve All for line
        """
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_buffer')
        with Swap(Setting.EXTENT, Extent.from_bounds(27, 45, 56, 70, crs=CRS(4326))):
            result = buffer(
                source, target=target, distance=distance,
                buffer_type=buffer_type, side_option=side_option,
                dissolve_option=DissolveOption.ALL)
            assert len(result) == 1
    # End test_all_line method

    @mark.parametrize('fc_name, distance', [
        param('airports_p', Meters(200), marks=mark.large),
        param('airports_p', DecimalDegrees(0.01), marks=mark.large),
        param('airports_p', 'NUM_DIST', marks=mark.large),
        param('airports_p', 'LIN_UNIT', marks=mark.large),
        param('airports_p', 'ANG_UNIT', marks=mark.large),
        param('airports_p', 'MIX_UNIT', marks=mark.large),
        param('airports_mp_p', Meters(200), marks=mark.large),
        param('airports_mp_p', DecimalDegrees(0.01), marks=mark.large),
        param('airports_mp_p', 'NUM_DIST', marks=mark.large),
        param('airports_mp_p', 'LIN_UNIT', marks=mark.large),
        param('airports_mp_p', 'ANG_UNIT', marks=mark.large),
        param('airports_mp_p', 'MIX_UNIT', marks=mark.large),
        ('airports_lcc_na_p', Meters(200)),
        ('airports_lcc_na_p', DecimalDegrees(0.01)),
        ('airports_lcc_na_p', 'NUM_DIST'),
        ('airports_lcc_na_p', 'LIN_UNIT'),
        ('airports_lcc_na_p', 'ANG_UNIT'),
        ('airports_lcc_na_p', 'MIX_UNIT'),
        param('airports_lcc_na_mp_p', Meters(200), marks=mark.large),
        param('airports_lcc_na_mp_p', DecimalDegrees(0.01), marks=mark.large),
        param('airports_lcc_na_mp_p', 'NUM_DIST', marks=mark.large),
        param('airports_lcc_na_mp_p', 'LIN_UNIT', marks=mark.large),
        param('airports_lcc_na_mp_p', 'ANG_UNIT', marks=mark.large),
        param('airports_lcc_na_mp_p', 'MIX_UNIT', marks=mark.large),
    ])
    @mark.parametrize('buffer_type', [
        param(BufferTypeOption.PLANAR, marks=mark.large),
        BufferTypeOption.GEODESIC,
    ])
    def test_all_point(self, mem_gpkg, buffering, fc_name, distance, buffer_type):
        """
        Test Dissolve All Point
        """
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_buffer')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = buffer(
                source, target=target, distance=distance,
                buffer_type=buffer_type, side_option=SideOption.FULL,
                dissolve_option=DissolveOption.ALL)
            assert len(result) == 1
    # End test_all_point method

    @mark.parametrize('fc_name, distance, expected', [
        ('admin_a', Kilometers(12.345), 488),
        ('admin_a', DecimalDegrees(1.2345), 488),
        ('admin_a', 'NUM_DIST', 488),
        param('admin_a', 'LIN_UNIT', 488, marks=mark.large),
        param('admin_a', 'ANG_UNIT', 488, marks=mark.large),
        ('admin_a', 'MIX_UNIT', 488),
        param('admin_mp_a', Kilometers(12.345), 11, marks=mark.slow),
        param('admin_mp_a', DecimalDegrees(1.2345), 11, marks=mark.slow),
        param('admin_mp_a', 'NUM_DIST', 11, marks=mark.slow),
        param('admin_mp_a', 'LIN_UNIT', 11, marks=mark.slow),
        param('admin_mp_a', 'ANG_UNIT', 11, marks=mark.slow),
        param('admin_mp_a', 'MIX_UNIT', 11, marks=mark.slow),
        param('admin_lcc_na_a', Kilometers(12.345), 474, marks=mark.slow),
        param('admin_lcc_na_a', DecimalDegrees(1.2345), 474, marks=mark.slow),
        param('admin_lcc_na_a', 'NUM_DIST', 474, marks=mark.slow),
        param('admin_lcc_na_a', 'LIN_UNIT', 474, marks=mark.slow),
        param('admin_lcc_na_a', 'ANG_UNIT', 474, marks=mark.slow),
        param('admin_lcc_na_a', 'MIX_UNIT', 474, marks=mark.slow),
        param('admin_lcc_na_mp_a', Kilometers(12.345), 11, marks=mark.slow),
        param('admin_lcc_na_mp_a', DecimalDegrees(1.2345), 11, marks=mark.slow),
        param('admin_lcc_na_mp_a', 'NUM_DIST', 11, marks=mark.slow),
        param('admin_lcc_na_mp_a', 'LIN_UNIT', 11, marks=mark.slow),
        param('admin_lcc_na_mp_a', 'ANG_UNIT', 11, marks=mark.slow),
        param('admin_lcc_na_mp_a', 'MIX_UNIT', 11, marks=mark.slow),
    ])
    @mark.parametrize('buffer_type', [
        param(BufferTypeOption.PLANAR, marks=mark.large),
        BufferTypeOption.GEODESIC,
    ])
    @mark.parametrize('side_option', [
        SideOption.FULL,
        param(SideOption.ONLY_OUTSIDE, marks=mark.large),
    ])
    def test_none_polygon(self, mem_gpkg, buffering, fc_name, distance, expected, buffer_type, side_option):
        """
        Test Dissolve None for Polygon
        """
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_buffer')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = buffer(
                source, target=target, distance=distance,
                buffer_type=buffer_type, side_option=side_option,
                dissolve_option=DissolveOption.NONE)
            assert len(result) == expected
    # End test_none_polygon method

    @mark.parametrize('side_option, buffer_type, fc_name, distance, expected', [
        param(SideOption.FULL, BufferTypeOption.PLANAR, 'roads_l', Kilometers(12.345), 807, marks=mark.large),
        param(SideOption.FULL, BufferTypeOption.PLANAR, 'roads_l', DecimalDegrees(1.2345), 807, marks=mark.large),
        param(SideOption.FULL, BufferTypeOption.PLANAR, 'roads_l', 'NUM_DIST', 807, marks=mark.large),
        param(SideOption.FULL, BufferTypeOption.PLANAR, 'roads_l', 'LIN_UNIT', 807, marks=mark.large),
        param(SideOption.FULL, BufferTypeOption.PLANAR, 'roads_l', 'ANG_UNIT', 807, marks=mark.large),
        param(SideOption.FULL, BufferTypeOption.PLANAR, 'roads_l', 'MIX_UNIT', 807, marks=mark.large),
        param(SideOption.LEFT, BufferTypeOption.PLANAR, 'roads_l', Kilometers(12.345), 807, marks=mark.large),
        param(SideOption.LEFT, BufferTypeOption.PLANAR, 'roads_l', DecimalDegrees(1.2345), 803, marks=mark.large),
        param(SideOption.LEFT, BufferTypeOption.PLANAR, 'roads_l', 'NUM_DIST', 805, marks=mark.large),
        param(SideOption.LEFT, BufferTypeOption.PLANAR, 'roads_l', 'LIN_UNIT', 807, marks=mark.large),
        param(SideOption.LEFT, BufferTypeOption.PLANAR, 'roads_l', 'ANG_UNIT', 803, marks=mark.large),
        param(SideOption.LEFT, BufferTypeOption.PLANAR, 'roads_l', 'MIX_UNIT', 804, marks=mark.large),
        param(SideOption.RIGHT, BufferTypeOption.PLANAR, 'roads_l', Kilometers(12.345), 807, marks=mark.large),
        param(SideOption.RIGHT, BufferTypeOption.PLANAR, 'roads_l', DecimalDegrees(1.2345), 803, marks=mark.large),
        param(SideOption.RIGHT, BufferTypeOption.PLANAR, 'roads_l', 'NUM_DIST', 805, marks=mark.large),
        param(SideOption.RIGHT, BufferTypeOption.PLANAR, 'roads_l', 'LIN_UNIT', 807, marks=mark.large),
        param(SideOption.RIGHT, BufferTypeOption.PLANAR, 'roads_l', 'ANG_UNIT', 803, marks=mark.large),
        param(SideOption.RIGHT, BufferTypeOption.PLANAR, 'roads_l', 'MIX_UNIT', 804, marks=mark.large),
        (SideOption.FULL, BufferTypeOption.GEODESIC, 'roads_l', Kilometers(12.345), 807),
        (SideOption.FULL, BufferTypeOption.GEODESIC, 'roads_l', DecimalDegrees(1.2345), 807),
        (SideOption.FULL, BufferTypeOption.GEODESIC, 'roads_l', 'NUM_DIST', 807),
        (SideOption.FULL, BufferTypeOption.GEODESIC, 'roads_l', 'LIN_UNIT', 807),
        (SideOption.FULL, BufferTypeOption.GEODESIC, 'roads_l', 'ANG_UNIT', 807),
        (SideOption.FULL, BufferTypeOption.GEODESIC, 'roads_l', 'MIX_UNIT', 807),
        param(SideOption.LEFT, BufferTypeOption.GEODESIC, 'roads_l', Kilometers(12.345), 807, marks=mark.large),
        (SideOption.LEFT, BufferTypeOption.GEODESIC, 'roads_l', DecimalDegrees(1.2345), 801),
        (SideOption.LEFT, BufferTypeOption.GEODESIC, 'roads_l', 'NUM_DIST', 804),
        param(SideOption.LEFT, BufferTypeOption.GEODESIC, 'roads_l', 'LIN_UNIT', 807, marks=mark.large),
        (SideOption.LEFT, BufferTypeOption.GEODESIC, 'roads_l', 'ANG_UNIT', 804),
        (SideOption.LEFT, BufferTypeOption.GEODESIC, 'roads_l', 'MIX_UNIT', 804),
        param(SideOption.RIGHT, BufferTypeOption.GEODESIC, 'roads_l', Kilometers(12.345), 807, marks=mark.large),
        (SideOption.RIGHT, BufferTypeOption.GEODESIC, 'roads_l', DecimalDegrees(1.2345), 801),
        (SideOption.RIGHT, BufferTypeOption.GEODESIC, 'roads_l', 'NUM_DIST', 804),
        param(SideOption.RIGHT, BufferTypeOption.GEODESIC, 'roads_l', 'LIN_UNIT', 807, marks=mark.large),
        (SideOption.RIGHT, BufferTypeOption.GEODESIC, 'roads_l', 'ANG_UNIT', 804),
        (SideOption.RIGHT, BufferTypeOption.GEODESIC, 'roads_l', 'MIX_UNIT', 804),
    ])
    def test_none_line(self, mem_gpkg, buffering, side_option, buffer_type, fc_name, distance, expected):
        """
        Test Dissolve None for line
        """
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_buffer')
        with Swap(Setting.EXTENT, Extent.from_bounds(27, 45, 56, 70, crs=CRS(4326))):
            result = buffer(
                source, target=target, distance=distance,
                buffer_type=buffer_type, side_option=side_option,
                dissolve_option=DissolveOption.NONE)
            assert len(result) == expected
    # End test_none_line method

    @mark.parametrize('fc_name, distance, expected', [
        param('airports_p', Meters(200), 182, marks=mark.large),
        param('airports_p', DecimalDegrees(0.01), 182, marks=mark.large),
        param('airports_p', 'NUM_DIST', 182, marks=mark.large),
        param('airports_p', 'LIN_UNIT', 182, marks=mark.large),
        param('airports_p', 'ANG_UNIT', 182, marks=mark.large),
        param('airports_p', 'MIX_UNIT', 182, marks=mark.large),
        param('airports_mp_p', Meters(200), 4, marks=mark.large),
        param('airports_mp_p', DecimalDegrees(0.01), 4, marks=mark.large),
        param('airports_mp_p', 'NUM_DIST', 4, marks=mark.large),
        param('airports_mp_p', 'LIN_UNIT', 4, marks=mark.large),
        param('airports_mp_p', 'ANG_UNIT', 4, marks=mark.large),
        param('airports_mp_p', 'MIX_UNIT', 4, marks=mark.large),
        ('airports_lcc_na_p', Meters(200), 202),
        ('airports_lcc_na_p', DecimalDegrees(0.01), 202),
        ('airports_lcc_na_p', 'NUM_DIST', 202),
        ('airports_lcc_na_p', 'LIN_UNIT', 202),
        ('airports_lcc_na_p', 'ANG_UNIT', 202),
        ('airports_lcc_na_p', 'MIX_UNIT', 202),
        param('airports_lcc_na_mp_p', Meters(200), 3, marks=mark.large),
        param('airports_lcc_na_mp_p', DecimalDegrees(0.01), 3, marks=mark.large),
        param('airports_lcc_na_mp_p', 'NUM_DIST', 3, marks=mark.large),
        param('airports_lcc_na_mp_p', 'LIN_UNIT', 3, marks=mark.large),
        param('airports_lcc_na_mp_p', 'ANG_UNIT', 3, marks=mark.large),
        param('airports_lcc_na_mp_p', 'MIX_UNIT', 3, marks=mark.large),
    ])
    @mark.parametrize('buffer_type', [
        param(BufferTypeOption.PLANAR, marks=mark.large),
        BufferTypeOption.GEODESIC,
    ])
    def test_none_point(self, mem_gpkg, buffering, fc_name, distance, expected, buffer_type):
        """
        Test Dissolve None Point
        """
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_buffer')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = buffer(
                source, target=target, distance=distance,
                buffer_type=buffer_type, side_option=SideOption.FULL,
                dissolve_option=DissolveOption.NONE)
            assert len(result) == expected
    # End test_none_point method
# End TestBuffer class


class TestMultipleBuffer:
    """
    Test Multiple Buffer
    """
    @mark.parametrize('overlap, only, distances, expected', [
        (True, True, [-20, -10, 0, 10, 20, 35, 50], 24),
        (True, False, [-20, -10, 0, 10, 20, 35, 50], 28),
        (False, True, [-20, -10, 0, 10, 20, 35, 50], 6),
        (False, False, [-20, -10, 0, 10, 20, 35, 50], 7),
        (True, True, [-20, -10], 8),
        (True, False, [-20, -10], 12),
        (False, True, [-20, -10], 2),
        (False, False, [-20, -10], 3),
        (True, True, [10, 20, 35, 50], 16),
        (True, False, [10, 20, 35, 50], 16),
        (False, True, [10, 20, 35, 50], 4),
        (False, False, [10, 20, 35, 50], 4),
    ])
    @mark.parametrize('field_name', [
        'buffer_distance',
        None
    ])
    def test_polygons(self, mem_gpkg, buffering, overlap, only, distances, expected, field_name):
        """
        Test polygons
        """
        source = buffering['mb_boxes_a']
        target = FeatureClass(mem_gpkg, name=f'mb_boxes_buffer_a')
        result = multiple_buffer(
            source, target=target, distance_unit=DistanceUnit.KILOMETERS,
            distances=distances, buffer_type=BufferTypeOption.GEODESIC,
            overlapping=overlap, only_outside=only, field_name=field_name)
        assert not result.has_z
        assert not result.has_m
        assert len(result) == expected
    # End test_polygons method

    @mark.parametrize('overlap, only, distances, expected', [
        (True, True, [-20, -10, 0, 10, 20, 35, 50], 64),
        (True, False, [-20, -10, 0, 10, 20, 35, 50], 64),
        (False, True, [-20, -10, 0, 10, 20, 35, 50], 4),
        (False, False, [-20, -10, 0, 10, 20, 35, 50], 4),
        (True, True, [-20, -10], 0),
        (True, False, [-20, -10], 0),
        (False, True, [-20, -10], 0),
        (False, False, [-20, -10], 0),
        (True, True, [10, 20, 35, 50], 64),
        (True, False, [10, 20, 35, 50], 64),
        (False, True, [10, 20, 35, 50], 4),
        (False, False, [10, 20, 35, 50], 4),
    ])
    @mark.parametrize('field_name', [
        'buffer_distance',
        None
    ])
    def test_lines(self, mem_gpkg, buffering, overlap, only, distances, expected, field_name):
        """
        Test lines
        """
        source = buffering['mb_lines_l']
        target = FeatureClass(mem_gpkg, name=f'mb_lines_buffer_a')
        result = multiple_buffer(
            source, target=target, distance_unit=DistanceUnit.KILOMETERS,
            distances=distances, buffer_type=BufferTypeOption.GEODESIC,
            overlapping=overlap, only_outside=only, field_name=field_name)
        assert not result.has_z
        assert not result.has_m
        assert len(result) == expected
    # End test_lines method

    @mark.parametrize('overlap, only, distances, expected', [
        (True, True, [-20, -10, 0, 10, 20, 35, 50], 184),
        (True, False, [-20, -10, 0, 10, 20, 35, 50], 184),
        (False, True, [-20, -10, 0, 10, 20, 35, 50], 4),
        (False, False, [-20, -10, 0, 10, 20, 35, 50], 4),
        (True, True, [-20, -10], 0),
        (True, False, [-20, -10], 0),
        (False, True, [-20, -10], 0),
        (False, False, [-20, -10], 0),
        (True, True, [10, 20, 35, 50], 184),
        (True, False, [10, 20, 35, 50], 184),
        (False, True, [10, 20, 35, 50], 4),
        (False, False, [10, 20, 35, 50], 4),
    ])
    @mark.parametrize('field_name', [
        'buffer_distance',
        None
    ])
    def test_points(self, mem_gpkg, buffering, overlap, only, distances, expected, field_name):
        """
        Test points
        """
        source = buffering['mb_points_p']
        target = FeatureClass(mem_gpkg, name=f'mb_points_buffer_a')
        result = multiple_buffer(
            source, target=target, distance_unit=DistanceUnit.KILOMETERS,
            distances=distances, buffer_type=BufferTypeOption.GEODESIC,
            overlapping=overlap, only_outside=only, field_name=field_name)
        assert not result.has_z
        assert not result.has_m
        assert len(result) == expected
    # End test_points method

    @mark.zm
    @mark.parametrize('fc_name, extent', [
        ('mb_boxes_a', (-1525279.375, 1374077.125, -962867.9375, 1991558.375)),
        ('mb_lines_l', (-1686072.875, 1209916.375, -909135.4375, 1753811.125)),
        ('mb_points_p', (-1993130.625, 1041480.75, -758687.0625, 1959262.5)),
    ])
    @mark.parametrize('overlap', [
        True, False
    ])
    @mark.parametrize('only', [
        True, False
    ])
    def test_output_settings(self, mem_gpkg, buffering, fc_name, extent, overlap, only):
        """
        Test Buffering with Z output and M output + reprojecting features
        """
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_buffer')
        with (Swap(Setting.EXTENT, Extent.from_bounds(-120, 35, -100, 60, crs=CRS(4326))),
              Swap(Setting.OUTPUT_M_OPTION, OutputMOption.ENABLED),
              Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.ENABLED),
              Swap(Setting.Z_VALUE, 123.456),
              Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS.from_authority('ESRI', 102009))):
            result = multiple_buffer(
                source, target=target, distance_unit=DistanceUnit.MILES,
                distances=[5, 10, 20], buffer_type=BufferTypeOption.PLANAR,
                overlapping=overlap, only_outside=only,)
            assert result.has_z
            assert result.has_m
            assert result.spatial_reference_system.srs_id == 102009
            assert approx(result.extent, abs=1) == extent
    # End test_output_settings method
# End TestMultipleBuffer class


if __name__ == '__main__':  # pragma: no cover
    pass
