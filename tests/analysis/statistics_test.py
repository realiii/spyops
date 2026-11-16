# -*- coding: utf-8 -*-
"""
Tests for Statistics
"""


from fudgeo import Table
from pytest import mark

from conftest import world_features
from spyops.analysis import statistics, frequency, tabulate_intersection
from spyops.shared.stats import First, Max, Min, Mode


pytestmark = [mark.statistics, mark.analysis]


class TestStatistics:
    """
    Test Statistics
    """
    def test_table_sans_grouping(self, world_tables, mem_gpkg):
        """
        Test table without grouping
        """
        source = world_tables['admin']
        target = Table(geopackage=mem_gpkg, name='stats')
        result = statistics(source, target=target, stats_fields=First('COUNTRY'))
        assert len(result) == 1
        assert result.field_names[1:] == ['FIRST_COUNTRY']
    # End test_table_sans_grouping method

    def test_table_with_grouping(self, world_tables, mem_gpkg):
        """
        Test table with grouping
        """
        source = world_tables['admin']
        target = Table(geopackage=mem_gpkg, name='stats')
        result = statistics(
            source, target=target,
            stats_fields=[Min('Disputed'), Mode('LAND_RANK')],
            group_fields=('COUNTRY', 'ISO_CC', 'ADMINTYPE')
        )
        assert len(result) == 376
        assert result.field_names[1:] == [
            'COUNTRY', 'ISO_CC', 'ADMINTYPE', 'MIN_DISPUTED', 'MODE_LAND_RANK']
    # End test_table_with_grouping method

    def test_feature_class_sans_grouping(self, world_features, mem_gpkg):
        """
        Test feature class without grouping
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='stats')
        result = statistics(source, target=target, stats_fields=First('COUNTRY'))
        assert len(result) == 1
        assert result.field_names[1:] == ['FIRST_COUNTRY']
    # End test_feature_class_sans_grouping method

    def test_feature_class_with_grouping(self, world_features, mem_gpkg):
        """
        Test feature class with grouping
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='stats')
        result = statistics(
            source, target=target,
            stats_fields=[Min('Disputed'), Mode('LAND_RANK')],
            group_fields=('COUNTRY', 'ISO_CC', 'ADMINTYPE')
        )
        assert len(result) == 376
        assert result.field_names[1:] == [
            'COUNTRY', 'ISO_CC', 'ADMINTYPE', 'MIN_DISPUTED', 'MODE_LAND_RANK']
    # End test_feature_class_with_grouping method
# End TestStatistics class


class TestFrequency:
    """
    Test Frequency
    """
    def test_table_sans_statistics(self, world_tables, mem_gpkg):
        """
        Test table without statistics
        """
        source = world_tables['admin']
        target = Table(geopackage=mem_gpkg, name='freq')
        result = frequency(source, target=target, group_fields='COUNTRY')
        assert len(result) == 251
        assert result.field_names[1:] == ['COUNTRY', 'FREQUENCY']
    # End test_table_sans_statistics method

    def test_table_with_statistics(self, world_tables, mem_gpkg):
        """
        Test table with statistics
        """
        source = world_tables['admin']
        target = Table(geopackage=mem_gpkg, name='freq')
        result = frequency(
            source, target=target,
            stats_fields=[Min('Disputed'), Mode('LAND_RANK')],
            group_fields=('COUNTRY', 'ISO_CC', 'ADMINTYPE')
        )
        assert len(result) == 376
        assert result.field_names[1:] == [
            'COUNTRY', 'ISO_CC', 'ADMINTYPE', 'FREQUENCY', 'MIN_DISPUTED', 'MODE_LAND_RANK']
    # End test_table_with_statistics method

    def test_feature_class_sans_statistics(self, world_features, mem_gpkg):
        """
        Test feature class without statistics
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='freq')
        result = frequency(source, target=target, group_fields='COUNTRY')
        assert len(result) == 251
        assert result.field_names[1:] == ['COUNTRY', 'FREQUENCY']
    # End test_feature_class_sans_statistics method

    def test_feature_class_with_grouping(self, world_features, mem_gpkg):
        """
        Test feature class with grouping
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='stats')
        result = frequency(
            source, target=target,
            stats_fields=[Min('Disputed'), Mode('LAND_RANK')],
            group_fields=('COUNTRY', 'ISO_CC', 'ADMINTYPE')
        )
        assert len(result) == 376
        assert result.field_names[1:] == [
            'COUNTRY', 'ISO_CC', 'ADMINTYPE', 'FREQUENCY', 'MIN_DISPUTED', 'MODE_LAND_RANK']
    # End test_feature_class_with_grouping method
# End TestFrequency class


