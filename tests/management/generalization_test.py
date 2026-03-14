# -*- coding: utf-8 -*-
"""
Tests for Generalization Data Management
"""


from fudgeo import FeatureClass
from pyproj import CRS
from pytest import mark, param, approx

from spyops.crs.constant import EPSG, ESRI
from spyops.environment import Extent, OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.environment.core import zm_config
from spyops.management.generalization import dissolve
from spyops.shared.stats import Average, Concatenate, First, Last, Mode
from tests.util import UseGrids

pytestmark = [mark.management, mark.generalization]


class TestDissolve:
    """
    Test Dissolve
    """
    @mark.slow
    @mark.parametrize('fc_name, as_multi_part, count', [
        ('admin_a', True, 313),
        ('admin_a', False, 208_366),
        ('admin_mp_a', True, 313),
        ('admin_mp_a', False, 208_366),
    ])
    def test_polygon(self, world_features, mem_gpkg, fc_name, as_multi_part, count):
        """
        Test dissolve using polygons
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        fields = 'CONTINENT', 'COUNTRY', 'DISPUTED'
        stats = (First('LAND_TYPE'), Last('LAND_TYPE'), Mode('LAND_RANK'),
                 Concatenate('LAND_RANK'))
        result = dissolve(
            source, target=target, group_fields=fields, statistics=stats,
            as_multi_part=as_multi_part)
        assert result.is_multi_part is as_multi_part
        assert len(result) == count
    # End test_polygon method

    @mark.parametrize('fc_name, as_multi_part, count', [
        ('admin_a', True, 20),
        ('admin_a', False, 51),
        ('admin_mp_a', True, 20),
        ('admin_mp_a', False, 86),
    ])
    @mark.parametrize('xy_tolerance', [
        None,
        param(0.000_001, marks=mark.slow),
    ])
    def test_polygon_extent(self, world_features, mem_gpkg, fc_name, as_multi_part, count, xy_tolerance):
        """
        Test dissolve using polygons and Extent
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        fields = 'CONTINENT', 'COUNTRY', 'DISPUTED'
        stats = (First('LAND_TYPE'), Last('LAND_TYPE'), Mode('LAND_RANK'),
                 Concatenate('LAND_RANK'))
        with Swap(Setting.EXTENT, Extent.from_bounds(-12.5, 7, 15, 27, crs=CRS(4326))):
            result = dissolve(
                source, target=target, group_fields=fields, statistics=stats,
                as_multi_part=as_multi_part, xy_tolerance=xy_tolerance)
        assert result.is_multi_part is as_multi_part
        assert len(result) == count
    # End test_polygon_extent method

    @mark.parametrize('fc_name, as_multi_part, count', [
        ('airports_p', True, 191),
        ('airports_p', False, 3500),
        ('airports_mp_p', True, 191),
        ('airports_mp_p', False, 3500),
    ])
    @mark.parametrize('xy_tolerance', [
        None,
        0.000_001,
    ])
    def test_point(self, world_features, mem_gpkg, fc_name, as_multi_part, count, xy_tolerance):
        """
        Test dissolve using points
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        fields = 'ISO_CC',
        stats = Average(source.primary_key_field),
        result = dissolve(
            source, target=target, group_fields=fields, statistics=stats,
            as_multi_part=as_multi_part, xy_tolerance=xy_tolerance)
        assert result.is_multi_part is as_multi_part
        assert len(result) == count
    # End test_point method

    @mark.parametrize('fc_name, as_multi_part, count', [
        ('airports_p', True, 11),
        ('airports_p', False, 28),
        ('airports_mp_p', True, 15),
        ('airports_mp_p', False, 1917),
    ])
    @mark.parametrize('xy_tolerance', [
        None,
        0.000_001,
    ])
    def test_point_extent(self, world_features, mem_gpkg, fc_name, as_multi_part, count, xy_tolerance):
        """
        Test dissolve using points and Extent
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        fields = 'ISO_CC',
        stats = Average(source.primary_key_field),
        with Swap(Setting.EXTENT, Extent.from_bounds(-12.5, 7, 15, 27, crs=CRS(4326))):
            result = dissolve(
                source, target=target, group_fields=fields, statistics=stats,
                as_multi_part=as_multi_part, xy_tolerance=xy_tolerance)
        assert result.is_multi_part is as_multi_part
        assert len(result) == count
    # End test_point_extent method

    @mark.slow
    @mark.parametrize('fc_name, as_multi_part, count', [
        ('roads_l', True, 198),
        ('roads_l', False, 126_339),
        ('roads_mp_l', True, 198),
        ('roads_mp_l', False, 106_132),
    ])
    def test_line(self, world_features, mem_gpkg, fc_name, as_multi_part, count):
        """
        Test dissolve using lines
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        fields = 'ISO_CC',
        stats = Average(source.primary_key_field),
        result = dissolve(
            source, target=target, group_fields=fields, statistics=stats,
            as_multi_part=as_multi_part)
        assert result.is_multi_part is as_multi_part
        assert len(result) == count
    # End test_line method

    @mark.parametrize('fc_name, as_multi_part, count', [
        ('roads_l', True, 18),
        ('roads_l', False, 1335),
        param('roads_mp_l', True, 23, marks=mark.slow),
        param('roads_mp_l', False, 28_236, marks=mark.slow),
    ])
    @mark.parametrize('xy_tolerance', [
        0.000_001,
    ])
    def test_line_extent(self, world_features, mem_gpkg, fc_name, as_multi_part, count, xy_tolerance):
        """
        Test dissolve using lines and Extent
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        fields = 'ISO_CC',
        stats = Average(source.primary_key_field),
        with Swap(Setting.EXTENT, Extent.from_bounds(-12.5, 7, 15, 27, crs=CRS(4326))):
            result = dissolve(
                source, target=target, group_fields=fields, statistics=stats,
                as_multi_part=as_multi_part, xy_tolerance=xy_tolerance)
        assert result.is_multi_part is as_multi_part
        assert len(result) == count
    # End test_line_extent method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent, count', [
        ('hydro_4617_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0), 6),
        ('hydro_4617_zm_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0), 6),
        ('transmission_4617_m_l', EPSG, 2955, False, (674555.1875, 5652839.5, 710282.9375, 5681615.5), 4),
        ('transmission_4617_z_l', EPSG, 2955, False, (674555.1875, 5652839.5, 710282.9375, 5681615.5), 4),
        ('toponymy_4617_m_p', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0), 1),
        ('toponymy_4617_z_p', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0), 1),
        ('hydro_4617_a', ESRI, 102179, False, (35000.796875, 5647522.5, 70211.8828125, 5675482.0), 6),
        ('hydro_4617_zm_a', ESRI, 102179, False, (35000.796875, 5647522.5, 70211.8828125, 5675482.0), 6),
        ('transmission_4617_m_l', ESRI, 102179, False, (34973.9453125, 5647476.0, 70037.765625, 5675522.0), 4),
        ('transmission_4617_z_l', ESRI, 102179, False, (34973.9453125, 5647476.0, 70037.765625, 5675522.0), 4),
        ('toponymy_4617_m_p', ESRI, 102179, False, (35596.453125, 5647816.0, 70112.4921875, 5675320.0), 1),
        ('toponymy_4617_z_p', ESRI, 102179, False, (35596.453125, 5647816.0, 70112.4921875, 5675320.0), 1),
        ('hydro_4617_a', ESRI, 102179, True, (34997.60546875, 5647514.0, 70209.1640625, 5675475.0), 6),
        ('hydro_4617_zm_a', ESRI, 102179, True, (34997.60546875, 5647514.0, 70209.1640625, 5675475.0), 6),
        ('transmission_4617_m_l', ESRI, 102179, True, (34970.6953125, 5647467.0, 70035.03125, 5675514.0), 4),
        ('transmission_4617_z_l', ESRI, 102179, True, (34970.6953125, 5647467.0, 70035.03125, 5675514.0), 4),
        ('toponymy_4617_m_p', ESRI, 102179, True, (35593.41796875, 5647808.0, 70109.640625, 5675312.5), 1),
        ('toponymy_4617_z_p', ESRI, 102179, True, (35593.41796875, 5647808.0, 70109.640625, 5675312.5), 1),
    ])
    @mark.parametrize('output_z', [
        OutputZOption.SAME,
        param(OutputZOption.ENABLED, marks=mark.large),
        param(OutputZOption.DISABLED, marks=mark.large),
    ])
    @mark.parametrize('output_m', [
        OutputMOption.SAME,
        param(OutputMOption.ENABLED, marks=mark.large),
        param(OutputMOption.DISABLED, marks=mark.large),
    ])
    def test_output_crs(self, ntdb_zm_small, mem_gpkg, fc_name, auth_name,
                        srs_id, flag, extent, count, output_z, output_m):
        """
        Test select with output CRS and different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        fields = 'ENTITY', 'ENTITY_NAME', 'DATANAME'
        stats = Average('ACCURACY'),
        crs = CRS.from_authority(auth_name=auth_name, code=srs_id)
        with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs),
              Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m),
              Swap(Setting.Z_VALUE, 123.456),
              UseGrids(flag)):
            zm = zm_config(source)
            result = dissolve(
                source, target=target, group_fields=fields, statistics=stats)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert len(result) == count
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs method
# End TestDissolve class


if __name__ == '__main__':  # pragma: no cover
    pass
