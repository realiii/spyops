# -*- coding: utf-8 -*-
"""
Tests for Delimited File Conversion Classes
"""


from fudgeo import Field
from fudgeo.enumeration import FieldType
from pytest import mark

from spyops.crs.constant import WGS84
from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.query.conversion.delimited import QueryTableToDelimitedFile
from spyops.shared.constant import COMMA, PIPE
from spyops.shared.sort import Ascending, Descending


pytestmark = [mark.conversion, mark.delimited, mark.query]


class TestQueryTableToDelimitedFile:
    """
    Test Query Table to Delimited File
    """
    def test_select(self, ntdb_zm_small):
        """
        Test select with extent, where clause, adn sort fields
        """
        source = ntdb_zm_small['hydro_6654_zm_a']
        with Swap(Setting.EXTENT, Extent.from_bounds(
                -114.28, 51.125, -114.21, 51.185, crs=WGS84)):
            where = 'fid > 1'
            query = QueryTableToDelimitedFile(
                source, where_clause=where,
                sort_fields=(Ascending(Field('ENTITY_NAME', data_type=FieldType.text)),
                             Descending(Field('CODE', data_type=FieldType.text))))
            sql = query.select
            assert 'minx' in sql
            assert where in sql
            assert 'ORDER BY ENTITY_NAME ASC, CODE DESC' in sql
    # End test_select method

    def test_field_names_and_count(self, ntdb_zm_small):
        """
        Test field names and count
        """
        source = ntdb_zm_small['hydro_6654_zm_a']
        query = QueryTableToDelimitedFile(source)
        count, insert_names, select_names = query._field_names_and_count(source)
        assert count == 12
        assert insert_names == ''
        assert select_names == (
            'fid, FEATURE_ID, PART_ID, OBJECTID_1, ENTITY, '
            'ENTITY_NAME, VALDATE, PROVIDER, DATANAME, ACCURACY, '
            'FILE_NAME, CODE')
    # End test_field_names_and_count method

    def test_spatial_reference_system(self, ntdb_zm_small):
        """
        Test spatial reference system
        """
        source = ntdb_zm_small['hydro_6654_zm_a']
        query = QueryTableToDelimitedFile(source, use_aliases=True)
        srs = query.spatial_reference_system
        assert srs is not None
        assert query.spatial_reference_system.srs_id == 6654
    # End test_spatial_reference_system method

    @mark.parametrize('delimiter, expected', [
        (None, COMMA),
        (',\n', COMMA),
        (' ; ', ';'),
        ('\t', '\t'),
        ('\n', COMMA),
        ('|', PIPE),
    ])
    def test_get_dialect(self, ntdb_zm_small, delimiter, expected):
        """
        Test get dialect
        """
        source = ntdb_zm_small['hydro_6654_zm_a']
        query = QueryTableToDelimitedFile(source, delimiter=delimiter)
        excel = query._get_dialect()
        assert excel.delimiter == expected
    # End test_spatial_reference_system method

    @mark.parametrize('use_aliases, expected', [
        (True, ('fid', 'OBJECTID', 'CITY_NAME', 'CITY_CODE', 'CENTROID_X', 'CENTROID_Y', 'X Coordinate', 'Y Coordinate')),
        (False, ('fid', 'OBJECTID', 'CITY_NAME', 'CITY_CODE', 'CENTROID_X', 'CENTROID_Y', 'POINT_X', 'POINT_Y')),
    ])
    def test_get_attribute_names(self, inputs, use_aliases, expected):
        """
        Test get attribute names
        """
        source = inputs['yyc_a']
        query = QueryTableToDelimitedFile(source, use_aliases=use_aliases)
        assert query._get_attribute_names() == expected
    # End test_get_attribute_names method
# End TestQueryTableToDelimitedFile class


if __name__ == '__main__':  # pragma: no cover
    pass
