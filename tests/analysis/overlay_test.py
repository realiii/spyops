# -*- coding: utf-8 -*-
"""
Tests for Overlay
"""


from fudgeo import FeatureClass
from fudgeo.enumeration import GeometryType
from pytest import mark, param, raises

from gisworks.analysis.overlay import erase, intersect
from gisworks.environment.core import zm_config
from gisworks.shared.enumeration import (
    AlgorithmOption, AttributeOption, OutputTypeOption)
from gisworks.environment.enumeration import (
    OutputMOption, OutputZOption, Setting)
from gisworks.query.overlay import QueryErase
from gisworks.shared.exception import OperationsError
from gisworks.environment.context import Swap


pytestmark = [mark.overlay, mark.query]


class TestErase:
    """
    Test Erase
    """
    @mark.parametrize('fc_name, xy_tolerance, count', [
        ('admin_a', None, 245),
        ('airports_p', None, 29),
        ('roads_l', None, 3054),
        ('admin_mp_a', None, 217),
        ('airports_mp_p', None, 10),
        ('roads_mp_l', None, 14),
        ('admin_a', 0.001, 286),
        ('airports_p', 0.001, 29),
        ('roads_l', 0.001, 3054),
        ('admin_mp_a', 0.001, 217),
        ('airports_mp_p', 0.001, 10),
        param('roads_mp_l', 0.001, 14, marks=mark.slow),
        ('admin_a', 1, 41),
        ('airports_p', 1, 33),
        ('roads_l', 1, 337),
        ('admin_mp_a', 1, 37),
        ('airports_mp_p', 1, 10),
        ('roads_mp_l', 1, 14),
    ])
    def test_erase_reduced(self, inputs, world_features, fresh_gpkg, fc_name,
                           xy_tolerance, count):
        """
        Test erase -- reduced data for faster testing
        """
        eraser = inputs['eraser_a']
        assert len(eraser) == 5
        source = world_features[fc_name]
        assert source.is_multi_part == ('mp' in fc_name)
        target = FeatureClass(geopackage=fresh_gpkg, name=f'temp_{fc_name}')
        query = QueryErase(source=source, target=target, operator=eraser)
        _, touches = query.select.split('WHERE', 1)
        subset = source.copy(f'subset_{fc_name}', where_clause=touches,
                             geopackage=fresh_gpkg)
        assert len(subset) <= len(source)
        target = FeatureClass(geopackage=fresh_gpkg, name=fc_name)
        result = erase(source=subset, operator=eraser, target=target,
                       xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_erase_reduced method

    @mark.zm
    @mark.parametrize('fc_name, xy_tolerance, output_z_option, output_m_option, count', [
        ('admin_a', None, OutputZOption.SAME, OutputMOption.SAME, 245),
        ('airports_p', None, OutputZOption.SAME, OutputMOption.SAME, 29),
        ('roads_l', None, OutputZOption.SAME, OutputMOption.SAME, 3054),
        ('admin_mp_a', None, OutputZOption.SAME, OutputMOption.SAME, 217),
        ('airports_mp_p', None, OutputZOption.SAME, OutputMOption.SAME, 10),
        ('roads_mp_l', None, OutputZOption.SAME, OutputMOption.SAME, 14),
        ('admin_a', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 245),
        ('airports_p', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 29),
        ('roads_l', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 3054),
        ('admin_mp_a', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 217),
        ('airports_mp_p', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 10),
        ('roads_mp_l', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 14),
        ('admin_a', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 245),
        ('airports_p', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 29),
        ('roads_l', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 3054),
        ('admin_mp_a', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 217),
        ('airports_mp_p', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 10),
        ('roads_mp_l', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 14),
    ])
    def test_erase_reduced_zm(self, inputs, world_features, fresh_gpkg, fc_name,
                              xy_tolerance, output_z_option, output_m_option, count):
        """
        Test erase -- reduced data for faster testing -- with ZM
        """
        eraser = inputs['eraser_a']
        assert len(eraser) == 5
        source = world_features[fc_name]
        assert source.is_multi_part == ('mp' in fc_name)
        target = FeatureClass(geopackage=fresh_gpkg, name=f'temp_{fc_name}')
        query = QueryErase(source=source, target=target, operator=eraser)
        _, touches = query.select.split('WHERE', 1)
        subset = source.copy(f'subset_{fc_name}', where_clause=touches,
                             geopackage=fresh_gpkg)
        assert len(subset) <= len(source)
        target = FeatureClass(geopackage=fresh_gpkg, name=fc_name)
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z_option),
              Swap(Setting.OUTPUT_M_OPTION, output_m_option),
              Swap(Setting.Z_VALUE, 123.456)):
            zm = zm_config(source, eraser)
            result = erase(source=subset, operator=eraser, target=target,
                           xy_tolerance=xy_tolerance)
        assert len(result) == count
        assert result.has_z == zm.z_enabled
        assert result.has_m == zm.m_enabled
    # End test_erase_reduced_zm method

    def test_erase_reduced_sans_attributes(self, inputs, world_features, fresh_gpkg):
        """
        Test erase -- reduced data for faster testing -- sans attributes
        """
        eraser = inputs['intersect_sans_attr_a']
        assert len(eraser) == 5
        source = world_features['admin_sans_attr_a']
        target = FeatureClass(geopackage=fresh_gpkg, name=f'temp_sans_attr_a')
        query = QueryErase(source=source, target=target, operator=eraser)
        _, touches = query.select.split('WHERE', 1)
        subset = source.copy(f'subset_sans_attr_a', where_clause=touches,
                             geopackage=fresh_gpkg)
        assert len(subset) <= len(source)
        target = FeatureClass(geopackage=fresh_gpkg, name='sans_attr_a')
        result = erase(source=subset, operator=eraser, target=target)
        assert len(result) == 245
    # End test_erase_reduced_sans_attributes method

    @mark.parametrize('fc_name, xy_tolerance, count', [
        ('airports_p', None, 3464),
        ('airports_mp_p', None, 191),
        ('airports_p', 0.001, 3464),
        ('airports_mp_p', 0.001, 191),
    ])
    def test_erase(self, inputs, world_features, fresh_gpkg, fc_name, xy_tolerance, count):
        """
        Test erase - ensure that disjoint is exercised
        """
        eraser = inputs['eraser_a']
        assert len(eraser) == 5
        source = world_features[fc_name]
        assert source.is_multi_part == ('mp' in fc_name)
        target = FeatureClass(geopackage=fresh_gpkg, name=fc_name)
        result = erase(source=source, operator=eraser, target=target,
                       xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_erase method

    @mark.parametrize('xy_tolerance, count', [
        (None, 191),
        (0.001, 204),
    ])
    def test_erase_line_on_line(self, world_features, inputs, mem_gpkg, xy_tolerance, count):
        """
        Test erase using a line feature class as the operator on a line feature class
        """
        operator = inputs['rivers_portion_l']
        source = world_features['rivers_l']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = erase(source=source, operator=operator, target=target,
                       xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_erase_line_on_line method

    @mark.parametrize('xy_tolerance, count', [
        (None, 13_958),
        (0, 13_958),
        (0.0000000001, 21_353),
        (0.1, 21_356),
    ])
    def test_erase_line_on_point(self, inputs, mem_gpkg, xy_tolerance, count):
        """
        Test erase using a line feature class as the operator on a point feature class
        """
        operator = inputs['rivers_portion_l']
        source = inputs['river_p']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = erase(source=source, operator=operator, target=target,
                       xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_erase_line_on_point method

    @mark.parametrize('xy_tolerance, count', [
        (None, 21_256),
        (0, 21_256),
        (0.001, 21_256),
    ])
    def test_erase_point_on_point(self, inputs, mem_gpkg, xy_tolerance, count):
        """
        Test erase using a point feature class as the operator on a point feature class
        """
        operator = inputs['river_p']
        operator = operator.copy(
            name='river_p_operator', where_clause='fid <= 100',
            geopackage=mem_gpkg)
        assert len(operator) == 100
        source = inputs['river_p']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = erase(source=source, operator=operator, target=target,
                       xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_erase_point_on_point method

    @mark.zm
    @mark.parametrize('fc_name, op_name, output_z, output_m', [
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
    ])
    def test_output_zm(self, ntdb_clipped, mem_gpkg, fc_name, op_name, output_z, output_m):
        """
        Test erase using Output ZM settings
        """
        operator = ntdb_clipped[op_name]
        operator = operator.copy(name=op_name, where_clause="""DATANAME = '082O01'""", geopackage=mem_gpkg)
        source = ntdb_clipped[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_erased')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            erased = erase(source=source, operator=operator, target=target)
        if output_z == OutputZOption.SAME:
            has_z = source.has_z or operator.has_z
        else:
            has_z = output_z == OutputZOption.ENABLED
        if output_m == OutputZOption.SAME:
            has_m = source.has_m or operator.has_m
        else:
            has_m = output_m == OutputMOption.ENABLED
        assert erased.has_z == has_z
        assert erased.has_m == has_m
        assert len(erased) <= len(source)
    # End test_output_zm method

    @mark.benchmark
    @mark.parametrize('name, count', [
        ('utmzone_continentish_a', 11_046),
        ('utmzone_sparse_a', 186_254),
    ])
    def test_erase_larger_inputs(self, inputs, world_features, mem_gpkg, name, count):
        """
        Test erase using larger inputs
        """
        operator = inputs[name]
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name=name)
        result = erase(source=source, operator=operator, target=target)
        assert len(result) == count
    # End test_erase_larger_inputs function
# End TestErase class


class TestIntersect:
    """
    Test Intersect
    """
    @mark.parametrize('fc_name, xy_tolerance, option, feature_count, field_count', [
        ('admin_a', None, AttributeOption.ALL, 114, 25),
        ('airports_p', None, AttributeOption.ALL, 40, 14),
        ('roads_l', None, AttributeOption.ALL, 2514, 22),
        ('admin_mp_a', None, AttributeOption.ALL, 68, 23),
        ('airports_mp_p', None, AttributeOption.ALL, 8, 11),
        ('roads_mp_l', None, AttributeOption.ALL, 14, 11),
        ('admin_a', 0.001, AttributeOption.ALL, 112, 25),
        ('airports_p', 0.001, AttributeOption.ALL, 40, 14),
        ('roads_l', 0.001, AttributeOption.ALL, 2683, 22),
        ('admin_mp_a', 0.001, AttributeOption.ALL, 68, 23),
        ('airports_mp_p', 0.001, AttributeOption.ALL, 8, 11),
        ('roads_mp_l', 0.001, AttributeOption.ALL, 14, 11),
        ('admin_a', 1, AttributeOption.ALL, 22, 25),
        ('airports_p', 1, AttributeOption.ALL, 35, 14),
        ('roads_l', 1, AttributeOption.ALL, 347, 22),
        ('admin_mp_a', 1, AttributeOption.ALL, 22, 23),
        ('airports_mp_p', 1, AttributeOption.ALL, 8, 11),
        ('roads_mp_l', 1, AttributeOption.ALL, 13, 11),
        ('admin_a', None, AttributeOption.ONLY_FID, 114, 4),
        ('airports_p', None, AttributeOption.ONLY_FID, 40, 4),
        ('roads_l', None, AttributeOption.ONLY_FID, 2514, 4),
        ('admin_mp_a', None, AttributeOption.ONLY_FID, 68, 4),
        ('airports_mp_p', None, AttributeOption.ONLY_FID, 8, 4),
        ('roads_mp_l', None, AttributeOption.ONLY_FID, 14, 4),
        ('admin_a', 0.001, AttributeOption.ONLY_FID, 112, 4),
        ('airports_p', 0.001, AttributeOption.ONLY_FID, 40, 4),
        ('roads_l', 0.001, AttributeOption.ONLY_FID, 2683, 4),
        ('admin_mp_a', 0.001, AttributeOption.ONLY_FID, 68, 4),
        ('airports_mp_p', 0.001, AttributeOption.ONLY_FID, 8, 4),
        ('roads_mp_l', 0.001, AttributeOption.ONLY_FID, 14, 4),
        ('admin_a', 1, AttributeOption.ONLY_FID, 22, 4),
        ('airports_p', 1, AttributeOption.ONLY_FID, 35, 4),
        ('roads_l', 1, AttributeOption.ONLY_FID, 347, 4),
        ('admin_mp_a', 1, AttributeOption.ONLY_FID, 22, 4),
        ('airports_mp_p', 1, AttributeOption.ONLY_FID, 8, 4),
        ('roads_mp_l', 1, AttributeOption.ONLY_FID, 13, 4),
        ('admin_a', None, AttributeOption.SANS_FID, 114, 23),
        ('airports_p', None, AttributeOption.SANS_FID, 40, 12),
        ('roads_l', None, AttributeOption.SANS_FID, 2514, 20),
        ('admin_mp_a', None, AttributeOption.SANS_FID, 68, 21),
        ('airports_mp_p', None, AttributeOption.SANS_FID, 8, 9),
        ('roads_mp_l', None, AttributeOption.SANS_FID, 14, 9),
        ('admin_a', 0.001, AttributeOption.SANS_FID, 112, 23),
        ('airports_p', 0.001, AttributeOption.SANS_FID, 40, 12),
        ('roads_l', 0.001, AttributeOption.SANS_FID, 2683, 20),
        ('admin_mp_a', 0.001, AttributeOption.SANS_FID, 68, 21),
        ('airports_mp_p', 0.001, AttributeOption.SANS_FID, 8, 9),
        ('roads_mp_l', 0.001, AttributeOption.SANS_FID, 14, 9),
        ('admin_a', 1, AttributeOption.SANS_FID, 22, 23),
        ('airports_p', 1, AttributeOption.SANS_FID, 35, 12),
        ('roads_l', 1, AttributeOption.SANS_FID, 347, 20),
        ('admin_mp_a', 1, AttributeOption.SANS_FID, 22, 21),
        ('airports_mp_p', 1, AttributeOption.SANS_FID, 8, 9),
        ('roads_mp_l', 1, AttributeOption.SANS_FID, 13, 9),
    ])
    def test_intersect_setting(self, inputs, world_features, mem_gpkg, fc_name, xy_tolerance,
                               option, feature_count, field_count):
        """
        Test intersect using analysis settings for XY tolerance
        and varying attribute option
        """
        operator = inputs['intersect_a']
        assert len(operator) == 5
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with Swap(Setting.XY_TOLERANCE, xy_tolerance):
            result = intersect(source=source, operator=operator, target=target,
                               attribute_option=option)
        assert len(result) < len(source)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_intersect_setting method

    @mark.parametrize('fc_name, algorithm_option, output_option, feature_count, throws', [
        ('admin_a', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, 0, False),
        ('airports_p', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, None, True),
        ('roads_l', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, 1659, False),
        ('admin_mp_a', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, 0, False),
        ('airports_mp_p', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, None, True),
        ('roads_mp_l', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, 14, False),
        ('admin_a', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, 318, False),
        ('airports_p', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, 26, False),
        ('roads_l', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, 436, False),
        ('admin_mp_a', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, 55, False),
        ('airports_mp_p', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, 8, False),
        ('roads_mp_l', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, 12, False),
        ('admin_a', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, 0, False),
        ('airports_p', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, None, True),
        ('roads_l', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, 1709, False),
        ('admin_mp_a', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, 0, False),
        ('airports_mp_p', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, None, True),
        ('roads_mp_l', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, 24, False),
        ('admin_a', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, 358, False),
        ('airports_p', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, 26, False),
        ('roads_l', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, 536, False),
        ('admin_mp_a', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, 358, False),
        ('airports_mp_p', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, 13, False),
        ('roads_mp_l', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, 22, False),
    ])
    def test_intersect_output_type(self, inputs, world_features, mem_gpkg, fc_name,
                                   algorithm_option, output_option, feature_count, throws):
        """
        Test intersect varying output types for each algorithm option
        """
        operator = inputs['intersect_holes_a']
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        if throws:
            with raises(OperationsError):
                intersect(source=source, operator=operator,
                          algorithm_option=algorithm_option,
                          target=target, output_type_option=output_option)
        else:
            result = intersect(source=source, operator=operator, target=target,
                               algorithm_option=algorithm_option,
                               output_type_option=output_option)
            if output_option == OutputTypeOption.LINE:
                assert GeometryType.linestring in result.shape_type
            else:
                assert GeometryType.point in result.shape_type
            assert len(result) < len(source)
            assert len(result) == feature_count
    # End test_intersect_output_type method

    @mark.zm
    @mark.parametrize('fc_name, algorithm_option, output_option, output_z_option, output_m_option, feature_count', [
        ('admin_a', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, OutputZOption.SAME, OutputMOption.SAME, 0),
        ('roads_l', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, OutputZOption.SAME, OutputMOption.SAME, 1659),
        ('admin_mp_a', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, OutputZOption.SAME, OutputMOption.SAME, 0),
        ('roads_mp_l', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, OutputZOption.SAME, OutputMOption.SAME, 14),
        ('admin_a', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.SAME, OutputMOption.SAME, 318),
        ('airports_p', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.SAME, OutputMOption.SAME, 26),
        ('roads_l', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.SAME, OutputMOption.SAME, 436),
        ('admin_mp_a', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.SAME, OutputMOption.SAME, 55),
        ('airports_mp_p', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.SAME, OutputMOption.SAME, 8),
        ('roads_mp_l', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.SAME, OutputMOption.SAME, 12),
        ('admin_a', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, OutputZOption.SAME, OutputMOption.SAME, 0),
        ('roads_l', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, OutputZOption.SAME, OutputMOption.SAME, 1709),
        ('admin_mp_a', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, OutputZOption.SAME, OutputMOption.SAME, 0),
        ('roads_mp_l', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, OutputZOption.SAME, OutputMOption.SAME, 24),
        ('admin_a', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.SAME, OutputMOption.SAME, 358),
        ('airports_p', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.SAME, OutputMOption.SAME, 26),
        ('roads_l', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.SAME, OutputMOption.SAME, 536),
        ('admin_mp_a', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.SAME, OutputMOption.SAME, 358),
        ('airports_mp_p', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.SAME, OutputMOption.SAME, 13),
        ('roads_mp_l', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.SAME, OutputMOption.SAME, 22),
        ('admin_a', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, OutputZOption.ENABLED, OutputMOption.ENABLED, 0),
        ('roads_l', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, OutputZOption.ENABLED, OutputMOption.ENABLED, 1659),
        ('admin_mp_a', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, OutputZOption.ENABLED, OutputMOption.ENABLED, 0),
        ('roads_mp_l', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, OutputZOption.ENABLED, OutputMOption.ENABLED, 14),
        ('admin_a', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.ENABLED, OutputMOption.ENABLED, 318),
        ('airports_p', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.ENABLED, OutputMOption.ENABLED, 26),
        ('roads_l', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.ENABLED, OutputMOption.ENABLED, 436),
        ('admin_mp_a', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.ENABLED, OutputMOption.ENABLED, 55),
        ('airports_mp_p', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.ENABLED, OutputMOption.ENABLED, 8),
        ('roads_mp_l', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.ENABLED, OutputMOption.ENABLED, 12),
        ('admin_a', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, OutputZOption.ENABLED, OutputMOption.ENABLED, 0),
        ('roads_l', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, OutputZOption.ENABLED, OutputMOption.ENABLED, 1709),
        ('admin_mp_a', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, OutputZOption.ENABLED, OutputMOption.ENABLED, 0),
        ('roads_mp_l', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, OutputZOption.ENABLED, OutputMOption.ENABLED, 24),
        ('admin_a', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.ENABLED, OutputMOption.ENABLED, 358),
        ('airports_p', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.ENABLED, OutputMOption.ENABLED, 26),
        ('roads_l', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.ENABLED, OutputMOption.ENABLED, 536),
        ('admin_mp_a', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.ENABLED, OutputMOption.ENABLED, 358),
        ('airports_mp_p', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.ENABLED, OutputMOption.ENABLED, 13),
        ('roads_mp_l', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.ENABLED, OutputMOption.ENABLED, 22),
        ('admin_a', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, OutputZOption.DISABLED, OutputMOption.DISABLED, 0),
        ('roads_l', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, OutputZOption.DISABLED, OutputMOption.DISABLED, 1659),
        ('admin_mp_a', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, OutputZOption.DISABLED, OutputMOption.DISABLED, 0),
        ('roads_mp_l', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, OutputZOption.DISABLED, OutputMOption.DISABLED, 14),
        ('admin_a', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.DISABLED, OutputMOption.DISABLED, 318),
        ('airports_p', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.DISABLED, OutputMOption.DISABLED, 26),
        ('roads_l', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.DISABLED, OutputMOption.DISABLED, 436),
        ('admin_mp_a', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.DISABLED, OutputMOption.DISABLED, 55),
        ('airports_mp_p', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.DISABLED, OutputMOption.DISABLED, 8),
        ('roads_mp_l', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, OutputZOption.DISABLED, OutputMOption.DISABLED, 12),
        ('admin_a', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, OutputZOption.DISABLED, OutputMOption.DISABLED, 0),
        ('roads_l', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, OutputZOption.DISABLED, OutputMOption.DISABLED, 1709),
        ('admin_mp_a', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, OutputZOption.DISABLED, OutputMOption.DISABLED, 0),
        ('roads_mp_l', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, OutputZOption.DISABLED, OutputMOption.DISABLED, 24),
        ('admin_a', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.DISABLED, OutputMOption.DISABLED, 358),
        ('airports_p', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.DISABLED, OutputMOption.DISABLED, 26),
        ('roads_l', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.DISABLED, OutputMOption.DISABLED, 536),
        ('admin_mp_a', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.DISABLED, OutputMOption.DISABLED, 358),
        ('airports_mp_p', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.DISABLED, OutputMOption.DISABLED, 13),
        ('roads_mp_l', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, OutputZOption.DISABLED, OutputMOption.DISABLED, 22),
    ])
    def test_intersect_output_type_zm(self, inputs, world_features, mem_gpkg, fc_name,
                                      algorithm_option, output_option, output_z_option,
                                      output_m_option, feature_count):
        """
        Test intersect varying output types for each algorithm option and zm
        """
        operator = inputs['intersect_holes_a']
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z_option),
              Swap(Setting.OUTPUT_M_OPTION, output_m_option),
              Swap(Setting.Z_VALUE, 123.456)):
            zm = zm_config(source, operator)
            result = intersect(source=source, operator=operator, target=target,
                               algorithm_option=algorithm_option,
                               output_type_option=output_option)
        if output_option == OutputTypeOption.LINE:
            assert GeometryType.linestring in result.shape_type
        else:
            assert GeometryType.point in result.shape_type
        assert len(result) < len(source)
        assert len(result) == feature_count
        assert result.has_z == zm.z_enabled
        assert result.has_m == zm.m_enabled
    # End test_intersect_output_type_zm method

    @mark.zm
    @mark.parametrize('fc_name, op_name, output_z, output_m', [
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_z_nan_m_nan_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.SAME, OutputMOption.SAME),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.ENABLED, OutputMOption.ENABLED),
        ('CLIP_NTDB_HYDRO_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_M_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_M_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_Z_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_VCS_ZM_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_Z_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_Z_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_A', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_STRUCTURES_ZM_MA', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPOGRAPHY_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_VCS_Z_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_Z_MP', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TOPONYMY_Z_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_M_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_ML', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_P', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_Z_ML', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_VCS_ZM_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_Z_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
        ('CLIP_NTDB_TRANSMISSION_ZM_L', 'ntdb_50k_index_yyc16_zm_a', OutputZOption.DISABLED, OutputMOption.DISABLED),
    ])
    def test_output_zm_pairwise(self, ntdb_clipped, mem_gpkg, fc_name, op_name, output_z, output_m):
        """
        Test intersect using Output ZM settings using pairwise algorithm
        """
        operator = ntdb_clipped[op_name]
        source = ntdb_clipped[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_intersected')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            intersected = intersect(source=source, operator=operator,
                                    target=target, algorithm_option=AlgorithmOption.PAIRWISE)
        if output_z == OutputZOption.SAME:
            has_z = source.has_z or operator.has_z
        else:
            has_z = output_z == OutputZOption.ENABLED
        if output_m == OutputZOption.SAME:
            has_m = source.has_m or operator.has_m
        else:
            has_m = output_m == OutputMOption.ENABLED
        assert intersected.has_z == has_z
        assert intersected.has_m == has_m
    # End test_output_zm_pairwise method

    @mark.parametrize('fc_name, xy_tolerance, option, feature_count, field_count', [
        ('admin_a', None, AttributeOption.ALL, 128, 25),
        ('airports_p', None, AttributeOption.ALL, 40, 14),
        ('roads_l', None, AttributeOption.ALL, 2560, 22),
        ('admin_mp_a', None, AttributeOption.ALL, 128, 23),
        ('airports_mp_p', None, AttributeOption.ALL, 12, 11),
        ('roads_mp_l', None, AttributeOption.ALL, 21, 11),
        ('admin_a', 0.001, AttributeOption.ALL, 125, 25),
        ('airports_p', 0.001, AttributeOption.ALL, 40, 14),
        ('roads_l', 0.001, AttributeOption.ALL, 2725, 22),
        ('admin_mp_a', 0.001, AttributeOption.ALL, 125, 23),
        ('airports_mp_p', 0.001, AttributeOption.ALL, 12, 11),
        ('roads_mp_l', 0.001, AttributeOption.ALL, 21, 11),
        ('admin_a', None, AttributeOption.ONLY_FID, 128, 4),
        ('airports_p', None, AttributeOption.ONLY_FID, 40, 4),
        ('roads_l', None, AttributeOption.ONLY_FID, 2560, 4),
        ('admin_mp_a', None, AttributeOption.ONLY_FID, 128, 4),
        ('airports_mp_p', None, AttributeOption.ONLY_FID, 12, 4),
        ('roads_mp_l', None, AttributeOption.ONLY_FID, 21, 4),
        ('admin_a', 0.001, AttributeOption.ONLY_FID, 125, 4),
        ('airports_p', 0.001, AttributeOption.ONLY_FID, 40, 4),
        ('roads_l', 0.001, AttributeOption.ONLY_FID, 2725, 4),
        ('admin_mp_a', 0.001, AttributeOption.ONLY_FID, 125, 4),
        ('airports_mp_p', 0.001, AttributeOption.ONLY_FID, 12, 4),
        ('roads_mp_l', 0.001, AttributeOption.ONLY_FID, 21, 4),
        ('admin_a', None, AttributeOption.SANS_FID, 128, 23),
        ('airports_p', None, AttributeOption.SANS_FID, 40, 12),
        ('roads_l', None, AttributeOption.SANS_FID, 2560, 20),
        ('admin_mp_a', None, AttributeOption.SANS_FID, 128, 21),
        ('airports_mp_p', None, AttributeOption.SANS_FID, 12, 9),
        ('roads_mp_l', None, AttributeOption.SANS_FID, 21, 9),
        ('admin_a', 0.001, AttributeOption.SANS_FID, 125, 23),
        ('airports_p', 0.001, AttributeOption.SANS_FID, 40, 12),
        ('roads_l', 0.001, AttributeOption.SANS_FID, 2725, 20),
        ('admin_mp_a', 0.001, AttributeOption.SANS_FID, 125, 21),
        ('airports_mp_p', 0.001, AttributeOption.SANS_FID, 12, 9),
        ('roads_mp_l', 0.001, AttributeOption.SANS_FID, 21, 9),
    ])
    def test_intersect_classic_setting(self, inputs, world_features, mem_gpkg, fc_name, xy_tolerance,
                                       option, feature_count, field_count):
        """
        Test intersect using analysis settings -- classic algorithm
        """
        operator = inputs['intersect_a']
        assert len(operator) == 5
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with Swap(Setting.XY_TOLERANCE, xy_tolerance):
            result = intersect(source=source, operator=operator, target=target,
                               attribute_option=option, algorithm_option=AlgorithmOption.CLASSIC)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_intersect_classic_setting method

    @mark.parametrize('algorithm_option, attribute_option, feature_count, field_count', [
        (AlgorithmOption.PAIRWISE, AttributeOption.ALL, 64, 11),
        (AlgorithmOption.PAIRWISE, AttributeOption.SANS_FID, 64, 9),
        (AlgorithmOption.PAIRWISE, AttributeOption.ONLY_FID, 64, 4),
        (AlgorithmOption.CLASSIC, AttributeOption.ALL, 380, 11),
        (AlgorithmOption.CLASSIC, AttributeOption.SANS_FID, 380, 9),
        (AlgorithmOption.CLASSIC, AttributeOption.ONLY_FID, 380, 4),
    ])
    def test_intersect_option(self, inputs, mem_gpkg, algorithm_option, attribute_option, feature_count, field_count):
        """
        Test Intersect with Options for Classic and Pairwise
        """
        operator = inputs['intersect_a']
        source = inputs['int_flavor_a']
        target = FeatureClass(
            geopackage=mem_gpkg,
            name=f'{str(algorithm_option)}_{attribute_option}_a')
        result = intersect(source=source, operator=operator, target=target,
                           algorithm_option=algorithm_option, attribute_option=attribute_option)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_intersect_option method

    @mark.parametrize('algorithm_option, attribute_option, feature_count, field_count', [
        (AlgorithmOption.PAIRWISE, AttributeOption.ALL, 114, 4),
        (AlgorithmOption.PAIRWISE, AttributeOption.SANS_FID, 114, 2),
        (AlgorithmOption.PAIRWISE, AttributeOption.ONLY_FID, 114, 4),
        (AlgorithmOption.CLASSIC, AttributeOption.ALL, 128, 4),
        (AlgorithmOption.CLASSIC, AttributeOption.SANS_FID, 128, 2),
        (AlgorithmOption.CLASSIC, AttributeOption.ONLY_FID, 128, 4),
    ])
    def test_intersect_option_sans_attributes(self, inputs, world_features, mem_gpkg, algorithm_option, attribute_option, feature_count, field_count):
        """
        Test Intersect with Options for Classic and Pairwise -- sans attributes
        """
        operator = inputs['intersect_sans_attr_a']
        source = world_features['admin_sans_attr_a']
        target = FeatureClass(
            geopackage=mem_gpkg,
            name=f'{str(algorithm_option)}_{attribute_option}_a')
        result = intersect(source=source, operator=operator, target=target,
                           algorithm_option=algorithm_option, attribute_option=attribute_option)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_intersect_option method

    @mark.parametrize('xy_tolerance, feature_count', [
        (None, 380),
        (0.001, 379),
        (0.05, 352),
    ])
    def test_intersect_classic_xy_tolerance(self, inputs, mem_gpkg, xy_tolerance, feature_count):
        """
        Test Intersect classic with XY Tolerance
        """
        operator = inputs['intersect_a']
        source = inputs['int_flavor_a']
        target = FeatureClass(geopackage=mem_gpkg, name='xy_a')
        result = intersect(source=source, operator=operator, target=target,
                           algorithm_option=AlgorithmOption.CLASSIC, xy_tolerance=xy_tolerance)
        assert len(result) == feature_count
    # End test_intersect_classic_xy_tolerance method

    @mark.parametrize('option, xy_tolerance, count', [
        (AlgorithmOption.CLASSIC, None, 195),
        (AlgorithmOption.CLASSIC, 0.001, 209),
        (AlgorithmOption.PAIRWISE, None, 195),
        (AlgorithmOption.PAIRWISE, 0.001, 209),
    ])
    def test_intersect_line_on_line(self, world_features, inputs, mem_gpkg, option, xy_tolerance, count):
        """
        Test intersect using a line feature class as the operator on a line feature class
        """
        operator = inputs['rivers_portion_l']
        source = world_features['rivers_l']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = intersect(source=source, operator=operator, target=target,
                           algorithm_option=option, xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_intersect_line_on_line method

    @mark.parametrize('option, xy_tolerance, count', [
        (AlgorithmOption.CLASSIC, None, 7524),
        (AlgorithmOption.CLASSIC, 0, 7524),
        (AlgorithmOption.CLASSIC, 0.0000000001, 3),
        (AlgorithmOption.CLASSIC, 0.1, 0),
        (AlgorithmOption.PAIRWISE, None, 7524),
        (AlgorithmOption.PAIRWISE, 0, 7524),
        (AlgorithmOption.PAIRWISE, 0.0000000001, 3),
        (AlgorithmOption.PAIRWISE, 0.1, 0),
    ])
    def test_intersect_line_on_point(self, inputs, mem_gpkg, option, xy_tolerance, count):
        """
        Test intersect using a line feature class as the operator on a point feature class
        """
        operator = inputs['rivers_portion_l']
        source = inputs['river_p']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = intersect(source=source, operator=operator, target=target,
                           algorithm_option=option, xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_intersect_line_on_point method

    @mark.parametrize('option, xy_tolerance, count', [
        (AlgorithmOption.CLASSIC, None, 100),
        (AlgorithmOption.CLASSIC, 0, 100),
        (AlgorithmOption.CLASSIC, 0.001, 100),
        (AlgorithmOption.PAIRWISE, None, 100),
        (AlgorithmOption.PAIRWISE, 0, 100),
        (AlgorithmOption.PAIRWISE, 0.001, 100),
    ])
    def test_intersect_point_on_point(self, inputs, mem_gpkg, option, xy_tolerance, count):
        """
        Test intersect using a point feature class as the operator on a point feature class
        """
        operator = inputs['river_p']
        operator = operator.copy(
            name='river_p_operator', where_clause='fid <= 100', geopackage=mem_gpkg)
        assert len(operator) == 100
        source = inputs['river_p']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = intersect(source=source, operator=operator, target=target,
                           algorithm_option=option, xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_intersect_point_on_point method

    @mark.benchmark
    @mark.parametrize('option, name, count', [
        (AlgorithmOption.CLASSIC, 'utmzone_continentish_a', 206_708),
        (AlgorithmOption.CLASSIC, 'utmzone_sparse_a', 26_951),
        (AlgorithmOption.PAIRWISE, 'utmzone_continentish_a', 205_532),
        (AlgorithmOption.PAIRWISE, 'utmzone_sparse_a', 26_949),
    ])
    def test_intersect_larger_inputs(self, inputs, world_features, mem_gpkg, option, name, count):
        """
        Test intersect using larger inputs
        """
        operator = inputs[name]
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name=name)
        result = intersect(source=source, operator=operator, target=target, algorithm_option=option)
        assert len(result) == count
    # End test_intersect_larger_inputs method
# End TestIntersect class


if __name__ == '__main__':  # pragma: no cover
    pass