class TestTabulateIntersection:
    """
    Test Tabulate Intersection
    """
    @mark.parametrize('src_name, op_name, group_names, class_names, stats, expected_count, expected_field_names', [
        ('grid_lcc_a', 'hydro_6654_a', ['DATANAME'], ['CODE'], [], 6,
         ['fid', 'DATANAME', 'CODE', 'LENGTH', 'AREA']),
        ('grid_lcc_a', 'hydro_6654_a', ['DATANAME'], ['CODE'], [Min('ACCURACY'), Max('ACCURACY')], 6,
         ['fid', 'DATANAME', 'CODE', 'MIN_ACCURACY', 'MAX_ACCURACY', 'LENGTH', 'AREA']),
        ('grid_lcc_a', 'structures_p', ['DATANAME'], ['CODE'], [Min('ACCURACY'), Max('ACCURACY')], 14,
         ['fid', 'DATANAME', 'CODE', 'MIN_ACCURACY', 'MAX_ACCURACY', 'POINT_COUNT']),
        ('grid_lcc_a', 'transmission_10tm_l', ['DATANAME'], ['CODE'], [Min('ACCURACY'), Max('ACCURACY')], 4,
         ['fid', 'DATANAME', 'CODE', 'MIN_ACCURACY', 'MAX_ACCURACY', 'LENGTH']),
        ('grid_lcc_a', 'hydro_6654_a', ['DATANAME'], ['ENTITY_NAME', 'CODE'], [Min('ACCURACY'), Max('ACCURACY')], 6,
         ['fid', 'DATANAME', 'ENTITY_NAME', 'CODE', 'MIN_ACCURACY', 'MAX_ACCURACY', 'LENGTH', 'AREA']),
        ('grid_lcc_a', 'structures_p', ['DATANAME'], ['ENTITY_NAME', 'CODE'], [Min('ACCURACY'), Max('ACCURACY')], 14,
         ['fid', 'DATANAME', 'ENTITY_NAME', 'CODE', 'MIN_ACCURACY', 'MAX_ACCURACY', 'POINT_COUNT']),
        ('grid_lcc_a', 'transmission_10tm_l', ['DATANAME'], ['ENTITY_NAME', 'CODE'], [Min('ACCURACY'), Max('ACCURACY')], 4,
         ['fid', 'DATANAME', 'ENTITY_NAME', 'CODE', 'MIN_ACCURACY', 'MAX_ACCURACY', 'LENGTH']),
        ('grid_lcc_a', 'hydro_6654_a', ['row_index', 'col_index'], ['CODE'], [Min('ACCURACY'), Max('ACCURACY')], 29,
         ['fid', 'row_index', 'col_index', 'CODE', 'MIN_ACCURACY', 'MAX_ACCURACY', 'LENGTH', 'AREA']),
        ('grid_lcc_a', 'hydro_6654_a', ['row_index', 'col_index'], ['ENTITY_NAME', 'CODE'], [Min('ACCURACY'), Max('ACCURACY')], 29,
         ['fid', 'row_index', 'col_index', 'ENTITY_NAME', 'CODE', 'MIN_ACCURACY', 'MAX_ACCURACY', 'LENGTH', 'AREA']),
        ('grid_lcc_a', 'structures_p', ['row_index', 'col_index'], ['ENTITY_NAME', 'CODE'], [Min('ACCURACY'), Max('ACCURACY')], 46,
         ['fid', 'row_index', 'col_index', 'ENTITY_NAME', 'CODE', 'MIN_ACCURACY', 'MAX_ACCURACY', 'POINT_COUNT']),
        ('grid_lcc_a', 'transmission_10tm_l', ['row_index', 'col_index'], ['ENTITY_NAME', 'CODE'], [Min('ACCURACY'), Max('ACCURACY')], 20,
         ['fid', 'row_index', 'col_index', 'ENTITY_NAME', 'CODE', 'MIN_ACCURACY', 'MAX_ACCURACY', 'LENGTH']),
    ])
    def test_tabulate_intersection(self, grid_index, ntdb_zm_small, mem_gpkg,
                                   src_name, op_name, group_names, class_names,
                                   stats, expected_count, expected_field_names):
        """
        Test tabulate intersection
        """
        source = grid_index[src_name]
        operator = ntdb_zm_small[op_name]
        target = Table(mem_gpkg, name='ti_results')
        tbl = tabulate_intersection(
            source, operator=operator, target=target,
            group_fields=group_names, class_fields=class_names,
            stats_fields=stats)
        assert len(tbl) == expected_count
        assert tbl.field_names == expected_field_names
    # End test_tabulate_intersection method
# End TestTabulateIntersection class


if __name__ == '__main__':  # pragma: no cover
    pass
