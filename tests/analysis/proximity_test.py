# -*- coding: utf-8 -*-
"""
Tests for Proximity
"""

from fudgeo import FeatureClass
from pyproj import CRS
from pytest import mark, param

from spyops.analysis import buffer
from spyops.crs.unit import DecimalDegrees, Kilometers, Meters
from spyops.environment import Extent, Setting
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
# End TestBufferDissolveList class


if __name__ == '__main__':  # pragma: no cover
    pass
