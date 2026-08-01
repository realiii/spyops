# -*- coding: utf-8 -*-
"""
Test for Editing Query classes
"""


from spyops.query.editing import QueryGeneralize


class TestQueryGeneralize:
    """
    Test Query Generalize
    """
    def test_short_name(self):
        """
        Test short name
        """
        query = QueryGeneralize(None)
        assert query._short_name.startswith('editing_')
    # End test_short_name method

    def test_intermediate_fields(self, ntdb_zm_small):
        """
        Test intermediate fields
        """
        source = ntdb_zm_small['hydro_a']
        query = QueryGeneralize(source)
        fields = query._intermediate_fields
        assert [f.name for f in fields] == ['ORIG_FID', 'SHAPE']
    # End test_intermediate_fields method

    def test_get_field_names(self, ntdb_zm_small):
        """
        Test get field names
        """
        source = ntdb_zm_small['hydro_a']
        query = QueryGeneralize(source)
        assert query._get_field_names() == ['SHAPE']
    # End test_get_field_names method

    def test_update(self, ntdb_zm_small):
        """
        Test update
        """
        source = ntdb_zm_small['hydro_a']
        query = QueryGeneralize(source)
        sql = query.update
        assert 'UPDATE hydro_a ' in sql
        assert 'WHERE hydro_a.fid = temp.tmp_hydro_a_' in sql
    # End test_update method
# End TestQueryGeneralize class


if __name__ == '__main__':  # pragma: no cover
    pass
