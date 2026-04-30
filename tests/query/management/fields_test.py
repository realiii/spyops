# -*- coding: utf-8 -*-
"""
Test for Fields Query classes
"""


from fudgeo import Field
from fudgeo.enumeration import FieldType
from pytest import mark

from spyops.query.management.fields import QueryCalculateEndTime


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


if __name__ == '__main__':  # pragma: no cover
    pass
