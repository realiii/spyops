# -*- coding: utf-8 -*-
"""
Test Extraction
"""


from math import nan
from sqlite3 import OperationalError

from fudgeo import FeatureClass, Field, GeoPackage, Table
from fudgeo.enumeration import ShapeType, FieldType
from numpy import array, isnan
from pyproj import CRS
from pytest import approx, mark, param, raises

from spyops.analysis.extract import (
    clip, select, split, split_by_attributes, table_select)
from spyops.environment import Extent
from spyops.environment.core import zm_config
from spyops.environment.enumeration import (
    OutputMOption, OutputZOption, Setting)
from spyops.shared.constant import EPSG, ESRI
from spyops.shared.exception import OperationsError
from spyops.environment.context import Swap
from spyops.shared.util import element_names, make_unique_name
from tests.util import UseGrids


pytestmark = [mark.extract]


class TestTableSelect:
    """
    Test Table Select
    """
    @mark.parametrize('table_name, where_clause, count', [
        ('admin', None, 5824),
        ('admin', '', 5824),
        ('admin', 'ISO_CC = "BR"', 62),
        ('disputed_boundaries', None, 561),
        ('disputed_boundaries', '', 561),
        ('disputed_boundaries', 'Description = "Disputed Boundary"', 364),
        ('cities', None, 2540),
        ('cities', '', 2540),
        ('cities', 'POP IS NULL', 1377),
        ('cities', 'POP < 0', 0),
    ])
    def test_table_select(self, world_tables, mem_gpkg, table_name, where_clause, count):
        """
        Test table_select
        """
        source = world_tables[table_name]
        target = Table(geopackage=mem_gpkg, name=table_name)
        result = table_select(source=source, target=target, where_clause=where_clause)
        assert len(result) == count
    # End test_table_select method

    def test_overwrite(self, world_tables, mem_gpkg):
        """
        Test table_select that exercises overwrite
        """
        source = world_tables['admin']
        where_clause = 'ISO_CC = "BR"'
        count = 62
        target = Table(geopackage=mem_gpkg, name=source.name)
        result = table_select(source=source, target=target, where_clause=where_clause)
        assert len(result) == count

        with raises(OperationsError):
            table_select(source=source, target=target, where_clause=where_clause)

        with Swap(Setting.OVERWRITE, True):
            result = table_select(source=source, target=target, where_clause=where_clause)
        assert len(result) == count
    # End test_overwrite method

    @mark.parametrize('table_name, where_clause', [
        ('admin', 'ISO = "BR"'),
        ('disputed_boundaries', 'Description = "Disputed Boundary'),
        ('cities', 'POP ISNULL()'),
        ('cities', 'POP <<>> 0'),
    ])
    def test_bad_sql(self, world_tables, mem_gpkg, table_name, where_clause):
        """
        Test table_select bad SQL
        """
        source = world_tables[table_name]
        target = Table(geopackage=mem_gpkg, name=table_name)
        with raises(OperationsError):
            table_select(source=source, target=target, where_clause=where_clause)
    # End test_bad_sql method
# End TestTableSelect class


