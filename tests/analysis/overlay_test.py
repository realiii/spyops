# -*- coding: utf-8 -*-
"""
Tests for Overlay
"""


from fudgeo import FeatureClass
from fudgeo.enumeration import ShapeType
from pyproj import CRS
from pytest import mark, param, raises, approx

from spyops.analysis.overlay import (
    erase, intersect, symmetrical_difference, union)
from spyops.environment import Extent
from spyops.environment.core import zm_config
from spyops.shared.constant import EPSG
from spyops.shared.element import copy_element
from spyops.shared.enumeration import (
    AlgorithmOption, AttributeOption, OutputTypeOption)
from spyops.environment.enumeration import (
    OutputMOption, OutputZOption, Setting)
from spyops.shared.exception import OperationsError
from spyops.environment.context import Swap

from tests.util import UseGrids


pytestmark = [mark.overlay, mark.analysis]


class TestErase:
    """
    Test Erase
    """
    @mark.parametrize('fc_name, xy_tolerance, count', [
        ('admin_a', None, 245),
        ('airports_p', None, 29),
        param('roads_l', None, 3054, marks=mark.slow),
        ('admin_mp_a', None, 217),
        ('airports_mp_p', None, 10),
        param('roads_mp_l', None, 14, marks=mark.slow),
        ('admin_a', 0.001, 286),
        ('airports_p', 0.001, 29),
        param('roads_l', 0.001, 3054, marks=mark.slow),
        ('admin_mp_a', 0.001, 217),
        ('airports_mp_p', 0.001, 10),
        param('roads_mp_l', 0.001, 14, marks=mark.slow),
        ('admin_a', 1, 41),
        ('airports_p', 1, 33),
        param('roads_l', 1, 337, marks=mark.slow),
        ('admin_mp_a', 1, 37),
        ('airports_mp_p', 1, 10),
        param('roads_mp_l', 1, 14, marks=mark.slow),
    ])
    def test_reduced(self, inputs, world_features, fresh_gpkg, fc_name, xy_tolerance, count):
        """
        Test erase -- reduced data for faster testing
        """
        eraser = inputs['eraser_a']
        assert len(eraser) == 5
        source = world_features[fc_name]
        assert source.is_multi_part == ('mp' in fc_name)
        with Swap(Setting.EXTENT, Extent.from_feature_class(eraser)):
            target = FeatureClass(geopackage=fresh_gpkg, name=fc_name)
            result = erase(source=source, operator=eraser, target=target,
                           xy_tolerance=xy_tolerance)
            assert len(result) == count
    # End test_reduced method

    @mark.zm
    @mark.parametrize('fc_name, count', [
        ('admin_a', 245),
        ('airports_p', 29),
        ('roads_l', 3054),
        ('admin_mp_a', 217),
        ('airports_mp_p', 10),
        param('roads_mp_l', 14, marks=mark.slow),
    ])
    @mark.parametrize('output_z_option', [
        param(OutputZOption.SAME, marks=mark.large),
        OutputZOption.ENABLED,
        param(OutputZOption.DISABLED, marks=mark.large),
    ])
    @mark.parametrize('output_m_option', [
        param(OutputMOption.SAME, marks=mark.large),
        OutputMOption.ENABLED,
        param(OutputMOption.DISABLED, marks=mark.large),
    ])
    def test_reduced_zm(self, inputs, world_features, fresh_gpkg, fc_name,
                        output_z_option, output_m_option, count):
        """
        Test erase -- reduced data for faster testing -- with ZM
        """
        eraser = inputs['eraser_a']
        assert len(eraser) == 5
        source = world_features[fc_name]
        assert source.is_multi_part == ('mp' in fc_name)
        target = FeatureClass(geopackage=fresh_gpkg, name=fc_name)
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z_option),
              Swap(Setting.OUTPUT_M_OPTION, output_m_option),
              Swap(Setting.Z_VALUE, 123.456),
              Swap(Setting.EXTENT, Extent.from_feature_class(eraser))):
            zm = zm_config(source, eraser)
            result = erase(source=source, operator=eraser, target=target)
        assert len(result) == count
        assert result.has_z == zm.z_enabled
        assert result.has_m == zm.m_enabled
    # End test_reduced_zm method

    def test_reduced_sans_attributes(self, inputs, world_features, fresh_gpkg):
        """
        Test erase -- reduced data for faster testing -- sans attributes
        """
        eraser = inputs['intersect_sans_attr_a']
        assert len(eraser) == 5
        source = world_features['admin_sans_attr_a']
        target = FeatureClass(geopackage=fresh_gpkg, name='sans_attr_a')
        with Swap(Setting.EXTENT, Extent.from_feature_class(eraser)):
            result = erase(source=source, operator=eraser, target=target)
            assert len(result) == 245
    # End test_reduced_sans_attributes method

    @mark.parametrize('fc_name, count', [
        ('airports_p', 3464),
        ('airports_mp_p', 191),
    ])
    @mark.parametrize('xy_tolerance,', [
        None,
        0.001,
    ])
    def test_disjoint(self, inputs, world_features, fresh_gpkg, fc_name, xy_tolerance, count):
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
    # End test_disjoint method

    @mark.parametrize('xy_tolerance, count', [
        (None, 191),
        (0.001, 203),
    ])
    def test_line_on_line(self, world_features, inputs, mem_gpkg, xy_tolerance, count):
        """
        Test erase using a line feature class as the operator on a line feature class
        """
        operator = inputs['rivers_portion_l']
        source = world_features['rivers_l']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = erase(source=source, operator=operator, target=target,
                       xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_line_on_line method

    @mark.parametrize('xy_tolerance, count', [
        (None, 13_958),
        param(0, 13_958, marks=mark.slow),
        param(0.0000000001, 21_353, marks=mark.slow),
        param(0.1, 21_356, marks=mark.slow),
    ])
    def test_line_on_point(self, inputs, mem_gpkg, xy_tolerance, count):
        """
        Test erase using a line feature class as the operator on a point feature class
        """
        operator = inputs['rivers_portion_l']
        source = inputs['river_p']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = erase(source=source, operator=operator, target=target,
                       xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_line_on_point method

    @mark.parametrize('xy_tolerance', [
        None,
        param(0, marks=mark.slow),
        param(0.001, marks=mark.slow),
    ])
    def test_point_on_point(self, inputs, mem_gpkg, xy_tolerance):
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
        assert len(result) == 21_256
    # End test_point_on_point method

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
        Test erase using Output ZM settings
        """
        operator = grid_index[op_name]
        operator = operator.copy(
            name=op_name, where_clause="""DATANAME = '082O01-6'""",
            geopackage=mem_gpkg)
        source = ntdb_zm_meh_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_erased')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            erased = erase(source=source, operator=operator, target=target)
        assert erased.has_z == zm.z_enabled
        assert erased.has_m == zm.m_enabled
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
    def test_output_zm_cleaner(self, grid_index, ntdb_zm_small, mem_gpkg,
                               fc_name, op_name, output_z, output_m):
        """
        Test erase using Output ZM settings using cleaner inputs
        """
        operator = grid_index[op_name]
        operator = operator.copy(
            name=op_name, where_clause="""DATANAME = '082O01-6'""",
            geopackage=mem_gpkg)
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_erased')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            erased = erase(source=source, operator=operator, target=target)
        assert erased.has_z == zm.z_enabled
        assert erased.has_m == zm.m_enabled
    # End test_output_zm_cleaner method

    @mark.benchmark
    @mark.parametrize('name, count', [
        ('utmzone_continentish_a', 11_046),
        ('utmzone_sparse_a', 186_254),
    ])
    def test_larger_inputs(self, inputs, world_features, mem_gpkg, name, count):
        """
        Test erase using larger inputs
        """
        operator = inputs[name]
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name=name)
        result = erase(source=source, operator=operator, target=target)
        assert len(result) == count
    # End test_larger_inputs function

    @mark.benchmark
    @mark.parametrize('name, count', [
        ('utmzone_continentish_a', 15),
        ('utmzone_sparse_a', 31),
    ])
    def test_larger_inputs_extent(self, inputs, world_features, mem_gpkg, name, count):
        """
        Test erase using larger inputs
        """
        operator = inputs[name]
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name=f'erase_{name}')
        with Swap(Setting.EXTENT, Extent.from_bounds(-120, 30, -100, 50, crs=CRS(4326))):
            result = erase(source=source, operator=operator, target=target)
            assert len(result) == count
    # End test_larger_inputs_extent function

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('hydro_4617_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0 )),
        ('hydro_4617_zm_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0 )),
        ('transmission_4617_m_l', EPSG, 2955, False, (674555.1875, 5652839.5, 710282.9375, 5681615.5)),
        ('transmission_4617_z_l', EPSG, 2955, False, (674555.1875, 5652839.5, 710282.9375, 5681615.5)),
        ('toponymy_4617_m_p', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0)),
        ('toponymy_4617_z_p', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0)),
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
        Test erase with output CRS and different input spatial reference systems
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
            result = erase(source=source, operator=operator, target=target)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, extent', [
        ('hydro_4617_a', (-114.5, 51.0, -113.99998474121094, 51.25000762939453)),
        ('hydro_6654_a', (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('hydro_lcc_a', (-1276437.125, 1414240.375, -1239210.75, 1450238.625)),
        ('hydro_utm11_a', (674655.0625, 5653054.0, 710481.625, 5681614.0)),
    ])
    @mark.parametrize('op_name', [
        'grid_10tm_a',
    ])
    def test_different_crs(self, ntdb_zm_small, grid_index, mem_gpkg,
                           fc_name, extent, op_name):
        """
        Test erase with different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_clipped')
        operator = grid_index[op_name].copy(
            f'{op_name}_subset', geopackage=mem_gpkg,
            where_clause="""DATANAME = '082O01-6'""")
        with UseGrids(True):
            result = erase(source=source, operator=operator, target=target)
            srs_id = source.spatial_reference_system.srs_id
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
    # End test_different_crs method
# End TestErase class


class TestIntersect:
    """
    Test Intersect
    """
    @mark.parametrize('fc_name, xy_tolerance, feature_count', [
        ('admin_a', None, 114),
        ('airports_p', None, 40),
        param('roads_l', None, 2514, marks=mark.slow),
        ('admin_mp_a', None, 68),
        ('airports_mp_p', None, 8),
        param('roads_mp_l', None, 14, marks=mark.slow),
        ('admin_a', 0.001, 112),
        ('airports_p', 0.001, 40),
        param('roads_l', 0.001, 2683, marks=mark.slow),
        ('admin_mp_a', 0.001, 68),
        ('airports_mp_p', 0.001, 8),
        param('roads_mp_l', 0.001, 14, marks=mark.slow),
        ('admin_a', 1, 22),
        ('airports_p', 1, 35),
        param('roads_l', 1, 347, marks=mark.slow),
        ('admin_mp_a', 1, 22),
        ('airports_mp_p', 1, 8),
        param('roads_mp_l', 1, 13, marks=mark.slow),
    ])
    def test_xy_tolerance_setting(self, inputs, world_features, mem_gpkg, fc_name, xy_tolerance, feature_count):
        """
        Test intersect using analysis settings for XY tolerance
        """
        operator = inputs['intersect_a']
        assert len(operator) == 5
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with Swap(Setting.XY_TOLERANCE, xy_tolerance):
            result = intersect(source=source, operator=operator, target=target)
        assert len(result) < len(source)
        assert len(result) == feature_count
    # End test_xy_tolerance_setting method

    @mark.parametrize('fc_name, option, field_count', [
        ('admin_a', AttributeOption.ALL, 25),
        ('airports_p', AttributeOption.ALL, 14),
        param('roads_l', AttributeOption.ALL, 22, marks=mark.slow),
        ('admin_mp_a', AttributeOption.ALL, 23),
        ('airports_mp_p', AttributeOption.ALL, 11),
        param('roads_mp_l', AttributeOption.ALL, 11, marks=mark.slow),
        ('admin_a', AttributeOption.ONLY_FID, 4),
        ('airports_p', AttributeOption.ONLY_FID, 4),
        param('roads_l', AttributeOption.ONLY_FID, 4, marks=mark.slow),
        ('admin_mp_a', AttributeOption.ONLY_FID, 4),
        ('airports_mp_p', AttributeOption.ONLY_FID, 4),
        param('roads_mp_l', AttributeOption.ONLY_FID, 4, marks=mark.slow),
        ('admin_a', AttributeOption.ONLY_FID, 4),
        ('airports_p', AttributeOption.ONLY_FID, 4),
        param('roads_l', AttributeOption.ONLY_FID, 4, marks=mark.slow),
        ('admin_mp_a', AttributeOption.ONLY_FID, 4),
        ('admin_a', AttributeOption.SANS_FID, 23),
        ('airports_p', AttributeOption.SANS_FID, 12),
        param('roads_l', AttributeOption.SANS_FID, 20, marks=mark.slow),
        ('admin_mp_a', AttributeOption.SANS_FID, 21),
        ('airports_mp_p', AttributeOption.SANS_FID, 9),
        param('roads_mp_l', AttributeOption.SANS_FID, 9, marks=mark.slow),
        ('admin_a', AttributeOption.SANS_FID, 23),
        ('airports_p', AttributeOption.SANS_FID, 12),
        param('roads_l', AttributeOption.SANS_FID, 20, marks=mark.slow),
        ('admin_mp_a', AttributeOption.SANS_FID, 21),
    ])
    def test_attribute_option(self, inputs, world_features, mem_gpkg, fc_name, option, field_count):
        """
        Test intersect varying attribute option
        """
        operator = inputs['intersect_a']
        assert len(operator) == 5
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = intersect(source=source, operator=operator, target=target,
                           attribute_option=option)
        assert len(result) < len(source)
        assert len(result.fields) == field_count
    # End test_attribute_option method

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
    def test_output_type(self, inputs, world_features, mem_gpkg, fc_name,
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
                assert ShapeType.linestring in result.shape_type
            else:
                assert ShapeType.point in result.shape_type
            assert len(result) < len(source)
            assert len(result) == feature_count
    # End test_output_type method

    @mark.zm
    @mark.parametrize('fc_name, algorithm_option, output_option, feature_count', [
          ('admin_a', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, 0),
          ('roads_l', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, 1659),
          param('admin_mp_a', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, 0, marks=mark.slow),
          param('roads_mp_l', AlgorithmOption.PAIRWISE, OutputTypeOption.LINE, 14, marks=mark.slow),
          ('admin_a', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, 318),
          ('airports_p', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, 26),
          ('roads_l', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, 436),
          param('admin_mp_a', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, 55, marks=mark.slow),
          ('airports_mp_p', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, 8),
          param('roads_mp_l', AlgorithmOption.PAIRWISE, OutputTypeOption.POINT, 12, marks=mark.slow),
          ('admin_a', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, 0),
          ('roads_l', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, 1709),
          param('admin_mp_a', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, 0, marks=mark.slow),
          param('roads_mp_l', AlgorithmOption.CLASSIC, OutputTypeOption.LINE, 24, marks=mark.slow),
          ('admin_a', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, 358),
          ('airports_p', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, 26),
          ('roads_l', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, 536),
          param('admin_mp_a', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, 358, marks=mark.slow),
          ('airports_mp_p', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, 13),
          param('roads_mp_l', AlgorithmOption.CLASSIC, OutputTypeOption.POINT, 22, marks=mark.slow),
    ])
    @mark.parametrize('output_z_option', [
        param(OutputZOption.SAME, marks=mark.large),
        OutputZOption.ENABLED,
        param(OutputZOption.DISABLED, marks=mark.large),
    ])
    @mark.parametrize('output_m_option', [
        param(OutputMOption.SAME, marks=mark.large),
        OutputMOption.ENABLED,
        param(OutputMOption.DISABLED, marks=mark.large),
    ])
    def test_output_type_zm(self, inputs, world_features, mem_gpkg,
                                      fc_name, algorithm_option, output_option,
                                      output_z_option, output_m_option, feature_count):
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
            assert ShapeType.linestring in result.shape_type
        else:
            assert ShapeType.point in result.shape_type
        assert len(result) < len(source)
        assert len(result) == feature_count
        assert result.has_z == zm.z_enabled
        assert result.has_m == zm.m_enabled
    # End test_output_type_zm method

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
    def test_output_zm_classic(self, grid_index, ntdb_zm_meh_small, mem_gpkg,
                               fc_name, op_name, output_z, output_m):
        """
        Test intersect using Output ZM settings and classic algorithm
        """
        operator = grid_index[op_name]
        source = ntdb_zm_meh_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_intersected')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            intersected = intersect(
                source=source, operator=operator,
                target=target, algorithm_option=AlgorithmOption.CLASSIC)
        assert intersected.has_z == zm.z_enabled
        assert intersected.has_m == zm.m_enabled
    # End test_output_zm_classic method

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
    @mark.parametrize('name', [
        'ntdb_zm_small',
        'ntdb_zm_tile'
    ])
    def test_output_zm_classic_cleaner(self, request, grid_index, name, mem_gpkg,
                                       fc_name, op_name, output_z, output_m):
        """
        Test intersect using Output ZM settings and classic algorithm using cleaner inputs
        """
        gpkg = request.getfixturevalue(name)
        operator = grid_index[op_name]
        source = gpkg[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_intersected')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            intersected = intersect(
                source=source, operator=operator, target=target,
                algorithm_option=AlgorithmOption.CLASSIC)
        assert intersected.has_z == zm.z_enabled
        assert intersected.has_m == zm.m_enabled
    # End test_output_zm_classic_cleaner method

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
    def test_output_zm_pairwise(self, grid_index, ntdb_zm_meh_small, mem_gpkg,
                                fc_name, op_name, output_z, output_m):
        """
        Test intersect using Output ZM settings using pairwise algorithm
        """
        operator = grid_index[op_name]
        source = ntdb_zm_meh_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_intersected')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            intersected = intersect(
                source=source, operator=operator,
                target=target, algorithm_option=AlgorithmOption.PAIRWISE)
        assert intersected.has_z == zm.z_enabled
        assert intersected.has_m == zm.m_enabled
    # End test_output_zm_pairwise method

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
    def test_output_zm_pairwise_cleaner(self, grid_index, ntdb_zm_small, mem_gpkg,
                                        fc_name, op_name, output_z, output_m):
        """
        Test intersect using Output ZM settings using pairwise algorithm using cleaner inputs
        """
        operator = grid_index[op_name]
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_intersected')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            intersected = intersect(
                source=source, operator=operator,
                target=target, algorithm_option=AlgorithmOption.PAIRWISE)
        assert intersected.has_z == zm.z_enabled
        assert intersected.has_m == zm.m_enabled
    # End test_output_zm_pairwise_cleaner method

    @mark.parametrize('fc_name, xy_tolerance, feature_count', [
        ('admin_a', None, 128),
        ('airports_p', None, 40),
        ('roads_l', None, 2560),
        param('admin_mp_a', None, 128, marks=mark.slow),
        ('airports_mp_p', None, 12),
        param('roads_mp_l', None, 21, marks=mark.slow),
        ('admin_a', 0.001, 125),
        ('airports_p', 0.001, 40),
        ('roads_l', 0.001, 2729),
        param('admin_mp_a', 0.001, 125, marks=mark.slow),
        ('airports_mp_p', 0.001, 12),
        param('roads_mp_l', 0.001, 21, marks=mark.slow),
    ])
    def test_classic_setting(self, inputs, world_features, mem_gpkg,
                             fc_name, xy_tolerance, feature_count):
        """
        Test intersect using analysis settings -- classic algorithm
        """
        operator = inputs['intersect_a']
        assert len(operator) == 5
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with Swap(Setting.XY_TOLERANCE, xy_tolerance):
            result = intersect(
                source=source, operator=operator, target=target,
                algorithm_option=AlgorithmOption.CLASSIC)
        assert len(result) == feature_count
    # End test_classic_setting method

    @mark.parametrize('algorithm_option, attribute_option, feature_count, field_count', [
        (AlgorithmOption.PAIRWISE, AttributeOption.ALL, 64, 11),
        (AlgorithmOption.PAIRWISE, AttributeOption.SANS_FID, 64, 9),
        (AlgorithmOption.PAIRWISE, AttributeOption.ONLY_FID, 64, 4),
        (AlgorithmOption.CLASSIC, AttributeOption.ALL, 380, 11),
        (AlgorithmOption.CLASSIC, AttributeOption.SANS_FID, 380, 9),
        (AlgorithmOption.CLASSIC, AttributeOption.ONLY_FID, 380, 4),
    ])
    def test_algorithm_option(self, inputs, mem_gpkg, algorithm_option, attribute_option, feature_count, field_count):
        """
        Test Intersect with Options for Classic and Pairwise
        """
        operator = inputs['intersect_a']
        source = inputs['int_flavor_a']
        target = FeatureClass(
            geopackage=mem_gpkg,
            name=f'{str(algorithm_option)}_{attribute_option}_a')
        result = intersect(
            source=source, operator=operator, target=target,
            algorithm_option=algorithm_option, attribute_option=attribute_option)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_algorithm_option method

    @mark.parametrize('algorithm_option, attribute_option, feature_count, field_count', [
        (AlgorithmOption.PAIRWISE, AttributeOption.ALL, 42, 11),
        (AlgorithmOption.PAIRWISE, AttributeOption.SANS_FID, 42, 9),
        (AlgorithmOption.PAIRWISE, AttributeOption.ONLY_FID, 42, 4),
        (AlgorithmOption.CLASSIC, AttributeOption.ALL, 244, 11),
        (AlgorithmOption.CLASSIC, AttributeOption.SANS_FID, 244, 9),
        (AlgorithmOption.CLASSIC, AttributeOption.ONLY_FID, 244, 4),
    ])
    def test_algorithm_option_extent(self, inputs, mem_gpkg, algorithm_option, attribute_option, feature_count, field_count):
        """
        Test Intersect with Options for Classic and Pairwise using Extent
        """
        operator = inputs['intersect_a']
        source = inputs['int_flavor_a']
        target = FeatureClass(
            geopackage=mem_gpkg,
            name=f'{str(algorithm_option)}_{attribute_option}_a')
        with Swap(Setting.EXTENT, Extent.from_bounds(9, 47.3, 14, 50.5, crs=CRS(4326))):
            result = intersect(
                source=source, operator=operator, target=target,
                algorithm_option=algorithm_option, attribute_option=attribute_option)
            assert len(result) == feature_count
            assert len(result.fields) == field_count
    # End test_algorithm_option_extent method

    @mark.parametrize('algorithm_option, attribute_option, feature_count, field_count', [
        (AlgorithmOption.PAIRWISE, AttributeOption.ALL, 114, 4),
        (AlgorithmOption.PAIRWISE, AttributeOption.SANS_FID, 114, 2),
        (AlgorithmOption.PAIRWISE, AttributeOption.ONLY_FID, 114, 4),
        (AlgorithmOption.CLASSIC, AttributeOption.ALL, 128, 4),
        (AlgorithmOption.CLASSIC, AttributeOption.SANS_FID, 128, 2),
        (AlgorithmOption.CLASSIC, AttributeOption.ONLY_FID, 128, 4),
    ])
    def test_option_sans_attributes(self, inputs, world_features, mem_gpkg, algorithm_option, attribute_option, feature_count, field_count):
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
    # End test_option_sans_attributes method

    @mark.parametrize('xy_tolerance, feature_count', [
        (None, 380),
        (0.001, 379),
        (0.05, 369),
    ])
    def test_classic_xy_tolerance(self, inputs, mem_gpkg, xy_tolerance, feature_count):
        """
        Test Intersect classic with XY Tolerance
        """
        operator = inputs['intersect_a']
        source = inputs['int_flavor_a']
        target = FeatureClass(geopackage=mem_gpkg, name='xy_a')
        result = intersect(source=source, operator=operator, target=target,
                           algorithm_option=AlgorithmOption.CLASSIC, xy_tolerance=xy_tolerance)
        assert len(result) == feature_count
    # End test_classic_xy_tolerance method

    @mark.parametrize('option, xy_tolerance, count', [
        (AlgorithmOption.CLASSIC, None, 195),
        (AlgorithmOption.CLASSIC, 0.001, 209),
        (AlgorithmOption.PAIRWISE, None, 195),
        (AlgorithmOption.PAIRWISE, 0.001, 209),
    ])
    def test_line_on_line(self, world_features, inputs, mem_gpkg, option, xy_tolerance, count):
        """
        Test intersect using a line feature class as the operator on a line feature class
        """
        operator = inputs['rivers_portion_l']
        source = world_features['rivers_l']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = intersect(source=source, operator=operator, target=target,
                           algorithm_option=option, xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_line_on_line method

    @mark.parametrize('option, xy_tolerance, count', [
        (AlgorithmOption.CLASSIC, None, 7524),
        param(AlgorithmOption.CLASSIC, 0, 7524, marks=mark.large),
        param(AlgorithmOption.CLASSIC, 0.0000000001, 3, marks=mark.large),
        param(AlgorithmOption.CLASSIC, 0.1, 0, marks=mark.large),
        (AlgorithmOption.PAIRWISE, None, 7524),
        param(AlgorithmOption.PAIRWISE, 0, 7524, marks=mark.large),
        param(AlgorithmOption.PAIRWISE, 0.0000000001, 3, marks=mark.large),
        param(AlgorithmOption.PAIRWISE, 0.1, 0, marks=mark.large),
    ])
    def test_line_on_point(self, inputs, mem_gpkg, option, xy_tolerance, count):
        """
        Test intersect using a line feature class as the operator on a point feature class
        """
        operator = inputs['rivers_portion_l']
        source = inputs['river_p']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = intersect(source=source, operator=operator, target=target,
                           algorithm_option=option, xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_line_on_point method

    @mark.parametrize('option, xy_tolerance, count', [
        (AlgorithmOption.CLASSIC, None, 100),
        (AlgorithmOption.CLASSIC, 0, 100),
        (AlgorithmOption.CLASSIC, 0.001, 100),
        (AlgorithmOption.PAIRWISE, None, 100),
        (AlgorithmOption.PAIRWISE, 0, 100),
        (AlgorithmOption.PAIRWISE, 0.001, 100),
    ])
    def test_point_on_point(self, inputs, mem_gpkg, option, xy_tolerance, count):
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
    # End test_point_on_point method

    @mark.benchmark
    @mark.parametrize('option, name, count', [
        (AlgorithmOption.CLASSIC, 'utmzone_continentish_a', 206_708),
        (AlgorithmOption.CLASSIC, 'utmzone_sparse_a', 26_951),
        (AlgorithmOption.PAIRWISE, 'utmzone_continentish_a', 205_532),
        (AlgorithmOption.PAIRWISE, 'utmzone_sparse_a', 26_949),
    ])
    def test_larger_inputs(self, inputs, world_features, mem_gpkg, option, name, count):
        """
        Test intersect using larger inputs
        """
        operator = inputs[name]
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name=f'intersect_{option}_{name}')
        result = intersect(source=source, operator=operator, target=target, algorithm_option=option)
        assert len(result) == count
    # End test_larger_inputs method

    @mark.benchmark
    @mark.parametrize('option, name, count', [
        (AlgorithmOption.CLASSIC, 'utmzone_continentish_a', 123),
        (AlgorithmOption.CLASSIC, 'utmzone_sparse_a', 58),
        (AlgorithmOption.PAIRWISE, 'utmzone_continentish_a', 123),
        (AlgorithmOption.PAIRWISE, 'utmzone_sparse_a', 58),
    ])
    def test_larger_inputs_extent(self, inputs, world_features, mem_gpkg, option, name, count):
        """
        Test intersect using larger inputs and extent
        """
        operator = inputs[name]
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name=f'intersect_{option}_{name}')
        with Swap(Setting.EXTENT, Extent.from_bounds(-120, 30, -100, 50, crs=CRS(4326))):
            result = intersect(source=source, operator=operator, target=target, algorithm_option=option)
            assert len(result) == count
    # End test_larger_inputs_extent method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('hydro_4617_a', EPSG, 2955, False, (692526.375, 5653596.5, 701490.4375, 5665959.5)),
        ('hydro_4617_zm_a', EPSG, 2955, False, (692526.375, 5653596.5, 701490.4375, 5665959.5)),
        ('transmission_4617_m_l', EPSG, 2955, False, (692509.5625, 5654147.0, 701508.4375, 5667420.5 )),
        ('transmission_4617_z_l', EPSG, 2955, False, (692509.5625, 5654147.0, 701508.4375, 5667420.5 )),
        ('toponymy_4617_m_p', EPSG, 2955, False, (693519.3125, 5654016.0, 701489.6875, 5666594.0)),
        ('toponymy_4617_z_p', EPSG, 2955, False, (693519.3125, 5654016.0, 701489.6875, 5666594.0)),
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
    def test_output_crs_pairwise(self, ntdb_zm_small, grid_index, mem_gpkg,
                                 fc_name, auth_name, srs_id, flag, extent, op_name,
                                 output_z, output_m):
        """
        Test intersect with output CRS and different input spatial reference systems
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
            result = intersect(source=source, operator=operator, target=target,
                               algorithm_option=AlgorithmOption.PAIRWISE)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs_pairwise method

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
    def test_different_crs_pairwise(self, ntdb_zm_small, grid_index, mem_gpkg,
                                    fc_name, extent, op_name):
        """
        Test intersect with different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_clipped')
        operator = grid_index[op_name].copy(
            f'{op_name}_subset', geopackage=mem_gpkg,
            where_clause="""DATANAME = '082O01-6'""")
        with UseGrids(True):
            result = intersect(source=source, operator=operator, target=target,
                               algorithm_option=AlgorithmOption.PAIRWISE)
            assert approx(result.extent, abs=0.001) == extent
            srs_id = source.spatial_reference_system.srs_id
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
    # End test_different_crs_pairwise method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('hydro_4617_a', EPSG, 2955, False, (692526.375, 5653596.5, 701490.4375, 5665959.5)),
        ('hydro_4617_zm_a', EPSG, 2955, False, (692526.375, 5653596.5, 701490.4375, 5665959.5)),
        ('transmission_4617_m_l', EPSG, 2955, False, (692509.5625, 5654147.0, 701508.4375, 5667420.5 )),
        ('transmission_4617_z_l', EPSG, 2955, False, (692509.5625, 5654147.0, 701508.4375, 5667420.5 )),
        ('toponymy_4617_m_p', EPSG, 2955, False, (693519.3125, 5654016.0, 701489.6875, 5666594.0)),
        ('toponymy_4617_z_p', EPSG, 2955, False, (693519.3125, 5654016.0, 701489.6875, 5666594.0)),
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
    def test_output_crs_classic(self, ntdb_zm_small, grid_index, mem_gpkg,
                                fc_name, auth_name, srs_id, flag, extent, op_name,
                                output_z, output_m):
        """
        Test intersect with output CRS and different input spatial reference systems
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
            result = intersect(source=source, operator=operator, target=target,
                               algorithm_option=AlgorithmOption.CLASSIC)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs_classic method

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
    def test_different_crs_classic(self, ntdb_zm_small, grid_index, mem_gpkg,
                                   fc_name, extent, op_name):
        """
        Test intersect with different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_clipped')
        operator = grid_index[op_name].copy(
            f'{op_name}_subset', geopackage=mem_gpkg,
            where_clause="""DATANAME = '082O01-6'""")
        with UseGrids(True):
            result = intersect(source=source, operator=operator, target=target,
                               algorithm_option=AlgorithmOption.CLASSIC)
            assert approx(result.extent, abs=0.001) == extent
            srs_id = source.spatial_reference_system.srs_id
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
    # End test_different_crs_classic method
