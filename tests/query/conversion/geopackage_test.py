# -*- coding: utf-8 -*-
"""
Tests for Geopackage Conversion Classes
"""


from fudgeo import Field
from pytest import mark

from spyops.environment import Setting
from spyops.environment.context import Swap
from spyops.query.conversion.geopackage import (
    QueryExportTable,
    QueryTableToGeoPackage)
from spyops.shared.sort import Ascending

pytestmark = [mark.conversion, mark.geopackage, mark.query]


class TestQueryTableToGeoPackage:
    """
    Test Query Table to GeoPackage
    """
    @mark.parametrize('overwrite, expected', [
        (True, 'hydro_zm_a'),
        (False, 'hydro_zm_a_1'),
    ])
    def test_make_target(self, ntdb_zm_small, overwrite, expected):
        """
        Test make target
        """
        source = ntdb_zm_small['hydro_zm_a']
        with Swap(Setting.OVERWRITE, overwrite):
            target = QueryTableToGeoPackage._make_target(source, ntdb_zm_small)
            assert target.name == expected
    # End test_make_target method
# End TestQueryTableToGeoPackage class


class TestQueryExportTable:
    """
    Test Query Export Table
    """
    def test_sort_fields(self, world_tables):
        """
        Test sort fields
        """
        source = world_tables['admin']
        query = QueryExportTable(
            source, target=None, where_clause='', sort_fields=[])
        assert 'ORDER BY' not in query.select
        query = QueryExportTable(
            source, target=None, where_clause='',
            sort_fields=[Ascending(Field('ISO_CODE', data_type='TEXT(10)'))])
        assert 'ORDER BY ISO_CODE ASC' in query.select
    # End test_sort_fields method
# End TestQueryExportTable class


if __name__ == '__main__':  # pragma: no cover
    pass
