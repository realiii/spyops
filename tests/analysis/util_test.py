# -*- coding: utf-8 -*-
"""
Tests for Analysis utilities
"""


from fudgeo import FeatureClass
from pytest import mark

from spyops.analysis.util import (
    _add_geometry_attribute_fields, _combine_inputs, _summarize_by_feature)
from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.shared.enumeration import AlgorithmOption, AttributeOption
from spyops.shared.field import validate_fields
from spyops.shared.keywords import NAME_ATTR
from spyops.shared.stats import Least, Most, Sum


pytestmark = [mark.utility, mark.analysis]


class TestAddGeometryAttributeFields:
    """
    Test Add Geometry Attribute Fields
    """
    @mark.parametrize('fc_name, expected', [
        ('hydro_a', (None, 'LENGTH', 'AREA')),
        ('structures_6654_zm_ma', (None, 'LENGTH', 'AREA')),
        ('transmission_l', (None, 'LENGTH', None)),
        ('transmission_6654_z_ml', (None, 'LENGTH', None)),
        ('toponymy_p', ('POINT_COUNT', None, None)),
        ('toponymy_zm_mp', ('POINT_COUNT', None, None)),
    ])
    def test_geometry_types(self, ntdb_zm_small, mem_gpkg, fc_name, expected):
        """
        Test geometry types
        """
        fc = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        fields = _add_geometry_attribute_fields(
            fc, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        names = [getattr(f, NAME_ATTR, f) for f in fields]
        assert names == list(expected)
    # End test_geometry_types method

    @mark.parametrize('fc_name, expected', [
        ('hydro_a', (None, 'LENGTH_1', 'AREA_1')),
        ('structures_6654_zm_ma', (None, 'LENGTH_1', 'AREA_1')),
        ('transmission_l', (None, 'LENGTH_1', None)),
        ('transmission_6654_z_ml', (None, 'LENGTH_1', None)),
        ('toponymy_p', ('POINT_COUNT_1', None, None)),
        ('toponymy_zm_mp', ('POINT_COUNT_1', None, None)),
    ])
    def test_geometry_types_existing(self, ntdb_zm_small, mem_gpkg, fc_name, expected):
        """
        Test geometry types where the fields already exist
        """
        fc = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        _add_geometry_attribute_fields(
            fc, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        fields = _add_geometry_attribute_fields(
            fc, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        names = [getattr(f, NAME_ATTR, f) for f in fields]
        assert names == list(expected)
    # End test_geometry_types_existing method
# End TestAddGeometryAttributeFields class


class TestSummarizeByFeature:
    """
    Test Summarize by Feature
    """
    @mark.parametrize('src_name, op_name, stats_field_names, count, expected', [
        ('grid_a', 'hydro_a', ['CODE', 'ACCURACY'], 8,
         ['fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
          'MOST_COMMON_CODE', 'SUM_CODE', 'SUM_ACCURACY', 'LENGTH', 'AREA']),
        ('grid_a', 'hydro_a', [], 8,
         ['fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
          'MOST_COMMON_CODE', 'LENGTH', 'AREA']),
        ('grid_a', 'structures_p', ['CODE', 'ACCURACY'], 8,
         ['fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
          'MOST_COMMON_CODE', 'SUM_CODE', 'SUM_ACCURACY', 'POINT_COUNT']),
        ('grid_a', 'structures_p', [], 8,
         ['fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
          'MOST_COMMON_CODE', 'POINT_COUNT']),
        ('grid_a', 'transmission_l', ['CODE', 'ACCURACY'], 8,
         ['fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
          'MOST_COMMON_CODE', 'SUM_CODE', 'SUM_ACCURACY', 'LENGTH']),
        ('grid_a', 'transmission_l', [], 8,
         ['fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
          'MOST_COMMON_CODE', 'LENGTH']),
    ])
    def test_with_class_field(self, grid_index, ntdb_zm_small, mem_gpkg,
                              src_name, op_name, stats_field_names, count, expected):
        """
        Test with class field
        """
        source = grid_index[src_name]
        operator = ntdb_zm_small[op_name]
        class_field, = validate_fields(operator, fields=['CODE'])
        stats_fields = [Sum(f) for f in validate_fields(operator, fields=stats_field_names)]
        least_most = Least(class_field), Most(class_field)
        target = FeatureClass(name='target', geopackage=mem_gpkg)
        intermediate, *geom_fields = _combine_inputs(
            scratch=mem_gpkg, attribute_option=AttributeOption.ALL,
            source=source, operator=operator, target=target,
            algorithm_option=AlgorithmOption.PAIRWISE,
            length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS, xy_tolerance=None)
        summary, group_field = _summarize_by_feature(
            scratch=mem_gpkg, source=source, operator=operator,
            intermediate=intermediate, geom_fields=geom_fields,
            least_most=least_most, stats_fields=stats_fields)
        assert len(summary) == count
        assert summary.field_names == expected
        assert group_field.name == 'fid_grid_a'
    # End test_with_class_field method

    def test_least_most_overlap(self, grid_index, ntdb_zm_small, mem_gpkg):
        """
        Test least most overlap with class field least most
        """
        source = grid_index['grid_a']
        operator = ntdb_zm_small['hydro_a']
        class_field, = validate_fields(operator, fields=['CODE'])
        stats_fields = least_most = Least(class_field), Most(class_field)
        target = FeatureClass(name='target', geopackage=mem_gpkg)
        intermediate, *geom_fields = _combine_inputs(
            scratch=mem_gpkg, attribute_option=AttributeOption.ALL,
            source=source, operator=operator, target=target,
            algorithm_option=AlgorithmOption.PAIRWISE,
            length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS, xy_tolerance=None)
        summary, group_field = _summarize_by_feature(
            scratch=mem_gpkg, source=source, operator=operator,
            intermediate=intermediate, geom_fields=geom_fields,
            least_most=least_most, stats_fields=stats_fields)
        assert len(summary) == 8
        assert summary.field_names == [
            'fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
            'MOST_COMMON_CODE', 'LENGTH', 'AREA']
        assert group_field.name == 'fid_grid_a'
    # End test_with_class_field method
# End TestSummarizeByFeature class


if __name__ == '__main__':  # pragma: no cover
    pass