# End TestIntersect class


class TestSymmetricalDifference:
    """
    Tests for Symmetrical Difference
    """
    @mark.benchmark
    @mark.parametrize('option, count', [
        (AlgorithmOption.CLASSIC, 16_457),
        (AlgorithmOption.PAIRWISE, 16_328),
    ])
    def test_larger_inputs(self, ntdb_zm, mem_gpkg, option, count):
        """
        Test symmetrical difference using larger inputs
        """
        source = ntdb_zm['hydro_a']
        operator = ntdb_zm['structures_a']
        target = FeatureClass(geopackage=mem_gpkg, name=f'symdiff_{option}')
        result = symmetrical_difference(source=source, operator=operator, target=target, algorithm_option=option)
        assert len(result) == count
    # End test_larger_inputs method

    @mark.benchmark
    @mark.parametrize('option, count', [
        (AlgorithmOption.CLASSIC, 7593),
        (AlgorithmOption.PAIRWISE, 7475),
    ])
    def test_larger_inputs_extent(self, ntdb_zm, mem_gpkg, option, count):
        """
        Test symmetrical difference using larger inputs and extent
        """
        source = ntdb_zm['hydro_a']
        operator = ntdb_zm['structures_a']
        target = FeatureClass(geopackage=mem_gpkg, name=f'symdiff_{option}')
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.5, 50.75, -112.5, 51.25, crs=CRS(4326))):
            result = symmetrical_difference(source=source, operator=operator, target=target, algorithm_option=option)
            assert len(result) == count
    # End test_larger_inputs_extent method

    def test_holes_and_shifted(self, inputs, mem_gpkg):
        """
        Test for symmetric difference using small datasets
        """
        source = inputs['intersect_holes_a']
        operator = inputs['intersect_holes_shifted_a']
        target = FeatureClass(geopackage=mem_gpkg, name='sym_diff')
        symmetrical_difference(source=source, operator=operator, target=target)
        assert len(target) == 36
        cursor = target.select(where_clause="""fid_intersect_holes_a IS NULL""")
        assert len(cursor.fetchall()) == 18
        cursor = target.select(where_clause="""fid_intersect_holes_shifted_a IS NULL""")
        assert len(cursor.fetchall()) == 18
    # End test_holes_and_shifted method

    @mark.parametrize('source_name, operator_name, feature_count, field_count', [
        ('hydro_a', 'hydro_a', 194, 42),
        ('hydro_a', 'hydro_zm_a', 194, 43),
        ('hydro_zm_a', 'hydro_zm_a', 194, 44),
        ('structures_a', 'structures_a', 33, 42),
        ('structures_a', 'structures_zm_a', 33, 43),
        ('structures_zm_a', 'structures_zm_a', 33, 44),
        ('structures_p', 'structures_p', 852, 38),
        ('structures_p', 'structures_zm_p', 852, 38),
        ('structures_zm_p', 'structures_zm_p', 852, 38),
        ('toponymy_mp', 'toponymy_mp', 2, 40),
        ('toponymy_mp', 'toponymy_zm_mp', 2, 40),
        ('toponymy_zm_mp', 'toponymy_zm_mp', 2, 40),
        ('transmission_l', 'transmission_l', 21, 42),
        ('transmission_l', 'transmission_zm_l', 21, 43),
        ('transmission_zm_l', 'transmission_zm_l', 21, 44),
    ])
    def test_xy_tolerance_setting_pairwise(self, ntdb_zm_tile, mem_gpkg, source_name,
                                           operator_name, feature_count, field_count):
        """
        Test sym diff using analysis settings for XY tolerance and pairwise algorithm
        """
        source = ntdb_zm_tile[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        operator = ntdb_zm_tile[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-2', '082O01-3')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        with Swap(Setting.XY_TOLERANCE, 0.000001):
            result = symmetrical_difference(
                source=source, operator=operator, target=target,
                attribute_option=AttributeOption.ALL)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_xy_tolerance_setting_pairwise method

    @mark.parametrize('source_name, operator_name, feature_count, field_count', [
        ('hydro_a', 'hydro_a', 194, 42),
        ('hydro_a', 'hydro_zm_a', 194, 43),
        ('hydro_zm_a', 'hydro_zm_a', 194, 44),
        ('structures_a', 'structures_a', 35, 42),
        ('structures_a', 'structures_zm_a', 35, 43),
        ('structures_zm_a', 'structures_zm_a', 35, 44),
        ('structures_p', 'structures_p', 852, 38),
        ('structures_p', 'structures_zm_p', 852, 38),
        ('structures_zm_p', 'structures_zm_p', 852, 38),
        ('toponymy_mp', 'toponymy_mp', 2, 40),
        ('toponymy_mp', 'toponymy_zm_mp', 2, 40),
        ('toponymy_zm_mp', 'toponymy_zm_mp', 2, 40),
        ('transmission_l', 'transmission_l', 21, 42),
        ('transmission_l', 'transmission_zm_l', 21, 43),
        ('transmission_zm_l', 'transmission_zm_l', 21, 44),
    ])
    def test_xy_tolerance_setting_classic(self, ntdb_zm_tile, mem_gpkg, source_name,
                                          operator_name, feature_count, field_count):
        """
        Test sym diff using analysis settings for XY tolerance
        """
        source = ntdb_zm_tile[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        operator = ntdb_zm_tile[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-2', '082O01-3')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        with Swap(Setting.XY_TOLERANCE, 0.00001):
            result = symmetrical_difference(
                source=source, operator=operator, target=target,
                attribute_option=AttributeOption.ALL,
                algorithm_option=AlgorithmOption.CLASSIC)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_xy_tolerance_setting_classic method

    @mark.parametrize('source_name, operator_name, feature_count, field_count', [
        ('hydro_a', 'hydro_zm_a', 133, 43),
        ('structures_a', 'structures_zm_a', 30, 43),
        ('structures_p', 'structures_zm_p', 571, 38),
        ('toponymy_mp', 'toponymy_zm_mp', 2, 40),
        ('transmission_l', 'transmission_zm_l', 20, 43),
    ])
    def test_extent_setting_pairwise(self, ntdb_zm_tile, mem_gpkg, source_name,
                                     operator_name, feature_count, field_count):
        """
        Test sym diff using an extent and pairwise algorithm
        """
        source = ntdb_zm_tile[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        operator = ntdb_zm_tile[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-2', '082O01-3')""")
        print(source.extent)
        print(operator.extent)
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.5, 51.05, -114.3, 51.25, crs=CRS(4326))):
            result = symmetrical_difference(
                source=source, operator=operator, target=target,
                attribute_option=AttributeOption.ALL,
                algorithm_option=AlgorithmOption.PAIRWISE)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_extent_setting_pairwise method

    @mark.parametrize('source_name, operator_name, feature_count, field_count', [
        ('hydro_a', 'hydro_zm_a', 133, 43),
        ('structures_a', 'structures_zm_a', 34, 43),
        ('structures_p', 'structures_zm_p', 571, 38),
        ('toponymy_mp', 'toponymy_zm_mp', 2, 40),
        ('transmission_l', 'transmission_zm_l', 20, 43),
    ])
    def test_extent_setting_classic(self, ntdb_zm_tile, mem_gpkg, source_name,
                                    operator_name, feature_count, field_count):
        """
        Test sym diff using an extent and classic algorithm
        """
        source = ntdb_zm_tile[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        operator = ntdb_zm_tile[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-2', '082O01-3')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.5, 51.05, -114.3, 51.25, crs=CRS(4326))):
            result = symmetrical_difference(
                source=source, operator=operator, target=target,
                attribute_option=AttributeOption.ALL,
                algorithm_option=AlgorithmOption.CLASSIC)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_extent_setting_classic method

    @mark.zm
    @mark.parametrize('source_name, operator_name', [
        ('hydro_a', 'hydro_a'),
        ('hydro_a', 'hydro_z_a'),
        ('hydro_m_a', 'hydro_z_a'),
        ('structures_a', 'structures_a'),
        ('structures_a', 'structures_m_a'),
        ('structures_m_a', 'structures_z_a'),
        ('structures_p', 'structures_p'),
        ('structures_p', 'structures_m_p'),
        ('structures_m_p', 'structures_z_p'),
        ('transmission_l', 'transmission_l'),
        ('transmission_l', 'transmission_z_l'),
        ('transmission_l', 'transmission_m_l'),
        ('transmission_zm_l', 'transmission_m_l'),
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
    def test_output_zm_pairwise_cleaner(self, ntdb_zm_tile, mem_gpkg, source_name,
                                        operator_name, output_z, output_m):
        """
        Test sym diff using Output ZM settings using pairwise algorithm using cleaner inputs
        """
        source = ntdb_zm_tile[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        operator = ntdb_zm_tile[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-2', '082O01-3')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            result = symmetrical_difference(
                source=source, operator=operator,
                target=target, algorithm_option=AlgorithmOption.PAIRWISE)
        assert result.has_z == zm.z_enabled
        assert result.has_m == zm.m_enabled
    # End test_output_zm_pairwise_cleaner method

    def test_sans_attributes(self, inputs, world_features, fresh_gpkg):
        """
        Test sym diff -- reduced data for faster testing -- sans attributes
        """
        operator = inputs['intersect_sans_attr_a']
        assert len(operator) == 5
        source = world_features['admin_sans_attr_a']
        target = FeatureClass(geopackage=fresh_gpkg, name='sans_attr_a')
        with Swap(Setting.EXTENT, Extent.from_feature_class(operator)):
            result = symmetrical_difference(source=source, operator=operator, target=target)
            assert len(result) == 245
            assert len(result.fields) == 4
    # End test_sans_attributes method

    @mark.parametrize('source_name, operator_name, option, field_count', [
        ('hydro_a', 'hydro_a', AttributeOption.SANS_FID, 40),
        ('structures_a', 'structures_a', AttributeOption.SANS_FID, 40),
        ('structures_p', 'structures_p', AttributeOption.SANS_FID, 36),
        ('toponymy_mp', 'toponymy_mp', AttributeOption.SANS_FID, 38),
        ('transmission_l', 'transmission_l', AttributeOption.SANS_FID, 40),
        ('hydro_a', 'hydro_a', AttributeOption.ONLY_FID, 4),
        ('structures_a', 'structures_a', AttributeOption.ONLY_FID, 4),
        ('structures_p', 'structures_p', AttributeOption.ONLY_FID, 4),
        ('toponymy_mp', 'toponymy_mp', AttributeOption.ONLY_FID, 4),
        ('transmission_l', 'transmission_l', AttributeOption.ONLY_FID, 4),
    ])
    def test_attribute_option(self, inputs, ntdb_zm_tile, mem_gpkg,
                                       source_name, operator_name, option, field_count):
        """
        Test sym diff using analysis settings for XY tolerance
        and varying attribute option
        """
        source = ntdb_zm_tile[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        operator = ntdb_zm_tile[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-2', '082O01-3')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        result = symmetrical_difference(
            source=source, operator=operator, target=target,
            attribute_option=option)
        assert len(result.fields) == field_count
    # End test_attribute_option method

    @mark.zm
    @mark.parametrize('fc_name, count', [
        ('hydro_a', 88),
        ('hydro_m_a', 88),
        ('hydro_zm_a', 88),
        ('structures_a', 30),
        ('structures_m_a', 30),
        ('structures_z_a', 30),
        ('structures_zm_a', 30),
        ('structures_m_ma', 10),
        ('structures_z_ma', 10),
        ('structures_zm_ma', 10),
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
    def test_target_full_disjoint_pairwise(self, grid_index, ntdb_zm_tile,
                                           mem_gpkg, fc_name, count,
                                           op_name, output_z, output_m):
        """
        Test target full, exercising process disjoint and handling
        different ZM dimensions
        """
        option = AttributeOption.ALL
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = copy_element(
            ntdb_zm_tile[fc_name], target=FeatureClass(mem_gpkg, fc_name),
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        source.add_spatial_index()
        operator = copy_element(
            grid_index[op_name], target=FeatureClass(mem_gpkg, op_name),
            where_clause="""DATANAME = '082O01-8'""")
        operator.add_spatial_index()
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            result = symmetrical_difference(
                source=source, operator=operator,
                target=target, attribute_option=option)
        assert result.has_z == zm.z_enabled
        assert result.has_m == zm.m_enabled
        assert result.count == count
    # End test_target_full_disjoint_pairwise method

    @mark.zm
    @mark.parametrize('fc_name, count', [
        ('hydro_a', 88),
        ('hydro_m_a', 88),
        ('hydro_zm_a', 88),
        ('structures_a', 34),
        ('structures_m_a', 34),
        ('structures_z_a', 34),
        ('structures_zm_a', 34),
        ('structures_m_ma', 34),
        ('structures_z_ma', 34),
        ('structures_zm_ma', 34),
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
    def test_target_full_disjoint_classic(self, grid_index, ntdb_zm_tile, mem_gpkg,
                                          fc_name, count, op_name, output_z, output_m):
        """
        Test target full, exercising process disjoint and handling
        different ZM dimensions
        """
        option = AttributeOption.ALL
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = copy_element(
            ntdb_zm_tile[fc_name], target=FeatureClass(mem_gpkg, fc_name),
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        source.add_spatial_index()
        operator = copy_element(
            grid_index[op_name], target=FeatureClass(mem_gpkg, op_name),
            where_clause="""DATANAME = '082O01-8'""")
        operator.add_spatial_index()
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            result = symmetrical_difference(
                source=source, operator=operator,
                algorithm_option=AlgorithmOption.CLASSIC,
                target=target, attribute_option=option)
        assert result.has_z == zm.z_enabled
        assert result.has_m == zm.m_enabled
        assert result.count == count
    # End test_target_full_disjoint_classic method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('hydro_4617_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('hydro_lcc_zm_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0)),
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
    def test_output_crs_pairwise(self, ntdb_zm_small, grid_index, mem_gpkg,
                                 fc_name, auth_name, srs_id, flag, extent, op_name,
                                 output_z, output_m):
        """
        Test sym diff with output CRS and different input spatial reference systems
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
            result = symmetrical_difference(
                source=source, operator=operator, target=target,
                algorithm_option=AlgorithmOption.PAIRWISE)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs_pairwise method

    @mark.transform
    @mark.parametrize('fc_name, extent', [
        ('hydro_4617_a', (-114.5, 51.0, -113.99998474121094, 51.25000762939453)),
        ('hydro_6654_a', (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('hydro_lcc_a', (-1276437.125, 1414240.375, -1239210.75, 1450238.625)),
        ('hydro_utm11_a', (674655.0625, 5653054.0, 710481.625, 5681614.0)),
    ])
    @mark.parametrize('op_name', [
        'grid_10tm_a',
    ])
    def test_different_crs_pairwise(self, ntdb_zm_small, grid_index, mem_gpkg,
                                    fc_name, extent, op_name):
        """
        Test sym diff with different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_clipped')
        operator = grid_index[op_name].copy(
            f'{op_name}_subset', geopackage=mem_gpkg,
            where_clause="""DATANAME = '082O01-6'""")
        with UseGrids(True):
            result = symmetrical_difference(
                source=source, operator=operator, target=target,
                algorithm_option=AlgorithmOption.PAIRWISE)
            assert approx(result.extent, abs=0.001) == extent
            srs_id = source.spatial_reference_system.srs_id
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
    # End test_different_crs_pairwise method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('hydro_4617_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('hydro_lcc_zm_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0)),
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
    def test_output_crs_classic(self, ntdb_zm_small, grid_index, mem_gpkg,
                                fc_name, auth_name, srs_id, flag, extent, op_name,
                                output_z, output_m):
        """
        Test sym diff with output CRS and different input spatial reference systems
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
            result = symmetrical_difference(
                source=source, operator=operator, target=target,
                algorithm_option=AlgorithmOption.CLASSIC)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs_classic method

    @mark.transform
    @mark.parametrize('fc_name, extent', [
        ('hydro_4617_a', (-114.5, 51.0, -113.99998474121094, 51.25000762939453)),
        ('hydro_6654_a', (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('hydro_lcc_a', (-1276437.125, 1414240.375, -1239210.75, 1450238.625)),
        ('hydro_utm11_a', (674655.0625, 5653054.0, 710481.625, 5681614.0)),
    ])
    @mark.parametrize('op_name', [
        'grid_10tm_a',
    ])
    def test_different_crs_classic(self, ntdb_zm_small, grid_index, mem_gpkg,
                                    fc_name, extent, op_name):
        """
        Test sym diff with different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_clipped')
        operator = grid_index[op_name].copy(
            f'{op_name}_subset', geopackage=mem_gpkg,
            where_clause="""DATANAME = '082O01-6'""")
        with UseGrids(True):
            result = symmetrical_difference(
                source=source, operator=operator, target=target,
                algorithm_option=AlgorithmOption.CLASSIC)
            assert approx(result.extent, abs=0.001) == extent
            srs_id = source.spatial_reference_system.srs_id
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
    # End test_different_crs_classic method
# End TestSymmetricalDifference class


class TestUnion:
    """
    Tests for Union
    """
    @mark.benchmark
    @mark.parametrize('option, count', [
        (AlgorithmOption.CLASSIC, 16_514),
        (AlgorithmOption.PAIRWISE, 16_384),
    ])
    def test_larger_inputs(self, ntdb_zm, mem_gpkg, option, count):
        """
        Test union using larger inputs
        """
        source = ntdb_zm['hydro_a']
        operator = ntdb_zm['structures_a']
        target = FeatureClass(geopackage=mem_gpkg, name=f'union_{option}')
        result = union(source=source, operator=operator, target=target, algorithm_option=option)
        assert len(result) == count
    # End test_larger_inputs method

    @mark.benchmark
    @mark.parametrize('option, count', [
        (AlgorithmOption.CLASSIC, 7645),
        (AlgorithmOption.PAIRWISE, 7526),
    ])
    def test_larger_inputs_extent(self, ntdb_zm, mem_gpkg, option, count):
        """
        Test union using larger inputs and extent
        """
        source = ntdb_zm['hydro_a']
        operator = ntdb_zm['structures_a']
        target = FeatureClass(geopackage=mem_gpkg, name=f'union_{option}')
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.5, 50.75, -112.5, 51.25, crs=CRS(4326))):
            result = union(source=source, operator=operator, target=target, algorithm_option=option)
            assert len(result) == count
    # End test_larger_inputs_extent method

    @mark.parametrize('algorithm_option, feature_count, hole_count, shifted_count', [
        (AlgorithmOption.PAIRWISE, 50, 18, 18),
        (AlgorithmOption.CLASSIC, 82, 29, 29),
    ])
    def test_holes_and_shifted(self, inputs, mem_gpkg, algorithm_option, feature_count, hole_count, shifted_count):
        """
        Test for union using small datasets
        """
        source = inputs['intersect_holes_a']
        operator = inputs['intersect_holes_shifted_a']
        target = FeatureClass(geopackage=mem_gpkg, name='union_holes_shifted_a')
        union(source=source, operator=operator, target=target, algorithm_option=algorithm_option)
        assert len(target) == feature_count
        cursor = target.select(where_clause="""fid_intersect_holes_a IS NULL""")
        assert len(cursor.fetchall()) == hole_count
        cursor = target.select(where_clause="""fid_intersect_holes_shifted_a IS NULL""")
        assert len(cursor.fetchall()) == shifted_count
        cursor = target.select(where_clause="""fid_intersect_holes_a IS NOT NULL AND fid_intersect_holes_shifted_a IS NOT NULL""")
        assert len(cursor.fetchall()) == feature_count - (hole_count + shifted_count)
    # End test_holes_and_shifted method

    @mark.parametrize('source_name, operator_name, feature_count, field_count', [
        ('hydro_a', 'hydro_a', 227, 42),
        ('hydro_a', 'hydro_zm_a', 227, 43),
        ('hydro_zm_a', 'hydro_zm_a', 227, 44),
        ('structures_a', 'structures_a', 34, 42),
        ('structures_a', 'structures_zm_a', 34, 43),
        ('structures_zm_a', 'structures_zm_a', 34, 44),
    ])
    def test_xy_tolerance_setting(self, ntdb_zm_tile, mem_gpkg, source_name,
                                  operator_name, feature_count, field_count):
        """
        Test union using analysis settings for XY tolerance
        """
        source = ntdb_zm_tile[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        operator = ntdb_zm_tile[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-2', '082O01-3')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        with Swap(Setting.XY_TOLERANCE, 0.000001):
            result = union(
                source=source, operator=operator, target=target,
                attribute_option=AttributeOption.ALL)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_xy_tolerance_setting method

    @mark.parametrize('source_name, operator_name, feature_count, field_count', [
        ('hydro_a', 'hydro_zm_a', 157, 43),
        ('structures_a', 'structures_zm_a', 31, 43),
    ])
    def test_extent_setting_pairwise(self, ntdb_zm_tile, mem_gpkg, source_name,
                                     operator_name, feature_count, field_count):
        """
        Test union using an extent and pairwise algorithm
        """
        source = ntdb_zm_tile[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        operator = ntdb_zm_tile[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-2', '082O01-3')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.5, 51.05, -114.3, 51.25, crs=CRS(4326))):
            result = union(
                source=source, operator=operator, target=target,
                attribute_option=AttributeOption.ALL)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_extent_setting_pairwise method

    @mark.parametrize('source_name, operator_name, feature_count, field_count', [
        ('hydro_a', 'hydro_zm_a', 157, 43),
        ('structures_a', 'structures_zm_a', 35, 43),
    ])
    def test_extent_setting_classic(self, ntdb_zm_tile, mem_gpkg, source_name,
                                    operator_name, feature_count, field_count):
        """
        Test union using an extent and classic algorithm
        """
        source = ntdb_zm_tile[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        operator = ntdb_zm_tile[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-2', '082O01-3')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.5, 51.05, -114.3, 51.25, crs=CRS(4326))):
            result = union(
                source=source, operator=operator, target=target,
                algorithm_option=AlgorithmOption.CLASSIC,
                attribute_option=AttributeOption.ALL)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_extent_setting_classic method

    @mark.parametrize('source_name, operator_name, feature_count, field_count', [
        ('hydro_a', 'hydro_a', 227, 42),
        ('hydro_a', 'hydro_zm_a', 227, 43),
        ('hydro_zm_a', 'hydro_zm_a', 227, 44),
        ('structures_a', 'structures_a', 36, 42),
        ('structures_a', 'structures_zm_a', 36, 43),
        ('structures_zm_a', 'structures_zm_a', 36, 44),
    ])
    def test_xy_tolerance_setting_classic(self, ntdb_zm_tile, mem_gpkg, source_name,
                                          operator_name, feature_count, field_count):
        """
        Test union using analysis settings for XY tolerance
        """
        source = ntdb_zm_tile[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        operator = ntdb_zm_tile[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-2', '082O01-3')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        with Swap(Setting.XY_TOLERANCE, 0.00001):
            result = union(
                source=source, operator=operator, target=target,
                attribute_option=AttributeOption.ALL,
                algorithm_option=AlgorithmOption.CLASSIC)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_xy_tolerance_setting_classic method

    @mark.zm
    @mark.parametrize('source_name, operator_name', [
        ('hydro_a', 'hydro_a'),
        ('hydro_a', 'hydro_z_a'),
        ('hydro_m_a', 'hydro_z_a'),
        ('structures_a', 'structures_a'),
        ('structures_a', 'structures_m_a'),
        ('structures_m_a', 'structures_z_a'),
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
    def test_output_zm_pairwise_cleaner(self, ntdb_zm_tile, mem_gpkg, source_name,
                                        operator_name, output_z, output_m):
        """
        Test union using Output ZM settings using pairwise algorithm using cleaner inputs
        """
        source = ntdb_zm_tile[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        operator = ntdb_zm_tile[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-2', '082O01-3')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            result = union(
                source=source, operator=operator,
                target=target, algorithm_option=AlgorithmOption.PAIRWISE)
        assert result.has_z == zm.z_enabled
        assert result.has_m == zm.m_enabled
    # End test_output_zm_pairwise_cleaner method

    def test_sans_attributes(self, inputs, world_features, fresh_gpkg):
        """
        Test union -- reduced data for faster testing -- sans attributes
        """
        operator = inputs['intersect_sans_attr_a']
        assert len(operator) == 5
        source = world_features['admin_sans_attr_a']
        target = FeatureClass(geopackage=fresh_gpkg, name='sans_attr_a')
        with Swap(Setting.EXTENT, Extent.from_feature_class(operator)):
            result = union(source=source, operator=operator, target=target)
            assert len(result) == 359
            assert len(result.fields) == 4
    # End test_sans_attributes method

    @mark.parametrize('source_name, operator_name, option, field_count', [
        ('hydro_a', 'hydro_a', AttributeOption.SANS_FID, 40),
        ('structures_a', 'structures_a', AttributeOption.SANS_FID, 40),
        ('hydro_a', 'hydro_a', AttributeOption.ONLY_FID, 4),
        ('structures_a', 'structures_a', AttributeOption.ONLY_FID, 4),
    ])
    def test_attribute_option(self, inputs, ntdb_zm_tile, mem_gpkg,
                              source_name, operator_name, option, field_count):
        """
        Test union using analysis settings for XY tolerance
        and varying attribute option
        """
        source = ntdb_zm_tile[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        operator = ntdb_zm_tile[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082O01-2', '082O01-3')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        result = union(
            source=source, operator=operator, target=target,
            attribute_option=option)
        assert len(result.fields) == field_count
    # End test_attribute_option method

    @mark.zm
    @mark.parametrize('fc_name, count', [
        ('hydro_a', 88),
        ('hydro_m_a', 88),
        ('hydro_zm_a', 88),
        ('structures_a', 30),
        ('structures_m_a', 30),
        ('structures_z_a', 30),
        ('structures_zm_a', 30),
        ('structures_m_ma', 10),
        ('structures_z_ma', 10),
        ('structures_zm_ma', 10),
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
    def test_target_full_disjoint_pairwise(self, grid_index, ntdb_zm_tile,
                                           mem_gpkg, fc_name, count,
                                           op_name, output_z, output_m):
        """
        Test target full, exercising process disjoint and handling
        different ZM dimensions
        """
        option = AttributeOption.ALL
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = copy_element(
            ntdb_zm_tile[fc_name], target=FeatureClass(mem_gpkg, fc_name),
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        source.add_spatial_index()
        operator = copy_element(
            grid_index[op_name], target=FeatureClass(mem_gpkg, op_name),
            where_clause="""DATANAME = '082O01-8'""")
        operator.add_spatial_index()
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            result = union(
                source=source, operator=operator,
                target=target, attribute_option=option)
        assert result.has_z == zm.z_enabled
        assert result.has_m == zm.m_enabled
        assert result.count == count
    # End test_target_full_disjoint_pairwise method

    @mark.zm
    @mark.parametrize('fc_name, count', [
        ('hydro_a', 88),
        ('hydro_m_a', 88),
        ('hydro_zm_a', 88),
        ('structures_a', 34),
        ('structures_m_a', 34),
        ('structures_z_a', 34),
        ('structures_zm_a', 34),
        ('structures_m_ma', 34),
        ('structures_z_ma', 34),
        ('structures_zm_ma', 34),
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
    def test_target_full_disjoint_classic(self, grid_index, ntdb_zm_tile, mem_gpkg,
                                          fc_name, count, op_name, output_z, output_m):
        """
        Test target full, exercising process disjoint and handling
        different ZM dimensions
        """
        option = AttributeOption.ALL
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = copy_element(
            ntdb_zm_tile[fc_name], target=FeatureClass(mem_gpkg, fc_name),
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        source.add_spatial_index()
        operator = copy_element(
            grid_index[op_name], target=FeatureClass(mem_gpkg, op_name),
            where_clause="""DATANAME = '082O01-8'""")
        operator.add_spatial_index()
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            result = union(
                source=source, operator=operator,
                algorithm_option=AlgorithmOption.CLASSIC,
                target=target, attribute_option=option)
        assert result.has_z == zm.z_enabled
        assert result.has_m == zm.m_enabled
        assert result.count == count
    # End test_target_full_disjoint_classic method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('hydro_4617_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('hydro_lcc_zm_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0)),
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
    def test_output_crs_pairwise(self, ntdb_zm_small, grid_index, mem_gpkg,
                                 fc_name, auth_name, srs_id, flag, extent, op_name,
                                 output_z, output_m):
        """
        Test sym diff with output CRS and different input spatial reference systems
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
            result = union(
                source=source, operator=operator, target=target,
                algorithm_option=AlgorithmOption.PAIRWISE)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs_pairwise method

    @mark.transform
    @mark.parametrize('fc_name, extent', [
        ('hydro_4617_a', (-114.5, 51.0, -113.99998474121094, 51.25000762939453)),
        ('hydro_6654_a', (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('hydro_lcc_a', (-1276437.125, 1414240.375, -1239210.75, 1450238.625)),
        ('hydro_utm11_a', (674655.0625, 5653054.0, 710481.625, 5681614.0)),
    ])
    @mark.parametrize('op_name', [
        'grid_10tm_a',
    ])
    def test_different_crs_pairwise(self, ntdb_zm_small, grid_index, mem_gpkg,
                                    fc_name, extent, op_name):
        """
        Test sym diff with different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_clipped')
        operator = grid_index[op_name].copy(
            f'{op_name}_subset', geopackage=mem_gpkg,
            where_clause="""DATANAME = '082O01-6'""")
        with UseGrids(True):
            result = union(
                source=source, operator=operator, target=target,
                algorithm_option=AlgorithmOption.PAIRWISE)
            assert approx(result.extent, abs=0.001) == extent
            srs_id = source.spatial_reference_system.srs_id
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
    # End test_different_crs_pairwise method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('hydro_4617_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('hydro_lcc_zm_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0)),
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
    def test_output_crs_classic(self, ntdb_zm_small, grid_index, mem_gpkg,
                                fc_name, auth_name, srs_id, flag, extent, op_name,
                                output_z, output_m):
        """
        Test sym diff with output CRS and different input spatial reference systems
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
            result = union(
                source=source, operator=operator, target=target,
                algorithm_option=AlgorithmOption.CLASSIC)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs_classic method

    @mark.transform
    @mark.parametrize('fc_name, extent', [
        ('hydro_4617_a', (-114.5, 51.0, -113.99998474121094, 51.25000762939453)),
        ('hydro_6654_a', (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('hydro_lcc_a', (-1276437.125, 1414240.375, -1239210.75, 1450238.625)),
        ('hydro_utm11_a', (674655.0625, 5653054.0, 710481.625, 5681614.0)),
    ])
    @mark.parametrize('op_name', [
        'grid_10tm_a',
    ])
    def test_different_crs_classic(self, ntdb_zm_small, grid_index, mem_gpkg,
                                   fc_name, extent, op_name):
        """
        Test sym diff with different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_clipped')
        operator = grid_index[op_name].copy(
            f'{op_name}_subset', geopackage=mem_gpkg,
            where_clause="""DATANAME = '082O01-6'""")
        with UseGrids(True):
            result = union(
                source=source, operator=operator, target=target,
                algorithm_option=AlgorithmOption.CLASSIC)
            assert approx(result.extent, abs=0.001) == extent
            srs_id = source.spatial_reference_system.srs_id
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
    # End test_different_crs_classic method
# End TestUnion class


if __name__ == '__main__':  # pragma: no cover
    pass
