# -*- coding: utf-8 -*-
"""
Test for Statistics Query classes
"""


from fudgeo import Field, Table

from spyops.query.analysis.statistics import QueryFrequency, QueryStatistics
from spyops.shared.stats import First, Max


class TestQueryStatistics:
    """
    Test Query Statistics
    """
    def test_field_names_and_count_sans_group(self, world_features, mem_gpkg):
        """
        Test field names and count no grouping
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='stats_a')
        stats = First(Field('NAME', data_type='TEXT'))
        query = QueryStatistics(
            source, target=target, statistics=[stats], fields=[],
            where_clause='')
        count, insert_names, _ = query._field_names_and_count(source)
        assert count == 1
        assert insert_names == 'FIRST_NAME'
        sql = query.select
        assert 'SELECT spyops_first(NAME)' in sql
        assert 'GROUP BY' not in sql
    # End test_field_names_and_count_sans_group method

    def test_field_names_and_count_with_group(self, world_features, mem_gpkg):
        """
        Test field names and count with grouping
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='stats_a')
        stats = First(Field('LAND_TYPE', data_type='TEXT')), Max(Field('LAND_RANK', data_type='REAL'))
        query = QueryStatistics(
            source, target=target, statistics=stats,
            fields=[Field('COUNTRY', data_type='TEXT')],
            where_clause='')
        count, insert_names, _ = query._field_names_and_count(source)
        assert count == 3
        assert insert_names == 'COUNTRY, FIRST_LAND_TYPE, MAX_LAND_RANK'
        sql = query.select
        assert 'SELECT COUNTRY, spyops_first(LAND_TYPE), MAX(LAND_RANK)' in sql
        assert 'GROUP BY COUNTRY' in sql
    # End test_field_names_and_count_with_group method
# End TestQueryStatistics class


class TestQueryFrequency:
    """
    Test Query Frequency
    """
    def test_field_names_and_count_sans_stats(self, world_features, mem_gpkg):
        """
        Test field names and count no statistics
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='stats_a')
        field = Field('NAME', data_type='TEXT')
        query = QueryFrequency(
            source, target=target, statistics=[], fields=[field],
            where_clause='')
        count, insert_names, select_names = query._field_names_and_count(source)
        assert count == 2
        assert select_names == 'NAME, COUNT(ROWID)'
        assert insert_names == 'NAME, FREQUENCY'
        sql = query.select
        assert 'SELECT NAME, COUNT(ROWID)' in sql
        assert 'GROUP BY' in sql
    # End test_field_names_and_count_sans_group method

    def test_field_names_and_count_with_stats(self, world_features, mem_gpkg):
        """
        Test field names and count with statistics
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='stats_a')
        fields = Field('COUNTRY', data_type='TEXT'), Field('LAND_TYPE', data_type='TEXT'), Field('LAND_RANK', data_type='REAL')
        stats = First(Field('LAND_TYPE', data_type='TEXT')), Max(Field('LAND_RANK', data_type='REAL'))
        query = QueryFrequency(
            source, target=target, statistics=stats, fields=fields, where_clause='')
        count, insert_names, select_names = query._field_names_and_count(source)
        assert count == 6
        assert insert_names == 'COUNTRY, LAND_TYPE, LAND_RANK, FREQUENCY, FIRST_LAND_TYPE, MAX_LAND_RANK'
        assert select_names == 'COUNTRY, LAND_TYPE, LAND_RANK, COUNT(ROWID), spyops_first(LAND_TYPE), MAX(LAND_RANK)'
        sql = query.select
        assert 'SELECT COUNTRY, LAND_TYPE, LAND_RANK, COUNT(ROWID)' in sql
        assert 'GROUP BY COUNTRY' in sql
    # End test_field_names_and_count_with_group method
# End TestQueryFrequency class


if __name__ == '__main__':  # pragma: no cover
    pass
