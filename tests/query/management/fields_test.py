# -*- coding: utf-8 -*-
"""
Test for Fields Query classes
"""


from fudgeo import Field, Table
from fudgeo.enumeration import FieldType
from pytest import mark

from spyops.query.management.fields import (
    QueryCalculateEndTime,
    QueryFieldStatisticsToTableDate, QueryFieldStatisticsToTableNumeric,
    QueryFieldStatisticsToTableText)

pytestmark = [mark.fields, mark.query, mark.management]


class TestQueryCalculateEndTime:
    """
    Test QueryCalculateEndTime
    """
    def test_update_sans_sort(self, world_features):
        """
        Test Update Sans Sort Fields
        """
        source = world_features['admin_a']
        start = Field('NAME', data_type=FieldType.text)
        end = Field('ADMINTYPE', data_type=FieldType.text)
        query = QueryCalculateEndTime(
            source, start_field=start, end_field=end, sort_fields=())
        sql = query.update
        assert 'ITH lead_values AS (' in sql
        assert 'SELECT fid, LEAD(NAME) OVER (' in sql
        assert 'ORDER BY fid)' in sql
        assert 'UPDATE admin_a' in sql
        assert 'SET ADMINTYPE = lead_values.value' in sql
        assert 'FROM lead_values' in sql
        assert 'WHERE admin_a.fid = lead_values.fid' in sql
    # End test_update_sans_sort method

    def test_update_with_sort(self, world_features):
        """
        Test Update with Sort Fields
        """
        source = world_features['admin_a']
        start = Field('NAME', data_type=FieldType.text)
        end = Field('ADMINTYPE', data_type=FieldType.text)
        query = QueryCalculateEndTime(
            source, start_field=start, end_field=end,
            sort_fields=[
                Field('ISO_CC', data_type=FieldType.text),
                Field('ISO_SUB', data_type=FieldType.text),
            ])
        sql = query.update
        assert 'ITH lead_values AS (' in sql
        assert 'SELECT fid, LEAD(NAME) OVER (' in sql
        assert 'ORDER BY ISO_CC, ISO_SUB)' in sql
        assert 'UPDATE admin_a' in sql
        assert 'SET ADMINTYPE = lead_values.value' in sql
        assert 'FROM lead_values' in sql
        assert 'WHERE admin_a.fid = lead_values.fid' in sql
    # End test_update_sans_sort method
# End TestQueryCalculateEndTime class


class TestQueryFieldStatisticsToTable:
    """
    Test Query Field Statistics to Table
    """
    @mark.parametrize('cls, count', [
        (QueryFieldStatisticsToTableNumeric, 20),
        (QueryFieldStatisticsToTableText, 8),
        (QueryFieldStatisticsToTableDate, 13),
    ])
    def test_class_counts(self, cls, count):
        """
        Test class counts
        """
        query = cls(None, None, [], [], '')
        assert len(query._stat_classes) == count
    # End test_class_counts method

    @mark.parametrize('group_fields, count, expected', [
        ([], 11, ['FIELD_NAME', 'FIELD_ALIAS', 'FIELD_TYPE', 'COUNT_',
                  'COUNT_NULL', 'COUNT_NON_NULL', 'UNIQUE_', 'MODE',
                  'LEAST_COMMON', 'MINIMUM', 'MAXIMUM']),
        ([Field('COUNT_', data_type=FieldType.integer),
          Field('MODE', data_type=FieldType.text)], 13, [
            'COUNT__1', 'MODE_1', 'FIELD_NAME', 'FIELD_ALIAS', 'FIELD_TYPE',
            'COUNT_', 'COUNT_NULL', 'COUNT_NON_NULL', 'UNIQUE_', 'MODE',
            'LEAST_COMMON', 'MINIMUM', 'MAXIMUM'])
    ])
    def test_get_unique_fields(self, group_fields, count, expected):
        """
        Test get unique fields
        """
        fields = []
        query = QueryFieldStatisticsToTableText(
            None, None, fields=fields, group_fields=group_fields,
            where_clause='')
        fields = query._get_unique_fields()
        assert len(fields) == count
        assert [f.name for f in fields] == expected
    # End test_get_unique_fields method

    def test_select_sans_group(self, inputs):
        """
        Test select sans group
        """
        source = inputs['cl_run_messages']
        group_fields = fields = []
        query = QueryFieldStatisticsToTableNumeric(
            source, None, fields=fields, group_fields=group_fields,
            where_clause='')
        sql = query.select
        assert 'SELECT {}' in sql
        assert 'WHERE ROWID > -1' in sql
    # End test_select_sans_group method

    def test_select_with_group(self, inputs):
        """
        Test select with group
        """
        source = inputs['cl_run_messages']
        fields = []
        query = QueryFieldStatisticsToTableNumeric(
            source, None, fields=fields,
            group_fields=[Field('LMNO', data_type=FieldType.integer)],
            where_clause="""ASDF > 10""")
        sql = query.select
        assert 'SELECT LMNO, {}' in sql
        assert 'WHERE ASDF > 10' in sql
        assert 'GROUP BY LMNO' in sql
    # End test_select_with_group method

    def test_insert(self, mem_gpkg):
        """
        Test insert
        """
        target = Table(geopackage=mem_gpkg, name='asdf')
        group_fields = fields = []
        query = QueryFieldStatisticsToTableText(
            None, target, fields=fields, group_fields=group_fields,
            where_clause='')
        stub = 'INTO asdf(FIELD_NAME, FIELD_ALIAS, FIELD_TYPE, COUNT_, '
        assert stub in query.insert
        fields = []
        group_fields = [Field('LMNO', data_type=FieldType.integer)]
        target = Table(geopackage=mem_gpkg, name='asdf2')
        query = QueryFieldStatisticsToTableText(
            None, target, fields=fields, group_fields=group_fields,
            where_clause='')
        stub = 'INTO asdf2(LMNO, FIELD_NAME, FIELD_ALIAS, FIELD_TYPE, COUNT_, '
        assert stub in query.insert
    # End test_insert method
# End TestQueryFieldStatisticsToTable class


if __name__ == '__main__':  # pragma: no cover
    pass