class TestSelect:
    """
    Test Select
    """
    @mark.parametrize('fc_name, where_clause, count', [
        ('lakes_a', None, 39),
        ('lakes_a', '', 39),
        ('lakes_a', 'SQKM > 5000', 28),
        ('disputed_boundaries_l', None, 561),
        ('disputed_boundaries_l', '', 561),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary"', 364),
        ('cities_p', None, 2540),
        ('cities_p', '', 2540),
        ('cities_p', 'POP IS NULL', 1377),
        ('cities_p', 'POP < 0', 0),
    ])
    def test_select(self, world_features, mem_gpkg, fc_name, where_clause, count):
        """
        Test select
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = select(source=source, target=target, where_clause=where_clause)
        assert len(result) == count
    # End test_select method

    @mark.parametrize('fc_name, where_clause, count', [
        ('lakes_a', None, 7),
        ('lakes_a', '', 7),
        ('lakes_a', 'SQKM > 5000', 5),
        ('disputed_boundaries_l', None, 40),
        ('disputed_boundaries_l', '', 40),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary"', 40),
        ('cities_p', None, 310),
        ('cities_p', '', 310),
        ('cities_p', 'POP IS NULL', 241),
        ('cities_p', 'POP > 0', 69),
    ])
    def test_extent(self, world_features, mem_gpkg, fc_name, where_clause, count):
        """
        Test select with Extent
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with Swap(Setting.EXTENT, Extent.from_bounds(0, -20, 45, 30, CRS(4326))):
            result = select(source=source, target=target, where_clause=where_clause)
            assert len(result) == count
    # End test_extent method

    @mark.zm
    @mark.parametrize('fc_name, where_clause, output_z_option, output_m_option, count', [
        ('lakes_a', 'SQKM > 5000', OutputZOption.SAME, OutputMOption.SAME, 28),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary"', OutputZOption.SAME, OutputMOption.SAME, 364),
        ('cities_p', 'POP IS NULL', OutputZOption.SAME, OutputMOption.SAME, 1377),
        ('lakes_a', 'SQKM > 5000', OutputZOption.ENABLED, OutputMOption.ENABLED, 28),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary"', OutputZOption.ENABLED, OutputMOption.ENABLED, 364),
        ('cities_p', 'POP IS NULL', OutputZOption.ENABLED, OutputMOption.ENABLED, 1377),
        ('lakes_a', 'SQKM > 5000', OutputZOption.DISABLED, OutputMOption.DISABLED, 28),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary"', OutputZOption.DISABLED, OutputMOption.DISABLED, 364),
        ('cities_p', 'POP IS NULL', OutputZOption.DISABLED, OutputMOption.DISABLED, 1377),
    ])
    def test_zm(self, world_features, mem_gpkg, fc_name, where_clause, output_z_option, output_m_option, count):
        """
        Test select with ZM settings
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z_option),
              Swap(Setting.OUTPUT_M_OPTION, output_m_option),
              Swap(Setting.Z_VALUE, 123.456)):
            zm = zm_config(source)
            result = select(source=source, target=target, where_clause=where_clause)
        assert len(result) == count
        assert target.has_z == zm.z_enabled
        assert target.has_m == zm.m_enabled
    # End test_zm method

    def test_sans_attrs(self, inputs, world_features, mem_gpkg):
        """
        Test select sans attributes
        """
        where_clause = 'fid <= 10'
        fc_name = 'intersect_sans_attr_a'
        source = inputs[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = select(source=source, target=target, where_clause=where_clause)
        assert len(result) == 5
        fc_name = 'admin_sans_attr_a'
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = select(source=source, target=target, where_clause=where_clause)
        assert len(result) == 10
    # End test_sans_attrs method

    @mark.parametrize('fc_name, where_clause', [
        ('admin_a', 'ISO = "BR"'),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary'),
        ('cities_p', 'POP ISNULL()'),
        ('cities_p', 'POP <<>> 0'),
    ])
    def test_bad_sql(self, world_features, mem_gpkg, fc_name, where_clause):
        """
        Test select bad SQL
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with raises(OperationalError):
            select(source=source, target=target, where_clause=where_clause)
    # End test_bad_sql method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('hydro_4617_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('hydro_4617_zm_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('transmission_4617_m_l', EPSG, 2955, False, (674555.1875, 5652839.5, 710282.9375, 5681615.5)),
        ('transmission_4617_z_l', EPSG, 2955, False, (674555.1875, 5652839.5, 710282.9375, 5681615.5)),
        ('toponymy_4617_m_p', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0)),
        ('toponymy_4617_z_p', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0)),
        ('hydro_4617_a', ESRI, 102179, False, (35000.796875, 5647522.5, 70211.8828125, 5675482.0)),
        ('hydro_4617_zm_a', ESRI, 102179, False, (35000.796875, 5647522.5, 70211.8828125, 5675482.0)),
        ('transmission_4617_m_l', ESRI, 102179, False, (34973.9453125, 5647476.0, 70037.765625, 5675522.0)),
        ('transmission_4617_z_l', ESRI, 102179, False, (34973.9453125, 5647476.0, 70037.765625, 5675522.0)),
        ('toponymy_4617_m_p', ESRI, 102179, False, (35596.453125, 5647816.0, 70112.4921875, 5675320.0)),
        ('toponymy_4617_z_p', ESRI, 102179, False, (35596.453125, 5647816.0, 70112.4921875, 5675320.0)),
        ('hydro_4617_a', ESRI, 102179, True, (34997.60546875, 5647514.0, 70209.1640625, 5675475.0)),
        ('hydro_4617_zm_a', ESRI, 102179, True, (34997.60546875, 5647514.0, 70209.1640625, 5675475.0)),
        ('transmission_4617_m_l', ESRI, 102179, True, (34970.6953125, 5647467.0, 70035.03125, 5675514.0)),
        ('transmission_4617_z_l', ESRI, 102179, True, (34970.6953125, 5647467.0, 70035.03125, 5675514.0)),
        ('toponymy_4617_m_p', ESRI, 102179, True, (35593.41796875, 5647808.0, 70109.640625, 5675312.5)),
        ('toponymy_4617_z_p', ESRI, 102179, True, (35593.41796875, 5647808.0, 70109.640625, 5675312.5)),
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
                        srs_id, flag, extent, output_z, output_m):
        """
        Test select with output CRS and different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        crs = CRS.from_authority(auth_name=auth_name, code=srs_id)
        with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs),
              Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m),
              UseGrids(flag)):
            zm = zm_config(source)
            result = select(source=source, target=target)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert len(result) == len(source)
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name', [
        param('hydro_6654_a', marks=mark.large),
        param('hydro_6654_m_a', marks=mark.large),
        'hydro_6654_z_a',
        'hydro_6654_zm_a',
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
    def test_output_crs_include_vertical(self, ntdb_zm_small, mem_gpkg, fc_name, output_z, output_m):
        """
        Test select with output compound CRS coming from a compound CRS
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        srs_id = 6893
        crs = CRS(srs_id)
        assert crs.is_compound
        with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs),
              Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m),
              UseGrids(True)):
            zm = zm_config(source)
            result = select(source=source, target=target)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert len(result) == len(source)
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs_include_vertical method
# End TestSelect class


