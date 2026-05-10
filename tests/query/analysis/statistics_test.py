# -*- coding: utf-8 -*-
"""
Test for Statistics Query classes
"""


from fudgeo import Field, Table

from spyops.query.analysis.statistics import QueryStatistics
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
        count, select_names, _ = query._field_names_and_count(source)
        assert count == 1
        assert select_names == 'FIRST_NAME'
        sql = query.select
        assert 'SELECT spyops_first(NAME)' in sql
        assert 'GROUP BY' not in sql
    # End test_field_names_and_count_sans_group method

    def test_field_names_and_count_with_group(self, world_features, mem_gpkg):
        """
        Test field names and count no grouping
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='stats_a')
        stats = First(Field('LAND_TYPE', data_type='TEXT')), Max(Field('LAND_RANK', data_type='REAL'))
        query = QueryStatistics(
            source, target=target, statistics=stats,
            fields=[Field('COUNTRY', data_type='TEXT')],
            where_clause='')
        count, select_names, _ = query._field_names_and_count(source)
        assert count == 3
        assert select_names == 'COUNTRY, FIRST_LAND_TYPE, MAX_LAND_RANK'
        sql = query.select
        assert 'SELECT COUNTRY, spyops_first(LAND_TYPE), MAX(LAND_RANK)' in sql
        assert 'GROUP BY COUNTRY' in sql
    # End test_field_names_and_count_with_group method
# End TestQueryStatistics class


if __name__ == '__main__':  # pragma: no cover
    pass
