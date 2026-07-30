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
from spyops.query.conversion.delimited import (
    QueryDelimitedFileToTable, QueryTableToDelimitedFile)
from spyops.query.conversion.util import _get_dialect
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
    def test_get_dialect(self, delimiter, expected):
        """
        Test get dialect
        """
        excel = _get_dialect(delimiter)
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


class TestQueryDelimitedFileToTable:
    """
    Test Query Delimited File to Table
    """
    @mark.parametrize('name, delimiter, expected', [
        ('badname.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('FIELD', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('FIELD_123456', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('comma.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('empty_columns.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.text),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('good.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('header_data_mismatch.csv', COMMA, [
            Field('FIELD', data_type=FieldType.text),
            Field('MD', data_type=FieldType.real),
            Field('FIELD_INCL', data_type=FieldType.real),
            Field('FIELD_AZIM', data_type=FieldType.real),
            Field('TVD', data_type=FieldType.real),
            Field('DOGLEG', data_type=FieldType.real),
            Field('FIELD_V_SECT', data_type=FieldType.real),
            Field('FIELD_N_S', data_type=FieldType.real),
            Field('FIELD_E_W', data_type=FieldType.real),
        ]),
        ('keywords.csv', COMMA, [
            Field('FIELD_INDEX', data_type=FieldType.real),
            Field('FIELD_INNER', data_type=FieldType.real),
            Field('FIELD_OUTER', data_type=FieldType.real),
            Field('FIELD_SELECT', data_type=FieldType.real),
            Field('FIELD_UNION', data_type=FieldType.text),
            Field('FIELD_JOIN', data_type=FieldType.text),
            Field('FIELD_ON', data_type=FieldType.text),
            Field('FIELD_ALL', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('lower.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('missingdata.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('missingheader.csv', COMMA, [
            Field('FIELD_95_56526357', data_type=FieldType.real),
            Field('FIELD_49_24522535', data_type=FieldType.real),
            Field('FIELD_1', data_type=FieldType.real),
            Field('FIELD_1', data_type=FieldType.real),
            Field('HEIGHTS', data_type=FieldType.text),
            Field('S', data_type=FieldType.text),
            Field('FIELD_HOME_ROW', data_type=FieldType.text),
            Field('FIELD_7', data_type=FieldType.real),
            Field('FIELD_2_23_23_8_07', data_type=FieldType.text),
        ]),
        ('missingname.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('FIELD', data_type=FieldType.text),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('FIELD', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('nodata.csv', COMMA, []),
        ('null.csv', COMMA, [
            Field('FIELD', data_type=FieldType.text),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('FIELD', data_type=FieldType.text),
            Field('FIELD', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('null_as_string.csv', COMMA, [
            Field('FIELD', data_type=FieldType.text),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('FIELD', data_type=FieldType.real),
            Field('FIELD', data_type=FieldType.real),
            Field('TYPE', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('pipe.csv', PIPE, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('poly.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('repeated_column.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.real),
            Field('COMMENT', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
    ])
    def test_get_fields_from_source(self, csv_path, name, delimiter, expected):
        """
        Test get fields from source
        """
        path = csv_path.joinpath(name)
        assert path.is_file()
        query = QueryDelimitedFileToTable(
            path, target=None, delimiter=delimiter)
        fields = query._get_fields_from_source()
        assert fields == expected
    # End test_get_fields_from_source method

    @mark.parametrize('name, delimiter, expected', [
        ('badname.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('FIELD', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('FIELD_123456', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('comma.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('empty_columns.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.text),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('good.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('header_data_mismatch.csv', COMMA, [
            Field('FIELD', data_type=FieldType.text),
            Field('MD', data_type=FieldType.real),
            Field('FIELD_INCL', data_type=FieldType.real),
            Field('FIELD_AZIM', data_type=FieldType.real),
            Field('TVD', data_type=FieldType.real),
            Field('DOGLEG', data_type=FieldType.real),
            Field('FIELD_V_SECT', data_type=FieldType.real),
            Field('FIELD_N_S', data_type=FieldType.real),
            Field('FIELD_E_W', data_type=FieldType.real),
        ]),
        ('keywords.csv', COMMA, [
            Field('FIELD_INDEX', data_type=FieldType.real),
            Field('FIELD_INNER', data_type=FieldType.real),
            Field('FIELD_OUTER', data_type=FieldType.real),
            Field('FIELD_SELECT', data_type=FieldType.real),
            Field('FIELD_UNION', data_type=FieldType.text),
            Field('FIELD_JOIN', data_type=FieldType.text),
            Field('FIELD_ON', data_type=FieldType.text),
            Field('FIELD_ALL', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('lower.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('missingdata.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('missingheader.csv', COMMA, [
            Field('FIELD_95_56526357', data_type=FieldType.real),
            Field('FIELD_49_24522535', data_type=FieldType.real),
            Field('FIELD_1', data_type=FieldType.real),
            Field('FIELD_1_1', data_type=FieldType.real),
            Field('HEIGHTS', data_type=FieldType.text),
            Field('S', data_type=FieldType.text),
            Field('FIELD_HOME_ROW', data_type=FieldType.text),
            Field('FIELD_7', data_type=FieldType.real),
            Field('FIELD_2_23_23_8_07', data_type=FieldType.text),
        ]),
        ('missingname.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('FIELD', data_type=FieldType.text),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('FIELD_1', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('nodata.csv', COMMA, []),
        ('null.csv', COMMA, [
            Field('FIELD', data_type=FieldType.text),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('FIELD_1', data_type=FieldType.text),
            Field('FIELD_2', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('null_as_string.csv', COMMA, [
            Field('FIELD', data_type=FieldType.text),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('FIELD_1', data_type=FieldType.real),
            Field('FIELD_2', data_type=FieldType.real),
            Field('TYPE', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('pipe.csv', PIPE, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('poly.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.text),
            Field('COMMENT', data_type=FieldType.text),
            Field('ID', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
        ('repeated_column.csv', COMMA, [
            Field('X', data_type=FieldType.real),
            Field('Y', data_type=FieldType.real),
            Field('Z', data_type=FieldType.real),
            Field('M', data_type=FieldType.real),
            Field('NAME', data_type=FieldType.text),
            Field('TYPE', data_type=FieldType.real),
            Field('COMMENT', data_type=FieldType.text),
            Field('TYPE_1', data_type=FieldType.real),
            Field('UPDATED', data_type=FieldType.text),
        ]),
    ])
    def test_get_unique_fields(self, csv_path, name, delimiter, expected):
        """
        Test get unique fields
        """
        path = csv_path.joinpath(name)
        assert path.is_file()
        query = QueryDelimitedFileToTable(
            path, target=None, delimiter=delimiter)
        fields = query._get_unique_fields()
        names = [f.name.casefold() for f in fields]
        assert len(names) == len(set(names))
        assert fields == tuple(expected)
    # End test_get_unique_fields method
    
    @mark.parametrize('name, delimiter, count', [
        ('badname.csv', COMMA, 7),
        ('comma.csv', COMMA, 7),
        ('empty_columns.csv', COMMA, 7),
        ('good.csv', COMMA, 7),
        ('header_data_mismatch.csv', COMMA, 139),
        ('keywords.csv', COMMA, 7),
        ('lower.csv', COMMA, 7),
        ('missingdata.csv', COMMA, 7),
        ('missingheader.csv', COMMA, 6),
        ('missingname.csv', COMMA, 7),
        ('nodata.csv', COMMA, 0),
        ('null.csv', COMMA, 7),
        ('null_as_string.csv', COMMA, 7),
        ('pipe.csv', PIPE, 7),
        ('poly.csv', COMMA, 7),
        ('repeated_column.csv', COMMA, 7),
    ])
    def test_rows(self, csv_path, name, delimiter, count):
        """
        Test rows
        """
        path = csv_path.joinpath(name)
        assert path.is_file()
        query = QueryDelimitedFileToTable(
            path, target=None, delimiter=delimiter)
        assert len(query.rows()) == count
    # End test_rows method

    def test_replace_nulls(self):
        """
        Test replace nulls
        """
        records = [('a', 'b', '<unset>'), ('d', 'null', '')]
        result = QueryDelimitedFileToTable._replace_nulls(records)
        assert result == [('a', 'b', None), ('d', None, None)]
    # End test_replace_nulls method
# End TestQueryDelimitedFileToTable class


if __name__ == '__main__':  # pragma: no cover
    pass
