# -*- coding: utf-8 -*-
"""
Test for Editing Query classes
"""


from pytest import mark
from shapely import MultiPolygon

from spyops.query.editing import (
    QueryDensify, QueryErasePoint, QueryFlip,
    QueryGeneralize)


pytestmark = [mark.query, mark.editing]


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


class TestQueryDensify:
    """
    Test Query Densify
    """
    def test_short_name(self):
        """
        Test short name
        """
        query = QueryDensify(None)
        assert query._short_name.startswith('editing_')
    # End test_short_name method

    def test_intermediate_fields(self, ntdb_zm_small):
        """
        Test intermediate fields
        """
        source = ntdb_zm_small['hydro_a']
        query = QueryDensify(source)
        fields = query._intermediate_fields
        assert [f.name for f in fields] == ['ORIG_FID', 'SHAPE']
    # End test_intermediate_fields method

    def test_get_field_names(self, ntdb_zm_small):
        """
        Test get field names
        """
        source = ntdb_zm_small['hydro_a']
        query = QueryDensify(source)
        assert query._get_field_names() == ['SHAPE']
    # End test_get_field_names method

    def test_update(self, ntdb_zm_small):
        """
        Test update
        """
        source = ntdb_zm_small['hydro_a']
        query = QueryDensify(source)
        sql = query.update
        assert 'UPDATE hydro_a ' in sql
        assert 'WHERE hydro_a.fid = temp.tmp_hydro_a_' in sql
    # End test_update method
# End TestQueryDensify class


class TestQueryFlip:
    """
    Test Query Flip
    """
    def test_short_name(self):
        """
        Test short name
        """
        query = QueryFlip(None)
        assert query._short_name.startswith('editing_')
    # End test_short_name method

    def test_intermediate_fields(self, ntdb_zm_small):
        """
        Test intermediate fields
        """
        source = ntdb_zm_small['hydro_a']
        query = QueryFlip(source)
        fields = query._intermediate_fields
        assert [f.name for f in fields] == ['ORIG_FID', 'SHAPE']
    # End test_intermediate_fields method

    def test_get_field_names(self, ntdb_zm_small):
        """
        Test get field names
        """
        source = ntdb_zm_small['hydro_a']
        query = QueryFlip(source)
        assert query._get_field_names() == ['SHAPE']
    # End test_get_field_names method

    def test_update(self, ntdb_zm_small):
        """
        Test update
        """
        source = ntdb_zm_small['hydro_a']
        query = QueryFlip(source)
        sql = query.update
        assert 'UPDATE hydro_a ' in sql
        assert 'WHERE hydro_a.fid = temp.tmp_hydro_a_' in sql
    # End test_update method
# End TestQueryFlip class


class TestQueryErasePoint:
    """
    Test Query Flip
    """
    def test_short_name(self):
        """
        Test short name
        """
        query = QueryErasePoint(None, None, False, '')
        assert query._short_name.startswith('editing_')
    # End test_short_name method

    def test_intermediate_fields(self, ntdb_zm_tile):
        """
        Test intermediate fields
        """
        source = ntdb_zm_tile['structures_p']
        operator = ntdb_zm_tile['index_a']
        query = QueryErasePoint(source, operator, False, '')
        fields = query._intermediate_fields
        assert [f.name for f in fields] == ['ORIG_FID', 'SHAPE']
    # End test_intermediate_fields method

    def test_get_field_names(self, ntdb_zm_tile):
        """
        Test get field names
        """
        source = ntdb_zm_tile['structures_p']
        operator = ntdb_zm_tile['index_a']
        query = QueryErasePoint(source, operator, False, '')
        assert query._get_field_names() == ['SHAPE']
    # End test_get_field_names method

    def test_update(self, ntdb_zm_tile):
        """
        Test update
        """
        source = ntdb_zm_tile['structures_p']
        operator = ntdb_zm_tile['index_a']
        query = QueryErasePoint(source, operator, False, '')
        sql = query.update
        assert 'UPDATE structures_p ' in sql
        assert 'WHERE structures_p.fid = temp.tmp_structures_p_' in sql
    # End test_update method

    def test_operator_geometry(self, ntdb_zm_tile):
        """
        Test operator geometry
        """
        source = ntdb_zm_tile['structures_p']
        operator = ntdb_zm_tile['index_a']
        query = QueryErasePoint(source, operator, False, '')
        assert isinstance(query._operator_geometry, MultiPolygon)
        assert not query._operator_geometry.is_empty
    # End test_operator_geometry method

    @mark.parametrize('remove_inside, name', [
        (False, '_clip'),
        (True, '_erase'),
    ])
    def test_eraser(self, ntdb_zm_tile, remove_inside, name):
        """
        Test eraser
        """
        source = ntdb_zm_tile['structures_p']
        operator = ntdb_zm_tile['index_a']
        query = QueryErasePoint(source, operator, remove_inside, '')
        assert query.eraser.__name__ == name
    # End test_eraser method
# End TestQueryErasePoint class


if __name__ == '__main__':  # pragma: no cover
    pass