class TestSplitByAttributes:
    """
    Test Split By Attributes
    """
    @mark.parametrize('fields, split_count, total_count', [
        (Field('ISO_CC', data_type='TEXT'), 224, 5824),
        param((Field('ISO_CC', data_type='TEXT'), Field('LAND_TYPE', data_type='TEXT')), 580, 5824, marks=mark.slow),
        param('ISO_CC', 224, 5824, marks=mark.slow),
        param(('ISO_CC', 'LAND_TYPE'), 580, 5824, marks=mark.slow),
    ])
    def test_records(self, world_tables, mem_gpkg, fields, split_count, total_count):
        """
        Test split_by_attributes for tables
        """
        source = world_tables['admin']
        results = split_by_attributes(source, group_fields=fields, geopackage=mem_gpkg)
        assert len(results) == split_count
        assert sum([len(r) for r in results]) == total_count
    # End test_records method

    @mark.parametrize('fields, split_count, total_count', [
        (Field('ISO_CC', data_type='TEXT'), 7, 49),
        ((Field('ISO_CC', data_type='TEXT'), Field('LAND_TYPE', data_type='TEXT')), 7, 49),
        ('ISO_CC', 7, 49),
        (('ISO_CC', 'LAND_TYPE'), 7, 49),
    ])
    def test_features(self, world_features, mem_gpkg, fields, split_count, total_count):
        """
        Test split_by_attributes for feature classes
        """
        source = world_features['admin_a']
        with Swap(Setting.EXTENT, Extent.from_bounds(20, 0, 30, 20, crs=CRS(4326))):
            results = split_by_attributes(source, group_fields=fields, geopackage=mem_gpkg)
            assert len(results) == split_count
            assert sum([len(r) for r in results]) == total_count
    # End test_features method

    @mark.zm
    @mark.parametrize('fields, output_z_option, output_m_option, count', [
        (('ISO_CC', 'LAND_TYPE'), OutputZOption.SAME, OutputMOption.SAME, 7),
        (('ISO_CC', 'LAND_TYPE'), OutputZOption.ENABLED, OutputMOption.ENABLED, 7),
        (('ISO_CC', 'LAND_TYPE'), OutputZOption.DISABLED, OutputMOption.DISABLED, 7),
    ])
    def test_features_zm(self, world_features, mem_gpkg, fields,
                                             output_z_option, output_m_option, count):
        """
        Test split_by_attributes for feature classes with ZM settings
        """
        subset = 120
        source = world_features['admin_a']
        names = element_names(world_features)
        source = source.copy(
            make_unique_name(source.name, names=names),
            where_clause=f"""fid <= {subset}""", geopackage=mem_gpkg)

        with (Swap(Setting.OUTPUT_Z_OPTION, output_z_option),
              Swap(Setting.OUTPUT_M_OPTION, output_m_option),
              Swap(Setting.Z_VALUE, 123.456)):
            zm = zm_config(source)
            results = split_by_attributes(source, group_fields=fields, geopackage=mem_gpkg)
        assert len(results) == count
        assert sum([len(r) for r in results]) == subset
        assert all([target.has_z == zm.z_enabled for target in results])
        assert all([target.has_m == zm.m_enabled for target in results])
    # End test_features_zm method

    def test_features_sans_attributes(self, world_features, mem_gpkg):
        """
        Test split_by_attributes for feature classes sans attributes
        """
        count = 15
        source = world_features['admin_sans_attr_a']
        names = element_names(world_features)
        source = source.copy(
            make_unique_name(source.name, names=names),
            where_clause=f"""fid <= {count}""", geopackage=mem_gpkg)
        results = split_by_attributes(source, group_fields=['fid'], geopackage=mem_gpkg)
        assert len(results) == count
        assert sum([len(r) for r in results]) == count
    # End test_features_sans_attributes method

    @mark.parametrize('fields, count', [
        (Field('ISO_CC', data_type='TEXT'), 3),
        ((Field('ISO_CC', data_type='TEXT'), Field('LAND_TYPE', data_type='TEXT')), 7),
        ('ISO_CC', 3),
        (('ISO_CC', 'LAND_TYPE'), 7),
    ])
    def test_features_with_settings(self, world_features, mem_gpkg, fields, count):
        """
        Test split_by_attributes for feature classes with analysis settings
        """
        subset = 120
        source = world_features['admin_a']
        names = element_names(world_features)
        source = source.copy(
            make_unique_name(source.name, names=names),
            where_clause=f"""fid <= {subset}""", geopackage=mem_gpkg)
        with Swap(Setting.CURRENT_WORKSPACE, mem_gpkg):
            results = split_by_attributes(source.name, group_fields=fields, geopackage=None)
        assert len(results) == count
        assert sum([len(r) for r in results]) == subset
    # End test_features_with_settings method

    @mark.benchmark
    @mark.parametrize('fix_name, name, fields, count', [
        ('inputs', 'utmzone_continentish_a', ('ZONE', 'ROW_'), 708),
        ('inputs', 'utmzone_sparse_a', ('ZONE', 'ROW_'), 228),
        ('world_features', 'admin_a', ('COUNTRY', 'ISO_CC', 'ADMINTYPE'), 376),
    ])
    def test_larger_inputs(self, request, inputs, mem_gpkg, fix_name, name, fields, count):
        """
        Test split by attributes using larger inputs
        """
        source = request.getfixturevalue(fix_name)[name]
        results = split_by_attributes(
            source=source, group_fields=fields, geopackage=mem_gpkg)
        assert len(results) == count
    # End test_larger_inputs method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('hydro_4617_a', EPSG, 2955, False, (674655.0625, 5653408.0, 709947.5, 5681614.0)),
        ('hydro_4617_zm_a', EPSG, 2955, False, (674655.0625, 5653408.0, 709947.5, 5681614.0)),
        ('transmission_4617_m_l', EPSG, 2955, False, (674755.125, 5653806.0, 710282.9375, 5680738.5)),
        ('transmission_4617_z_l', EPSG, 2955, False, (674755.125, 5653806.0, 710282.9375, 5680738.5)),
        ('toponymy_4617_m_p', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0)),
        ('toponymy_4617_z_p', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0)),
        ('hydro_4617_a', ESRI, 102179, False, (35142.88671875, 5647703.0, 70034.015625, 5675482.0)),
        ('hydro_4617_zm_a', ESRI, 102179, False, (35142.88671875, 5647703.0, 70034.015625, 5675482.0)),
        ('transmission_4617_m_l', ESRI, 102179, False, (35012.9609375, 5647727.0, 70037.765625, 5674590.0)),
        ('transmission_4617_z_l', ESRI, 102179, False, (35012.9609375, 5647727.0, 70037.765625, 5674590.0)),
        ('toponymy_4617_m_p', ESRI, 102179, False, (35596.453125, 5647816.0, 70112.4921875, 5675320.0)),
        ('toponymy_4617_z_p', ESRI, 102179, False, (35596.453125, 5647816.0, 70112.4921875, 5675320.0)),
        ('hydro_4617_a', ESRI, 102179, True, (35139.65625, 5647695.0, 70031.140625, 5675475.0)),
        ('hydro_4617_zm_a', ESRI, 102179, True, (35139.65625, 5647695.0, 70031.140625, 5675475.0)),
        ('transmission_4617_m_l', ESRI, 102179, True, (35009.80859375, 5647718.5, 70035.03125, 5674582.5)),
        ('transmission_4617_z_l', ESRI, 102179, True, (35009.80859375, 5647718.5, 70035.03125, 5674582.5)),
        ('toponymy_4617_m_p', ESRI, 102179, True, (35593.41796875, 5647808.0, 70109.640625, 5675312.5)),
        ('toponymy_4617_z_p', ESRI, 102179, True, (35593.41796875, 5647808.0, 70109.640625, 5675312.5)),
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
    def test_output_crs(self, ntdb_zm_small, mem_gpkg, fc_name, auth_name, srs_id, flag, extent, output_z, output_m):
        """
        Test split by attributes with output CRS and different input
        spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        crs = CRS.from_authority(auth_name=auth_name, code=srs_id)
        with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs),
              Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m),
              UseGrids(flag)):
            zm = zm_config(source)
            result = split_by_attributes(source=source, group_fields='CODE', geopackage=mem_gpkg)
            first, *_ = result
            assert first.spatial_reference_system.srs_id == srs_id
            assert first.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(first.extent, abs=0.001) == extent
            assert first.has_z == zm.z_enabled
            assert first.has_m == zm.m_enabled
    # End test_output_crs method
# End TestSplitByAttributes class


class TestClip:
    """
    Test Clip
    """
    @mark.parametrize('fc_name, xy_tolerance, count', [
        ('admin_a', None, 89),
        ('airports_p', None, 35),
        param('roads_l', None, 2189, marks=mark.slow),
        ('admin_mp_a', None, 49),
        ('airports_mp_p', None, 4),
        param('roads_mp_l', None, 8, marks=mark.slow),
        ('admin_a', 0.001, 88),
        ('airports_p', 0.001, 35),
        param('roads_l', 0.001, 2319, marks=mark.slow),
        ('admin_mp_a', 0.001, 49),
        ('airports_mp_p', 0.001, 4),
        param('roads_mp_l', 0.001, 8, marks=mark.slow),
        ('admin_a', 1, 17),
        ('airports_p', 1, 32),
        param('roads_l', 1, 300, marks=mark.slow),
        ('admin_mp_a', 1, 17),
        ('airports_mp_p', 1, 4),
        param('roads_mp_l', 1, 8, marks=mark.slow),
    ])
    def test_clip(self, inputs, world_features, mem_gpkg, fc_name, xy_tolerance, count):
        """
        Test clip
        """
        clipper = inputs['clipper_a']
        assert len(clipper) == 3
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = clip(source=source, operator=clipper, target=target, xy_tolerance=xy_tolerance)
        assert len(result) < len(source)
        assert len(result) == count
    # End test_clip method

    def test_clip_sans_attributes(self, inputs, world_features, mem_gpkg):
        """
        Test clip sans attributes
        """
        clipper = inputs['intersect_sans_attr_a']
        assert len(clipper) == 5
        source = world_features['admin_sans_attr_a']
        target = FeatureClass(geopackage=mem_gpkg, name='sans')
        result = clip(source=source, operator=clipper, target=target)
        assert len(result) == 107
    # End test_clip_sans_attributes method

    @mark.parametrize('xy_tolerance, count', [
        (None, 195),
        (0.001, 209),
    ])
    def test_clip_line_on_line(self, world_features, inputs, mem_gpkg, xy_tolerance, count):
        """
        Test clipping using a line feature class as the operator on a line feature class
        """
        clipper = inputs['rivers_portion_l']
        source = world_features['rivers_l']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = clip(source=source, operator=clipper, target=target, xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_clip_line_on_line method

    @mark.parametrize('xy_tolerance, count', [
        param(None, 7398, marks=mark.slow),
        param(0, 7398, marks=mark.slow),
        (0.0000000001, 3),
        param(0.1, 0, marks=mark.slow),
    ])
    def test_clip_line_on_point(self, inputs, mem_gpkg, xy_tolerance, count):
        """
        Test clipping using a line feature class as the operator on a point feature class
        """
        clipper = inputs['rivers_portion_l']
        source = inputs['river_p']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = clip(source=source, operator=clipper, target=target, xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_clip_line_on_point method

    @mark.parametrize('xy_tolerance, count', [
        (None, 100),
        (0, 100),
        (0.001, 100),
    ])
    def test_clip_point_on_point(self, inputs, mem_gpkg, xy_tolerance, count):
        """
        Test clipping using a point feature class as the operator on a point feature class
        """
        clipper = inputs['river_p'].copy(name='river_p_clipper', where_clause='fid <= 100', geopackage=mem_gpkg)
        assert len(clipper) == 100
        source = inputs['river_p']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = clip(source=source, operator=clipper, target=target, xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_clip_point_on_point method

    @mark.parametrize('fc_name, xy_tolerance, count', [
        ('admin_a', None, 89),
        ('airports_p', None, 35),
        param('roads_l', None, 2189, marks=mark.slow),
        ('admin_mp_a', None, 49),
        ('airports_mp_p', None, 4),
        param('roads_mp_l', None, 8, marks=mark.slow),
        ('admin_a', 0.001, 88),
        ('airports_p', 0.001, 35),
        param('roads_l', 0.001, 2319, marks=mark.slow),
        ('admin_mp_a', 0.001, 49),
        ('airports_mp_p', 0.001, 4),
        param('roads_mp_l', 0.001, 8, marks=mark.slow),
        ('admin_a', 1, 17),
        ('airports_p', 1, 32),
        param('roads_l', 1, 300, marks=mark.slow),
        ('admin_mp_a', 1, 17),
        ('airports_mp_p', 1, 4),
        param('roads_mp_l', 1, 8, marks=mark.slow),
    ])
    def test_clip_setting(self, inputs, world_features, mem_gpkg, fc_name, xy_tolerance, count):
        """
        Test clip using analysis settings
        """
        clipper = inputs['clipper_a']
        assert len(clipper) == 3
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with Swap(Setting.XY_TOLERANCE, xy_tolerance):
            result = clip(source=source, operator=clipper, target=target)
        assert len(result) < len(source)
        assert len(result) == count
    # End test_clip_setting method

    @mark.benchmark
    @mark.parametrize('name, count', [
        ('utmzone_continentish_a', 200_915),
        ('utmzone_sparse_a', 26_602),
    ])
    def test_clip_larger_inputs(self, inputs, world_features, mem_gpkg, name, count):
        """
        Test clip using larger inputs
        """
        operator = inputs[name]
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name=name)
        result = clip(source=source, operator=operator, target=target)
        assert len(result) == count
    # End test_clip_larger_inputs method

    @mark.zm
    @mark.parametrize('fc_name', [
        'hydro_a',
        'structures_p',
        'structures_a',
        'structures_m_a',
        'structures_z_a',
        'structures_zm_a',
        'structures_ma',
        param('structures_m_ma', marks=mark.slow),
        param('structures_z_ma', marks=mark.slow),
        param('structures_zm_ma', marks=mark.slow),
        param('structures_vcs_z_ma', marks=mark.slow),
        param('structures_vcs_zm_ma', marks=mark.slow),
        param('structures_vcs_z_a', marks=mark.slow),
        param('structures_vcs_zm_a', marks=mark.slow),
        param('topography_l', marks=mark.slow),
        'toponymy_mp',
        'toponymy_z_mp',
        'toponymy_p',
        'toponymy_z_p',
        param('toponymy_vcs_z_p', marks=mark.large),
        param('toponymy_vcs_z_mp', marks=mark.large),
        'transmission_l',
        param('transmission_m_l', marks=mark.large),
        param('transmission_z_l', marks=mark.large),
        'transmission_zm_l',
        param('transmission_vcs_z_l', marks=mark.large),
        param('transmission_vcs_zm_l', marks=mark.large),
        'transmission_ml',
        param('transmission_vcs_z_ml', marks=mark.large),
        'transmission_p',
    ])
    @mark.parametrize('op_name', [
        'grid_a',
        param('grid_m_a', marks=mark.large),
        param('grid_z_a', marks=mark.large),
        param('grid_zm_a', marks=mark.large),
    ])
    @mark.parametrize('output_z', [
        OutputZOption.SAME,
        OutputZOption.ENABLED,
        OutputZOption.DISABLED,
    ])
    @mark.parametrize('output_m', [
        OutputMOption.SAME,
        OutputMOption.ENABLED,
        OutputMOption.DISABLED,
    ])
    def test_output_zm(self, grid_index, ntdb_zm_meh_small, mem_gpkg, fc_name, op_name, output_z, output_m):
        """
        Test clip using Output ZM settings
        """
        operator = grid_index[op_name]
        operator = operator.copy(
            name=op_name, where_clause="""DATANAME = '082O01-6'""",
            geopackage=mem_gpkg)
        source = ntdb_zm_meh_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_clipped')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            clipped = clip(source=source, operator=operator, target=target)
        assert clipped.has_z == zm.z_enabled
        assert clipped.has_m == zm.m_enabled
        assert len(clipped) <= len(source)
    # End test_output_zm method

    @mark.zm
    @mark.parametrize('fc_name', [
        'hydro_a',
        param('hydro_m_a', marks=mark.large),
        param('hydro_z_a', marks=mark.large),
        param('hydro_zm_a', marks=mark.large),
        'structures_a',
        param('structures_m_a', marks=mark.large),
        param('structures_z_a', marks=mark.large),
        param('structures_zm_a', marks=mark.large),
        param('structures_ma', marks=mark.large),
        param('structures_m_ma', marks=mark.large),
        param('structures_z_ma', marks=mark.large),
        'structures_zm_ma',
        'structures_p',
        param('structures_m_p', marks=mark.large),
        param('structures_z_p', marks=mark.large),
        'structures_zm_p',
        param('topography_l', marks=mark.slow),
        param('topography_m_l', marks=mark.slow),
        param('topography_z_l', marks=mark.slow),
        param('topography_zm_l', marks=mark.slow),
        param('toponymy_p', marks=mark.large),
        param('toponymy_m_p', marks=mark.large),
        param('toponymy_z_p', marks=mark.large),
        param('toponymy_zm_p', marks=mark.large),
        'toponymy_mp',
        param('toponymy_m_mp', marks=mark.large),
        param('toponymy_z_mp', marks=mark.large),
        'toponymy_zm_mp',
        param('transmission_p', marks=mark.large),
        'transmission_m_p',
        'transmission_z_p',
        param('transmission_zm_p', marks=mark.large),
        'transmission_l',
        param('transmission_m_l', marks=mark.large),
        param('transmission_z_l', marks=mark.large),
        'transmission_zm_l',
        'transmission_ml',
        param('transmission_m_ml', marks=mark.large),
        param('transmission_z_ml', marks=mark.large),
        'transmission_zm_ml',
        'transmission_mp',
        param('transmission_m_mp', marks=mark.large),
        param('transmission_z_mp', marks=mark.large),
        'transmission_zm_mp',
    ])
    @mark.parametrize('op_name', [
        'grid_a',
        param('grid_m_a', marks=mark.large),
        param('grid_z_a', marks=mark.large),
        param('grid_zm_a', marks=mark.large),
    ])
    @mark.parametrize('output_z', [
        OutputZOption.SAME,
        OutputZOption.ENABLED,
        OutputZOption.DISABLED,
    ])
    @mark.parametrize('output_m', [
        OutputMOption.SAME,
        OutputMOption.ENABLED,
        OutputMOption.DISABLED,
    ])
    def test_output_zm_cleaner(self, grid_index, ntdb_zm_small, mem_gpkg, fc_name, op_name, output_z, output_m):
        """
        Test clip using Output ZM settings using cleaner inputs
        """
        operator = grid_index[op_name]
        operator = operator.copy(
            name=op_name, where_clause="""DATANAME = '082O01-6'""",
            geopackage=mem_gpkg)
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_clipped')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            clipped = clip(source=source, operator=operator, target=target)
        assert clipped.has_z == zm.z_enabled
        assert clipped.has_m == zm.m_enabled
        assert len(clipped) <= len(source)
    # End test_output_zm_cleaner method

    @mark.zm
    @mark.parametrize('fc_name, op_name, z_value, expected', [
        ('hydro_a', 'grid_a', None, nan),
        ('structures_p', 'grid_a', None, nan),
        ('transmission_l', 'grid_a', None, nan),
        ('hydro_a', 'grid_a', nan, nan),
        ('structures_p', 'grid_a', nan, nan),
        ('transmission_l', 'grid_a', nan, nan),
        ('hydro_a', 'grid_a', 123, 123.),
        ('structures_p', 'grid_a', 234, 234.),
        ('transmission_l', 'grid_a', 345, 345.),
        ('hydro_a', 'grid_zm_a', None, nan),
        ('structures_p', 'grid_zm_a', None, nan),
        ('transmission_l', 'grid_zm_a', None, nan),
        ('hydro_a', 'grid_zm_a', nan, nan),
        ('structures_p', 'grid_zm_a', nan, nan),
        ('transmission_l', 'grid_zm_a', nan, nan),
        ('hydro_a', 'grid_zm_a', 123, 123.),
        ('structures_p', 'grid_zm_a', 234, 234.),
        ('transmission_l', 'grid_zm_a', 345, 345.),
    ])
    def test_output_z_value(self, grid_index, ntdb_zm_meh_small, mem_gpkg, fc_name, op_name, z_value, expected):
        """
        Test clip using output z value
        """
        operator = grid_index[op_name]
        operator = operator.copy(
            name=op_name, where_clause="""DATANAME = '082O01-6'""",
            geopackage=mem_gpkg)
        source = ntdb_zm_meh_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_clipped')
        with (Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.ENABLED),
              Swap(Setting.Z_VALUE, z_value)):
            clipped = clip(source=source, operator=operator, target=target)
        assert clipped.has_z is True
        assert clipped.has_m == source.has_z or operator.has_m
        if source.shape_type == ShapeType.point:
            z_values = array([pt.z for pt, in clipped.select()], dtype=float)
        elif source.shape_type == ShapeType.polygon:
            z_values = []
            for poly, in clipped.select():
                for ring in poly.rings:
                    z_values.extend(ring.coordinates[:, 2])
        else:
            z_values = []
            for line, in clipped.select():
                z_values.extend(line.coordinates[:, 2])
        if isnan(expected):
            assert all(isnan(z_values))
        else:
            assert approx(list(set(z_values))) == [expected]
    # End test_output_z_value method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('hydro_4617_a', EPSG, 2955, False, (692526.375, 5653596.5, 701490.4375, 5665959.5)),
        ('hydro_4617_zm_a', EPSG, 2955, False, (692526.375, 5653596.5, 701490.4375, 5665959.5)),
        ('transmission_4617_m_l', EPSG, 2955, False, (692509.5625, 5654147.0, 701508.4375, 5667420.5 )),
        ('transmission_4617_z_l', EPSG, 2955, False, (692509.5625, 5654147.0, 701508.4375, 5667420.5 )),
        ('toponymy_4617_m_p', EPSG, 2955, False, (693519.3125, 5654016.0, 701489.6875, 5666594.0)),
        ('toponymy_4617_z_p', EPSG, 2955, False, (693519.3125, 5654016.0, 701489.6875, 5666594.0)),
        ('hydro_4617_a', ESRI, 102179, False, (52561.53515625, 5647665.0, 61375.05078125, 5659934.5)),
        ('hydro_4617_zm_a', ESRI, 102179, False, (52561.53515625, 5647665.0, 61375.05078125, 5659934.5)),
        ('transmission_4617_m_l', ESRI, 102179, False, (52556.953125, 5648163.0, 61380.49609375, 5661534.5)),
        ('transmission_4617_z_l', ESRI, 102179, False, (52556.953125, 5648163.0, 61380.49609375, 5661534.5)),
        ('toponymy_4617_m_p', ESRI, 102179, False, (53556.5859375, 5647991.5, 61297.6328125, 5660650.5)),
        ('toponymy_4617_z_p', ESRI, 102179, False, (53556.5859375, 5647991.5, 61297.6328125, 5660650.5)),
        ('hydro_4617_a', ESRI, 102179, True, (52561.625, 5647659.5, 61375.1640625, 5659926.5)),
        ('hydro_4617_zm_a', ESRI, 102179, True, (52561.625, 5647659.5, 61375.1640625, 5659926.5)),
        ('transmission_4617_m_l', ESRI, 102179, True, (52557.04296875, 5648154.0, 61380.6171875, 5661554.0)),
        ('transmission_4617_z_l', ESRI, 102179, True, (52557.04296875, 5648154.0, 61380.6171875, 5661554.0)),
        ('toponymy_4617_m_p', ESRI, 102179, True, (53553.6328125, 5647982.5, 61294.859375, 5660642.5)),
        ('toponymy_4617_z_p', ESRI, 102179, True, (53553.6328125, 5647982.5, 61294.859375, 5660642.5)),
    ])
    @mark.parametrize('op_name', [
        'grid_10tm_a',
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
    def test_output_crs(self, ntdb_zm_small, grid_index, mem_gpkg,
                        fc_name, auth_name, srs_id, flag, extent, op_name,
                        output_z, output_m):
        """
        Test clip with output CRS and different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        crs = CRS.from_authority(auth_name=auth_name, code=srs_id)
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_clipped')
        operator = grid_index[op_name].copy(
            f'{op_name}_subset', geopackage=mem_gpkg,
            where_clause="""DATANAME = '082O01-6'""")
        with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs),
              Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m),
              UseGrids(flag)):
            zm = zm_config(source, operator)
            result = clip(source=source, operator=operator, target=target)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs method

    @mark.transform
    @mark.parametrize('fc_name, extent', [
        ('hydro_4617_a', (-114.25001525878906, 51.0, -114.125, 51.11003494262695)),
        ('hydro_6654_a', (692529.4375, 5653599.5, 701493.5, 5665959.5)),
        ('hydro_lcc_a', (-1260769.625, 1417430.0, -1250397.75, 1429655.5)),
        ('hydro_utm11_a', (692529.4375, 5653599.5, 701493.5, 5665959.5)),
    ])
    @mark.parametrize('op_name', [
        'grid_10tm_a',
    ])
    def test_different_crs(self, ntdb_zm_small, grid_index, mem_gpkg,
                           fc_name, extent, op_name):
        """
        Test clip with different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_clipped')
        operator = grid_index[op_name].copy(
            f'{op_name}_subset', geopackage=mem_gpkg,
            where_clause="""DATANAME = '082O01-6'""")
        with UseGrids(True):
            result = clip(source=source, operator=operator, target=target)
            srs_id = source.spatial_reference_system.srs_id
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
    # End test_different_crs method
# End TestClip class


class TestSplit:
    """
    Test Split
    """
    @mark.parametrize('fc_name, xy_tolerance, element_count, record_count', [
        ('admin_a', None, 4, 114),
        ('airports_p', None, 4, 40),
        param('roads_l', None, 4, 2514, marks=mark.slow),
        ('admin_mp_a', None, 4, 68),
        ('airports_mp_p', None, 4, 8),
        param('roads_mp_l', None, 4, 14, marks=mark.slow),
        ('admin_a', 0.001, 4, 112),
        ('airports_p', 0.001, 4, 40),
        param('roads_l', 0.001, 4, 2676, marks=mark.slow),
        ('admin_mp_a', 0.001, 4, 68),
        ('airports_mp_p', 0.001, 4, 8),
        param('roads_mp_l', 0.001, 4, 14, marks=mark.slow),
        ('admin_a', 1, 4, 22),
        ('airports_p', 1, 4, 35),
        param('roads_l', 1, 4, 345, marks=mark.slow),
        ('admin_mp_a', 1, 4, 22),
        ('airports_mp_p', 1, 4, 8),
        param('roads_mp_l', 1, 4, 13, marks=mark.slow),
    ])
    def test_split(self, inputs, world_features, mem_gpkg, fc_name, xy_tolerance, element_count, record_count):
        """
        Test split
        """
        splitter = inputs['splitter_a']
        assert len(splitter) == 5
        source = world_features[fc_name]
        field = Field('NAME', data_type=FieldType.text)
        results = split(source=source, operator=splitter, field=field,
                        geopackage=mem_gpkg, xy_tolerance=xy_tolerance)
        assert len(results) == element_count
        assert sum(len(r) for r in results) == record_count
    # End test_split method

    @mark.zm
    @mark.parametrize('fc_name, xy_tolerance, output_z_option, output_m_option, element_count, record_count', [
        ('admin_a', None, OutputZOption.SAME, OutputMOption.SAME, 4, 114),
        ('airports_p', None, OutputZOption.SAME, OutputMOption.SAME, 4, 40),
        ('roads_l', None, OutputZOption.SAME, OutputMOption.SAME, 4, 2514),
        ('admin_mp_a', None, OutputZOption.SAME, OutputMOption.SAME, 4, 68),
        ('airports_mp_p', None, OutputZOption.SAME, OutputMOption.SAME, 4, 8),
        param('roads_mp_l', None, OutputZOption.SAME, OutputMOption.SAME, 4, 14, marks=mark.slow),
        ('admin_a', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 4, 114),
        ('airports_p', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 4, 40),
        ('roads_l', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 4, 2514),
        ('admin_mp_a', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 4, 68),
        ('airports_mp_p', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 4, 8),
        param('roads_mp_l', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 4, 14, marks=mark.slow),
        ('admin_a', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 4, 114),
        ('airports_p', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 4, 40),
        ('roads_l', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 4, 2514),
        ('admin_mp_a', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 4, 68),
        ('airports_mp_p', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 4, 8),
        param('roads_mp_l', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 4, 14, marks=mark.slow),
    ])
    def test_split_zm(self, inputs, world_features, mem_gpkg, fc_name, xy_tolerance,
                      output_z_option, output_m_option, element_count, record_count):
        """
        Test split using ZM settings
        """
        splitter = inputs['splitter_a']
        assert len(splitter) == 5
        source = world_features[fc_name]
        field = Field('NAME', data_type=FieldType.text)
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z_option),
              Swap(Setting.OUTPUT_M_OPTION, output_m_option),
              Swap(Setting.Z_VALUE, 123.456)):
            zm = zm_config(source, splitter)
            results = split(source=source, operator=splitter, field=field,
                            geopackage=mem_gpkg, xy_tolerance=xy_tolerance)
        assert len(results) == element_count
        assert sum(len(r) for r in results) == record_count
        assert all([target.has_z == zm.z_enabled for target in results])
        assert all([target.has_m == zm.m_enabled for target in results])
    # End test_split_zm method

    @mark.parametrize('fc_name, xy_tolerance, element_count, record_count', [
        ('admin_a', None, 4, 114),
        ('airports_p', None, 4, 40),
        ('roads_l', None, 4, 2514),
        ('admin_mp_a', None, 4, 68),
        ('airports_mp_p', None, 4, 8),
        param('roads_mp_l', None, 4, 14, marks=mark.slow),
        ('admin_a', 0.001, 4, 112),
        ('airports_p', 0.001, 4, 40),
        ('roads_l', 0.001, 4, 2676),
        ('admin_mp_a', 0.001, 4, 68),
        ('airports_mp_p', 0.001, 4, 8),
        param('roads_mp_l', 0.001, 4, 14, marks=mark.slow),
    ])
    def test_split_setting(self, tmp_path, inputs, world_features, mem_gpkg,
                           fc_name, xy_tolerance, element_count, record_count):
        """
        Test split using analysis settings
        """
        splitter = inputs['splitter_a']
        assert len(splitter) == 5
        source = world_features[fc_name]
        field = Field('NAME', data_type=FieldType.text)
        gpkg = GeoPackage.create(tmp_path / 'test_scratch.gpkg')
        with (Swap(Setting.XY_TOLERANCE, xy_tolerance),
              Swap(Setting.CURRENT_WORKSPACE, mem_gpkg),
              Swap(Setting.SCRATCH_WORKSPACE, gpkg)):
            results = split(source=source, operator=splitter, field=field, geopackage=None)
        assert len(results) == element_count
        assert sum(len(r) for r in results) == record_count
    # End test_split_setting method

    @mark.zm
    @mark.parametrize('fc_name', [
        'hydro_a',
        'structures_p',
        'structures_a',
        'structures_m_a',
        'structures_z_a',
        'structures_zm_a',
        'structures_ma',
        param('structures_m_ma', marks=mark.slow),
        param('structures_z_ma', marks=mark.slow),
        param('structures_zm_ma', marks=mark.slow),
        param('structures_vcs_z_ma', marks=mark.slow),
        param('structures_vcs_zm_ma', marks=mark.slow),
        param('structures_vcs_z_a', marks=mark.slow),
        param('structures_vcs_zm_a', marks=mark.slow),
        param('topography_l', marks=mark.slow),
        'toponymy_mp',
        'toponymy_z_mp',
        'toponymy_p',
        'toponymy_z_p',
        param('toponymy_vcs_z_p', marks=mark.large),
        param('toponymy_vcs_z_mp', marks=mark.large),
        'transmission_l',
        param('transmission_m_l', marks=mark.large),
        param('transmission_z_l', marks=mark.large),
        'transmission_zm_l',
        param('transmission_vcs_z_l', marks=mark.large),
        param('transmission_vcs_zm_l', marks=mark.large),
        'transmission_ml',
        param('transmission_vcs_z_ml', marks=mark.large),
        'transmission_p',
    ])
    @mark.parametrize('op_name', [
        'grid_a',
        param('grid_m_a', marks=mark.large),
        param('grid_z_a', marks=mark.large),
        param('grid_zm_a', marks=mark.large),
    ])
    @mark.parametrize('output_z', [
        param(OutputZOption.SAME, marks=mark.large),
        OutputZOption.ENABLED,
        param(OutputZOption.DISABLED, marks=mark.large),
    ])
    @mark.parametrize('output_m', [
        param(OutputMOption.SAME, marks=mark.large),
        OutputMOption.ENABLED,
        param(OutputMOption.DISABLED, marks=mark.large),
    ])
    def test_output_zm(self, grid_index, ntdb_zm_meh_small, mem_gpkg,
                       fc_name, op_name, output_z, output_m):
        """
        Test split using Output ZM settings
        """
        operator = grid_index[op_name]
        operator = operator.copy(
            name=op_name,
            where_clause="""DATANAME IN ('082O01-6', '082O01-7', '082O01-8')""",
            geopackage=mem_gpkg)
        source = ntdb_zm_meh_small[fc_name]
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            results = split(source=source, operator=operator, field='DATANAME', geopackage=mem_gpkg)
        assert len(results) == 3
        result, *_ = results
        assert result.has_z == zm.z_enabled
        assert result.has_m == zm.m_enabled
    # End test_output_zm method

    @mark.zm
    @mark.parametrize('fc_name', [
        'hydro_a',
        param('hydro_m_a', marks=mark.large),
        param('hydro_z_a', marks=mark.large),
        param('hydro_zm_a', marks=mark.large),
        'structures_a',
        param('structures_m_a', marks=mark.large),
        param('structures_z_a', marks=mark.large),
        param('structures_zm_a', marks=mark.large),
        param('structures_ma', marks=mark.large),
        param('structures_m_ma', marks=mark.large),
        param('structures_z_ma', marks=mark.large),
        'structures_zm_ma',
        'structures_p',
        param('structures_m_p', marks=mark.large),
        param('structures_z_p', marks=mark.large),
        'structures_zm_p',
        param('topography_l', marks=mark.slow),
        param('topography_m_l', marks=mark.slow),
        param('topography_z_l', marks=mark.slow),
        param('topography_zm_l', marks=mark.slow),
        param('toponymy_p', marks=mark.large),
        param('toponymy_m_p', marks=mark.large),
        param('toponymy_z_p', marks=mark.large),
        param('toponymy_zm_p', marks=mark.large),
        'toponymy_mp',
        param('toponymy_m_mp', marks=mark.large),
        param('toponymy_z_mp', marks=mark.large),
        'toponymy_zm_mp',
        param('transmission_p', marks=mark.large),
        'transmission_m_p',
        'transmission_z_p',
        param('transmission_zm_p', marks=mark.large),
        'transmission_l',
        param('transmission_m_l', marks=mark.large),
        param('transmission_z_l', marks=mark.large),
        'transmission_zm_l',
        'transmission_ml',
        param('transmission_m_ml', marks=mark.large),
        param('transmission_z_ml', marks=mark.large),
        'transmission_zm_ml',
        'transmission_mp',
        param('transmission_m_mp', marks=mark.large),
        param('transmission_z_mp', marks=mark.large),
        'transmission_zm_mp',
    ])
    @mark.parametrize('op_name', [
        'grid_a',
        param('grid_m_a', marks=mark.large),
        param('grid_z_a', marks=mark.large),
        param('grid_zm_a', marks=mark.large),
    ])
    @mark.parametrize('output_z', [
        param(OutputZOption.SAME, marks=mark.large),
        OutputZOption.ENABLED,
        param(OutputZOption.DISABLED, marks=mark.large),
    ])
    @mark.parametrize('output_m', [
        param(OutputMOption.SAME, marks=mark.large),
        OutputMOption.ENABLED,
        param(OutputMOption.DISABLED, marks=mark.large),
    ])
    def test_output_zm_cleaner(self, grid_index, ntdb_zm_small, mem_gpkg, fc_name, op_name, output_z, output_m):
        """
        Test split using Output ZM settings using cleaner inputs
        """
        operator = grid_index[op_name]
        operator = operator.copy(
            name=op_name,
            where_clause="""DATANAME IN ('082O01-6', '082O01-7', '082O01-8')""",
            geopackage=mem_gpkg)
        source = ntdb_zm_small[fc_name]
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            results = split(source=source, operator=operator, field='DATANAME', geopackage=mem_gpkg)
        assert len(results) == 3
        result, *_ = results
        assert result.has_z == zm.z_enabled
        assert result.has_m == zm.m_enabled
    # End test_output_zm_cleaner method

    @mark.benchmark
    @mark.parametrize('name, count', [
        ('utmzone_continentish_a', 708),
        ('utmzone_sparse_a', 228),
    ])
    def test_split_larger_inputs(self, inputs, world_features, mem_gpkg, name, count):
        """
        Test split using larger inputs
        """
        operator = inputs[name]
        source = world_features['admin_a']
        results = split(source=source, operator=operator, field='NAME', geopackage=mem_gpkg)
        assert len(results) == count
    # End test_split_larger_inputs method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('hydro_4617_a', ESRI, 102179, True, (34997.609375, 5661405.0, 43766.390625, 5675267.)),
        param('hydro_4617_zm_a', ESRI, 102179, True, (34997.609375, 5661405.0, 43766.390625, 5675267.), marks=mark.slow),
        param('transmission_4617_m_l', ESRI, 102179, True, (34970.7265625, 5661361.0, 43784.84375, 5675250.5), marks=mark.slow),
        param('transmission_4617_z_l', ESRI, 102179, True, (34970.7265625, 5661361.0, 43784.84375, 5675250.5), marks=mark.slow),
        param('toponymy_4617_m_p', ESRI, 102179, True, (37632.4375, 5665134.0, 43108.640625, 5675312.5), marks=mark.slow),
        param('toponymy_4617_z_p', ESRI, 102179, True, (37632.4375, 5665134.0, 43108.640625, 5675312.5), marks=mark.slow),
    ])
    @mark.parametrize('op_name', [
        'grid_10tm_a',
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
    def test_output_crs(self, ntdb_zm_small, grid_index, mem_gpkg,
                        fc_name, auth_name, srs_id, flag, extent, op_name, output_z, output_m):
        """
        Test with output CRS and different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        operator = grid_index[op_name]
        crs = CRS.from_authority(auth_name=auth_name, code=srs_id)
        with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs),
              Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m),
              UseGrids(flag)):
            zm = zm_config(source)
            result = split(source=source, operator=operator, field='DATANAME', geopackage=mem_gpkg)
            first, *_ = result
            assert first.spatial_reference_system.srs_id == srs_id
            assert first.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(first.extent, abs=0.001) == extent
            assert first.has_z == zm.z_enabled
            assert first.has_m == zm.m_enabled
    # End test_output_crs method

    @mark.transform
    @mark.parametrize('fc_name, extent', [
        ('hydro_4617_a', (-114.25001525878906, 51.0, -114.125, 51.11003494262695)),
        ('hydro_6654_a', (692529.4375, 5653599.5, 701493.5, 5665959.5)),
        ('hydro_lcc_a', (-1260769.625, 1417430.0, -1250397.75, 1429655.5)),
        ('hydro_utm11_a', (692529.4375, 5653599.5, 701493.5, 5665959.5)),
    ])
    @mark.parametrize('op_name', [
        'grid_10tm_a',
    ])
    def test_different_crs(self, ntdb_zm_small, grid_index, mem_gpkg,
                           fc_name, extent, op_name):
        """
        Test split with different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        operator = grid_index[op_name].copy(
            f'{op_name}_subset', geopackage=mem_gpkg,
            where_clause="""DATANAME = '082O01-6'""")
        if '4671' in fc_name:
            tol = 0.000001
        else:
            tol = 0.001
        with UseGrids(True):
            result, = split(source=source, operator=operator, field='DATANAME', geopackage=mem_gpkg)
            srs_id = source.spatial_reference_system.srs_id
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=tol) == extent
    # End test_different_crs method
# End TestSplit class


if __name__ == '__main__':  # pragma: no cover
    pass
