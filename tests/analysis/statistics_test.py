# -*- coding: utf-8 -*-
"""
Tests for Statistics
"""


from fudgeo import Table

from conftest import world_features
from spyops.analysis import statistics
from spyops.analysis.statistics import frequency
from spyops.shared.stats import First, Min, Mode


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


if __name__ == '__main__':  # pragma: no cover
    pass
