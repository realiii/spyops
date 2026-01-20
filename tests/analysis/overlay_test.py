# -*- coding: utf-8 -*-
"""
Tests for Overlay
"""


from fudgeo import FeatureClass
from fudgeo.enumeration import GeometryType
from pytest import mark, param, raises

from spyops.analysis.overlay import erase, intersect, symmetrical_difference
from spyops.environment.core import zm_config
from spyops.shared.element import copy_element
from spyops.shared.enumeration import (
    AlgorithmOption, AttributeOption, OutputTypeOption)
from spyops.environment.enumeration import (
    OutputMOption, OutputZOption, Setting)
from spyops.query.overlay import QueryErase
from spyops.shared.exception import OperationsError
from spyops.environment.context import Swap


pytestmark = [mark.overlay, mark.query]


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
    def test_erase_reduced_zm(self, inputs, world_features, fresh_gpkg, fc_name,
                              output_z_option, output_m_option, count):
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
            result = erase(source=subset, operator=eraser, target=target)
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

    @mark.parametrize('fc_name, count', [
        ('airports_p', 3464),
        ('airports_mp_p', 191),
    ])
    @mark.parametrize('xy_tolerance,', [
        None,
        0.001,
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
        (0.001, 203),
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
        param(0, 13_958, marks=mark.slow),
        param(0.0000000001, 21_353, marks=mark.slow),
        param(0.1, 21_356, marks=mark.slow),
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

    @mark.parametrize('xy_tolerance', [
        None,
        param(0, marks=mark.slow),
        param(0.001, marks=mark.slow),
    ])
    def test_erase_point_on_point(self, inputs, mem_gpkg, xy_tolerance):
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
    # End test_erase_point_on_point method

    @mark.zm

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
        assert len(erased) <= len(source)
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
        assert len(erased) <= len(source)
    # End test_output_zm_cleaner method

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
    @mark.large
    @mark.parametrize('fc_name', [
        'hydro_a',
        'structures_a',
        'structures_m_a',
        'structures_m_ma',
        'structures_ma',
        'structures_p',
        'structures_vcs_z_a',
        'structures_vcs_z_ma',
        'structures_vcs_zm_a',
        'structures_vcs_zm_ma',
        'structures_z_a',
        'structures_z_ma',
        'structures_zm_a',
        'structures_zm_ma',
        'topography_l',
        'toponymy_mp',
        'toponymy_p',
        'toponymy_vcs_z_mp',
        'toponymy_vcs_z_p',
        'toponymy_z_mp',
        'toponymy_z_p',
        'transmission_l',
        'transmission_m_l',
        'transmission_ml',
        'transmission_p',
        'transmission_vcs_z_l',
        'transmission_vcs_z_ml',
        'transmission_vcs_zm_l',
        'transmission_z_l',
        'transmission_zm_l',
    ])
    @mark.parametrize('op_name', [
        'index_a',
        'index_m_a',
        'index_z_a',
        'index_zm_a',
        'index_zm_nan_a',
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
    def test_output_zm_classic(self, ntdb_zm_meh, mem_gpkg, fc_name, op_name, output_z, output_m):
        """
        Test intersect using Output ZM settings and classic algorithm
        """
        operator = ntdb_zm_meh[op_name]
        source = ntdb_zm_meh[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_intersected')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            intersected = intersect(source=source, operator=operator,
                                    target=target, algorithm_option=AlgorithmOption.CLASSIC)
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
    # End test_output_zm_classic method

    @mark.zm
    @mark.large
    @mark.parametrize('fc_name', [
        'hydro_a',
        'hydro_m_a',
        'hydro_z_a',
        'hydro_zm_a',
        'structures_a',
        'structures_m_a',
        'structures_m_ma',
        'structures_m_p',
        'structures_p',
        'structures_z_a',
        'structures_z_ma',
        'structures_z_p',
        'structures_zm_a',
        'structures_zm_ma',
        'structures_zm_p',
        'topography_l',
        'topography_m_l',
        'topography_z_l',
        'topography_zm_l',
        'toponymy_m_mp',
        'toponymy_m_p',
        'toponymy_p',
        'toponymy_z_mp',
        'toponymy_z_p',
        'toponymy_zm_mp',
        'toponymy_zm_p',
        'transmission_l',
        'transmission_m_l',
        'transmission_m_ml',
        'transmission_m_mp',
        'transmission_m_p',
        'transmission_p',
        'transmission_z_l',
        'transmission_z_ml',
        'transmission_z_mp',
        'transmission_z_p',
        'transmission_zm_l',
        'transmission_zm_ml',
        'transmission_zm_mp',
        'transmission_zm_p',
    ])
    @mark.parametrize('op_name', [
        'index_a',
        'index_m_a',
        'index_z_a',
        'index_zm_a',
        'index_zm_nan_a',
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
    def test_output_zm_classic_cleaner(self, ntdb_zm, mem_gpkg, fc_name, op_name, output_z, output_m):
        """
        Test intersect using Output ZM settings and classic algorithm using cleaner inputs
        """
        operator = ntdb_zm[op_name]
        source = ntdb_zm[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_intersected')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            intersected = intersect(source=source, operator=operator,
                                    target=target, algorithm_option=AlgorithmOption.CLASSIC)
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
    # End test_output_zm_classic_cleaner method

    @mark.zm
    @mark.large
    @mark.parametrize('fc_name', [
        'hydro_a',
        'structures_a',
        'structures_m_a',
        'structures_m_ma',
        'structures_ma',
        'structures_p',
        'structures_vcs_z_a',
        'structures_vcs_z_ma',
        'structures_vcs_zm_a',
        'structures_vcs_zm_ma',
        'structures_z_a',
        'structures_z_ma',
        'structures_zm_a',
        'structures_zm_ma',
        'topography_l',
        'toponymy_mp',
        'toponymy_p',
        'toponymy_vcs_z_mp',
        'toponymy_vcs_z_p',
        'toponymy_z_mp',
        'toponymy_z_p',
        'transmission_l',
        'transmission_m_l',
        'transmission_ml',
        'transmission_p',
        'transmission_vcs_z_l',
        'transmission_vcs_z_ml',
        'transmission_vcs_zm_l',
        'transmission_z_l',
        'transmission_zm_l',
    ])
    @mark.parametrize('op_name', [
        'index_a',
        'index_m_a',
        'index_z_a',
        'index_zm_a',
        'index_zm_nan_a',
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
    def test_output_zm_pairwise(self, ntdb_zm_meh, mem_gpkg, fc_name, op_name, output_z, output_m):
        """
        Test intersect using Output ZM settings using pairwise algorithm
        """
        operator = ntdb_zm_meh[op_name]
        source = ntdb_zm_meh[fc_name]
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

    @mark.zm
    @mark.large
    @mark.parametrize('fc_name', [
        'hydro_a',
        'hydro_m_a',
        'hydro_z_a',
        'hydro_zm_a',
        'structures_a',
        'structures_m_a',
        'structures_m_ma',
        'structures_m_p',
        'structures_p',
        'structures_z_a',
        'structures_z_ma',
        'structures_z_p',
        'structures_zm_a',
        'structures_zm_ma',
        'structures_zm_p',
        'topography_l',
        'topography_m_l',
        'topography_z_l',
        'topography_zm_l',
        'toponymy_m_mp',
        'toponymy_m_p',
        'toponymy_p',
        'toponymy_z_mp',
        'toponymy_z_p',
        'toponymy_zm_mp',
        'toponymy_zm_p',
        'transmission_l',
        'transmission_m_l',
        'transmission_m_ml',
        'transmission_m_mp',
        'transmission_m_p',
        'transmission_p',
        'transmission_z_l',
        'transmission_z_ml',
        'transmission_z_mp',
        'transmission_z_p',
        'transmission_zm_l',
        'transmission_zm_ml',
        'transmission_zm_mp',
        'transmission_zm_p',
    ])
    @mark.parametrize('op_name', [
        'index_a',
        'index_m_a',
        'index_z_a',
        'index_zm_a',
        'index_zm_nan_a',
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
    def test_output_zm_pairwise_cleaner(self, ntdb_zm, mem_gpkg, fc_name, op_name, output_z, output_m):
        """
        Test intersect using Output ZM settings using pairwise algorithm using cleaner inputs
        """
        operator = ntdb_zm[op_name]
        source = ntdb_zm[fc_name]
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
    # End test_output_zm_pairwise_cleaner method

    @mark.parametrize('fc_name, xy_tolerance, option, feature_count, field_count', [
        ('admin_a', None, AttributeOption.ALL, 128, 25),
        ('airports_p', None, AttributeOption.ALL, 40, 14),
        ('roads_l', None, AttributeOption.ALL, 2560, 22),
        ('admin_mp_a', None, AttributeOption.ALL, 128, 23),
        ('airports_mp_p', None, AttributeOption.ALL, 12, 11),
        ('roads_mp_l', None, AttributeOption.ALL, 21, 11),
        ('admin_a', 0.001, AttributeOption.ALL, 125, 25),
        ('airports_p', 0.001, AttributeOption.ALL, 40, 14),
        ('roads_l', 0.001, AttributeOption.ALL, 2729, 22),
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
        ('roads_l', 0.001, AttributeOption.ONLY_FID, 2729, 4),
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
        ('roads_l', 0.001, AttributeOption.SANS_FID, 2729, 20),
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
        (0.05, 369),
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


class TestSymmetricDifference:
    """
    Tests for Symmetric Difference
    """
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
        ('hydro_a', 'hydro_a', 5215, 24),
        ('hydro_a', 'hydro_zm_a', 5215, 25),
        ('hydro_zm_a', 'hydro_zm_a', 5215, 26),
        ('structures_a', 'structures_a', 2854, 24),
        ('structures_a', 'structures_zm_a', 2854, 25),
        ('structures_zm_a', 'structures_zm_a', 2854, 26),
        ('structures_p', 'structures_p', 11512, 20),
        ('structures_p', 'structures_zm_p', 11512, 20),
        ('structures_zm_p', 'structures_zm_p', 11512, 20),
        ('toponymy_mp', 'toponymy_mp', 6, 22),
        ('toponymy_mp', 'toponymy_zm_mp', 6, 22),
        ('toponymy_zm_mp', 'toponymy_zm_mp', 6, 22),
        ('transmission_l', 'transmission_l', 135, 24),
        ('transmission_l', 'transmission_zm_l', 135, 25),
        ('transmission_zm_l', 'transmission_zm_l', 135, 26),
    ])
    @mark.parametrize('xy_tolerance', [
        None,
        0.00001,
    ])
    def test_sym_diff_setting(self, inputs, ntdb_zm, mem_gpkg, source_name, operator_name,
                              feature_count, field_count, xy_tolerance):
        """
        Test sym diff using analysis settings for XY tolerance
        """
        source = ntdb_zm[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082I13', '082O01', '082J16', '082P04')""")
        operator = ntdb_zm[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082I13', '082I12', '082I14', '082I11')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        with Swap(Setting.XY_TOLERANCE, xy_tolerance):
            result = symmetrical_difference(
                source=source, operator=operator, target=target,
                attribute_option=AttributeOption.ALL)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_sym_diff_setting method

    @mark.parametrize('source_name, operator_name, feature_count, field_count', [
        ('hydro_a', 'hydro_a', 5216, 24),
        ('hydro_a', 'hydro_zm_a', 5216, 25),
        ('hydro_zm_a', 'hydro_zm_a', 5216, 26),
        ('structures_a', 'structures_a', 2958, 24),
        ('structures_a', 'structures_zm_a', 2958, 25),
        ('structures_zm_a', 'structures_zm_a', 2958, 26),
        ('structures_p', 'structures_p', 11512, 20),
        ('structures_p', 'structures_zm_p', 11512, 20),
        ('structures_zm_p', 'structures_zm_p', 11512, 20),
        ('toponymy_mp', 'toponymy_mp', 6, 22),
        ('toponymy_mp', 'toponymy_zm_mp', 6, 22),
        ('toponymy_zm_mp', 'toponymy_zm_mp', 6, 22),
        ('transmission_l', 'transmission_l', 135, 24),
        ('transmission_l', 'transmission_zm_l', 135, 25),
        ('transmission_zm_l', 'transmission_zm_l', 135, 26),
    ])
    @mark.parametrize('xy_tolerance', [
        0.00001,
    ])
    def test_sym_diff_setting_classic(self, inputs, ntdb_zm, mem_gpkg, source_name, operator_name,
                                      feature_count, field_count, xy_tolerance):
        """
        Test sym diff using analysis settings for XY tolerance
        """
        source = ntdb_zm[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082I13', '082O01', '082J16', '082P04')""")
        operator = ntdb_zm[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082I13', '082I12', '082I14', '082I11')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        with Swap(Setting.XY_TOLERANCE, xy_tolerance):
            result = symmetrical_difference(
                source=source, operator=operator, target=target,
                attribute_option=AttributeOption.ALL, algorithm_option=AlgorithmOption.CLASSIC)
        assert len(result) == feature_count
        assert len(result.fields) == field_count
    # End test_sym_diff_setting_classic method

    @mark.zm
    @mark.large
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
        OutputZOption.SAME,
        OutputZOption.ENABLED,
        OutputZOption.DISABLED,
    ])
    @mark.parametrize('output_m', [
        OutputMOption.SAME,
        OutputMOption.ENABLED,
        OutputMOption.DISABLED,
    ])
    def test_output_zm_pairwise_cleaner(self, ntdb_zm, mem_gpkg, source_name, operator_name, output_z, output_m):
        """
        Test sym diff using Output ZM settings using pairwise algorithm using cleaner inputs
        """
        source = ntdb_zm[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082I13', '082O01')""")
        operator = ntdb_zm[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082I13', '082I12')""")
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
        result = symmetrical_difference(source=subset, operator=eraser, target=target)
        assert len(result) == 245
        assert len(result.fields) == 4
    # End test_sans_attributes method

    @mark.parametrize('source_name, operator_name, option, field_count', [
        ('hydro_a', 'hydro_a', AttributeOption.SANS_FID, 22),
        ('structures_a', 'structures_a', AttributeOption.SANS_FID, 22),
        ('structures_p', 'structures_p', AttributeOption.SANS_FID, 18),
        ('toponymy_mp', 'toponymy_mp', AttributeOption.SANS_FID, 20),
        ('transmission_l', 'transmission_l', AttributeOption.SANS_FID, 22),
        ('hydro_a', 'hydro_a', AttributeOption.ONLY_FID, 4),
        ('structures_a', 'structures_a', AttributeOption.ONLY_FID, 4),
        ('structures_p', 'structures_p', AttributeOption.ONLY_FID, 4),
        ('toponymy_mp', 'toponymy_mp', AttributeOption.ONLY_FID, 4),
        ('transmission_l', 'transmission_l', AttributeOption.ONLY_FID, 4),
    ])
    def test_sym_diff_attribute_option(self, inputs, ntdb_zm, mem_gpkg, source_name, operator_name, option, field_count):
        """
        Test sym diff using analysis settings for XY tolerance
        and varying attribute option
        """
        source = ntdb_zm[source_name].copy(
            name=f'{source_name}_source', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082I13', '082O01')""")
        operator = ntdb_zm[operator_name].copy(
            name=f'{operator_name}_operator', geopackage=mem_gpkg,
            where_clause="""DATANAME IN ('082I13', '082I12')""")
        target = FeatureClass(geopackage=mem_gpkg, name=f'{source_name}_{operator_name}')
        result = symmetrical_difference(
            source=source, operator=operator, target=target,
            attribute_option=option)
        assert len(result.fields) == field_count
    # End test_sym_diff_attribute_option method

    @mark.zm
    @mark.large
    @mark.parametrize('fc_name, count, where_clause', [
        ('hydro_a', 2356, """DATANAME = '082O08'"""),
        ('hydro_m_a', 2356, """DATANAME = '082O08'"""),
        ('hydro_z_a', 2356, """DATANAME = '082O08'"""),
        ('hydro_zm_a', 2356, """DATANAME = '082O08'"""),
        ('structures_a', 52, """DATANAME = '082O08'"""),
        ('structures_m_a', 52, """DATANAME = '082O08'"""),
        ('structures_z_a', 52, """DATANAME = '082O08'"""),
        ('structures_zm_a', 52, """DATANAME = '082O08'"""),
        ('structures_m_ma', 5, """CODE = 2010082"""),
        ('structures_z_ma', 5, """CODE = 2010082"""),
        ('structures_zm_ma', 5, """CODE = 2010082"""),
    ])
    @mark.parametrize('op_name', [
        'index_a',
        'index_m_a',
        'index_z_a',
        'index_zm_a',
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
    def test_target_full_disjoint_pairwise(self, ntdb_zm, mem_gpkg, fc_name,
                                           count, where_clause, op_name,
                                           output_z, output_m):
        """
        Test target full, exercising process disjoint and handling
        different ZM dimensions
        """
        option = AttributeOption.ALL
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = copy_element(
            ntdb_zm[fc_name], target=FeatureClass(mem_gpkg, fc_name),
            where_clause=where_clause)
        source.add_spatial_index()
        operator = copy_element(
            ntdb_zm[op_name], target=FeatureClass(mem_gpkg, op_name),
            where_clause="""DATANAME = '082J10'""")
        operator.add_spatial_index()
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            result = symmetrical_difference(
                source=source, operator=operator,
                target=target, attribute_option=option)
        if output_z == OutputZOption.SAME:
            has_z = source.has_z or operator.has_z
        else:
            has_z = output_z == OutputZOption.ENABLED
        if output_m == OutputZOption.SAME:
            has_m = source.has_m or operator.has_m
        else:
            has_m = output_m == OutputMOption.ENABLED
        assert result.has_z == has_z
        assert result.has_m == has_m
        assert result.count == count
    # End test_target_full_disjoint_pairwise method

    @mark.zm
    @mark.large
    @mark.parametrize('fc_name, count, where_clause', [
        ('hydro_a', 2356, """DATANAME = '082O08'"""),
        ('hydro_m_a', 2356, """DATANAME = '082O08'"""),
        ('hydro_z_a', 2356, """DATANAME = '082O08'"""),
        ('hydro_zm_a', 2356, """DATANAME = '082O08'"""),
        ('structures_a', 52, """DATANAME = '082O08'"""),
        ('structures_m_a', 52, """DATANAME = '082O08'"""),
        ('structures_z_a', 52, """DATANAME = '082O08'"""),
        ('structures_zm_a', 52, """DATANAME = '082O08'"""),
        ('structures_m_ma', 11, """CODE = 2010082"""),
        ('structures_z_ma', 11, """CODE = 2010082"""),
        ('structures_zm_ma', 11, """CODE = 2010082"""),
    ])
    @mark.parametrize('op_name', [
        'index_a',
        'index_m_a',
        'index_z_a',
        'index_zm_a',
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
    def test_target_full_disjoint_classic(self, ntdb_zm, mem_gpkg, fc_name,
                                          count, where_clause, op_name,
                                          output_z, output_m):
        """
        Test target full, exercising process disjoint and handling
        different ZM dimensions
        """
        option = AttributeOption.ALL
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = copy_element(
            ntdb_zm[fc_name], target=FeatureClass(mem_gpkg, fc_name),
            where_clause=where_clause)
        source.add_spatial_index()
        operator = copy_element(
            ntdb_zm[op_name], target=FeatureClass(mem_gpkg, op_name),
            where_clause="""DATANAME = '082J10'""")
        operator.add_spatial_index()
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            result = symmetrical_difference(
                source=source, operator=operator,
                algorithm_option=AlgorithmOption.CLASSIC,
                target=target, attribute_option=option)
        if output_z == OutputZOption.SAME:
            has_z = source.has_z or operator.has_z
        else:
            has_z = output_z == OutputZOption.ENABLED
        if output_m == OutputZOption.SAME:
            has_m = source.has_m or operator.has_m
        else:
            has_m = output_m == OutputMOption.ENABLED
        assert result.has_z == has_z
        assert result.has_m == has_m
        assert result.count == count
    # End test_target_full_disjoint_classic method
# End TestSymmetricDifference class


if __name__ == '__main__':  # pragma: no cover
    pass
