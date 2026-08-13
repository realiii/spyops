# -*- coding: utf-8 -*-
"""
Test for General Query classes
"""


from fudgeo import FeatureClass, Field, Table
from fudgeo.enumeration import FieldType
from pyproj import CRS
from pytest import mark

from spyops.crs.constant import WGS84
from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.query.management.general import (
    QueryFindIdenticalFeatureClass,
    QueryFindIdenticalTable, QuerySortFeatureClass, QuerySortTable)
from spyops.shared.enumeration import SpatialSortOption
from spyops.shared.field import POINT_X, REASON
from spyops.shared.sort import Ascending, Descending

pytestmark = [mark.general, mark.query, mark.management]


class TestQueryFindIdenticalTable:
    """
    Test Query Find Identical Table
    """
    def test_select(self):
        """
        Test select
        """
        query = QueryFindIdenticalTable(None, None, [])
        assert not query.select
    # End test_select method

    def test_has_zm(self):
        """
        Test Has ZM
        """
        query = QueryFindIdenticalTable(None, None, [])
        assert query.has_zm == (False, False)
    # End test_has_zm method
# End TestQueryFindIdenticalTable class


class TestQueryFindIdenticalFeatureClass:
    """
    Test Query Find Identical Feature Class
    """
    def test_select(self, identical):
        """
        Test select
        """
        source = identical['point_p']
        query = QueryFindIdenticalFeatureClass(
            source, target=None, fields=[REASON], include_geometry=False,
            xy_tolerance=None, z_tolerance=None, m_tolerance=None)
        assert not query.select
        query = QueryFindIdenticalFeatureClass(
            source, target=None, fields=[REASON], include_geometry=True,
            xy_tolerance=None, z_tolerance=None, m_tolerance=None)
        assert query.select
    # End test_select method

    @mark.parametrize('fc_name, expected', [
        ('hydro_a', (False, False)),
        ('hydro_m_a', (False, True)),
        ('hydro_zm_a', (True, True)),
    ])
    def test_has_zm(self, ntdb_zm_small, fc_name, expected):
        """
        Test Has ZM
        """
        source = ntdb_zm_small[fc_name]
        query = QueryFindIdenticalFeatureClass(
            source, target=None, fields=[REASON], include_geometry=False,
            xy_tolerance=None, z_tolerance=None, m_tolerance=None)
        assert query.has_zm == expected
    # End test_has_zm method

    def test_grid_size(self, identical):
        """
        Test Grid Size
        """
        source = identical['point_p']
        query = QueryFindIdenticalFeatureClass(
            source, target=None, fields=[REASON], include_geometry=False,
            xy_tolerance=100, z_tolerance=None, m_tolerance=None)
        assert query.grid_size == 100
    # End test_grid_size method
# End TestQueryFindIdenticalFeatureClass class


class TestQuerySortTable:
    """
    Test Query Sort Table
    """
    def test_get_unique_fields(self, inputs):
        """
        Test get unique fields
        """
        source = inputs['xyzm_table']
        query = QuerySortTable(source, target=None, sort_fields=[])
        assert [f.name for f in query._get_unique_fields()] == [
            'ORIG_FID', 'FEATURE_ID', 'PART_ID', 'ENTITY', 'ENTITY_NAME',
            'VALDATE', 'PROVIDER', 'DATANAME', 'ACCURACY', 'FILE_NAME', 'CODE',
            'POINT_X', 'POINT_Y', 'POINT_Z', 'POINT_M']
    # End test_get_unique_fields method

    def test_select_sans_sort(self, inputs):
        """
        Test select sans sorting fields
        """
        source = inputs['xyzm_table']
        query = QuerySortTable(source, target=None, sort_fields=[])
        sql = query.select
        assert 'ORDER BY' not in sql
        assert sql.strip().startswith(
            'SELECT fid, FEATURE_ID, PART_ID, ENTITY, ENTITY_NAME')
    # End test_select_sans_sort method

    def test_select_with_sort(self, inputs):
        """
        Test select with sorting fields
        """
        source = inputs['xyzm_table']
        fld = Field('FEATURE_ID', data_type=FieldType.integer)
        fields = Descending(fld), Ascending(POINT_X)
        query = QuerySortTable(source, target=None, sort_fields=fields)
        sql = query.select
        assert 'ORDER BY' in sql
        assert 'FEATURE_ID DESC, POINT_X ASC' in sql
        assert sql.strip().startswith(
            'SELECT fid, FEATURE_ID, PART_ID, ENTITY, ENTITY_NAME')
    # End test_select_with_sort method

    def test_insert(self, inputs, mem_gpkg):
        """
        Test insert
        """
        source = inputs['xyzm_table']
        target = Table(geopackage=mem_gpkg, name='sorted_table')
        query = QuerySortTable(source, target=target, sort_fields=[])
        sql = query.insert
        assert 'INTO sorted_table(ORIG_FID, FEATURE_ID, PART_ID' in sql
    # End test_insert method
# End TestQuerySortTable class


class TestQuerySortFeatureClass:
    """
    Test Query Sort Feature Class
    """
    def test_get_unique_fields(self, inputs):
        """
        Test get unique fields
        """
        source = inputs['river_p']
        query = QuerySortFeatureClass(
            source, target=None, sort_fields=[],
            spatial_sort_option=SpatialSortOption.NONE)
        assert [f.name for f in query._get_unique_fields()] == [
            'ORIG_FID', 'NAME', 'SYSTEM', 'vertex_index', 'vertex_part',
            'vertex_part_index', 'distance', 'angle']
    # End test_get_unique_fields method

    def test_select_sans_sort(self, inputs):
        """
        Test select sans sorting fields
        """
        source = inputs['river_p']
        query = QuerySortFeatureClass(
            source, target=None, sort_fields=[],
            spatial_sort_option=SpatialSortOption.NONE)
        sql = query.select
        assert 'ORDER BY' not in sql
        assert sql.strip().startswith(
            'SELECT geom "[Point]", fid, NAME, SYSTEM')
    # End test_select_sans_sort method

    def test_select_sans_sort_extent(self, inputs):
        """
        Test select sans sorting fields + extent
        """
        source = inputs['river_p']
        with Swap(Setting.EXTENT, Extent.from_bounds(-180, 0, 0, 90, crs=WGS84)):
            query = QuerySortFeatureClass(
                source, target=None, sort_fields=[],
                spatial_sort_option=SpatialSortOption.NONE)
            sql = query.select
            assert 'ORDER BY' not in sql
            assert sql.strip().startswith(
                'SELECT geom "[Point]", fid, NAME, SYSTEM')
            assert 'minx <= 0.0' in sql
    # End test_select_sans_sort_extent method

    def test_select_sans_sort_and_spatial(self, inputs):
        """
        Test select sans sorting fields with spatial
        """
        source = inputs['river_p']
        query = QuerySortFeatureClass(
            source, target=None, sort_fields=[],
            spatial_sort_option=SpatialSortOption.UPPER_RIGHT_ASCENDING)
        sql = query.select
        assert 'A.*' in sql
        assert 'ORDER BY' in sql
        assert 'B.maxy DESC, B.maxx DESC' in sql
        assert 'ORDER BY' in sql
        assert sql.strip().startswith(
            'SELECT geom "[Point]", fid, NAME, SYSTEM')
        assert 'WHERE ' not in sql
    # End test_select_sans_sort_and_spatial method

    def test_select_sans_sort_and_spatial_extent(self, inputs):
        """
        Test select sans sorting fields with spatial + extent
        """
        source = inputs['river_p']
        with Swap(Setting.EXTENT, Extent.from_bounds(-180, 0, 0, 90, crs=WGS84)):
            query = QuerySortFeatureClass(
                source, target=None, sort_fields=[],
                spatial_sort_option=SpatialSortOption.UPPER_RIGHT_ASCENDING)
            sql = query.select
            assert 'A.*' in sql
            assert 'ORDER BY' in sql
            assert 'B.maxy DESC, B.maxx DESC' in sql
            assert 'ORDER BY' in sql
            assert sql.strip().startswith(
                'SELECT geom "[Point]", fid, NAME, SYSTEM')
            assert 'WHERE ' in sql
            assert 'minx <= 0.0' in sql
    # End test_select_sans_sort_and_spatial_extent method

    def test_select_with_sort(self, inputs):
        """
        Test select with sorting fields
        """
        source = inputs['river_p']
        fields = (Descending(Field('NAME', data_type=FieldType.text)),
                  Ascending(Field('vertex_index', data_type=FieldType.integer)))
        query = QuerySortFeatureClass(
            source, target=None, sort_fields=fields,
            spatial_sort_option=SpatialSortOption.NONE)
        sql = query.select
        assert 'ORDER BY' in sql
        assert 'NAME DESC, vertex_index ASC' in sql
        assert sql.strip().startswith(
            'SELECT geom "[Point]", fid, NAME, SYSTEM')
    # End test_select_with_sort method

    def test_select_with_sort_and_spatial(self, inputs):
        """
        Test select with sorting fields and spatial
        """
        source = inputs['river_p']
        fields = (Descending(Field('NAME', data_type=FieldType.text)),
                  Ascending(Field('vertex_index', data_type=FieldType.integer)))
        query = QuerySortFeatureClass(
            source, target=None, sort_fields=fields,
            spatial_sort_option=SpatialSortOption.UPPER_RIGHT_ASCENDING)
        sql = query.select
        assert 'A.*' in sql
        assert 'ORDER BY' in sql
        assert 'B.maxy DESC, B.maxx DESC, ' in sql
        assert 'A.NAME DESC, A.vertex_index ASC' in sql
        assert sql.strip().startswith(
            'SELECT geom "[Point]", fid, NAME, SYSTEM')
        assert 'WHERE ' not in sql
    # End test_select_with_sort_and_spatial method

    def test_select_with_sort_and_spatial_and_extent(self, inputs):
        """
        Test select with sorting fields and spatial + extent
        """
        source = inputs['river_p']
        fields = (Descending(Field('NAME', data_type=FieldType.text)),
                  Ascending(Field('vertex_index', data_type=FieldType.integer)))
        with Swap(Setting.EXTENT, Extent.from_bounds(-180, 0, 0, 90, crs=WGS84)):
            query = QuerySortFeatureClass(
                source, target=None, sort_fields=fields,
                spatial_sort_option=SpatialSortOption.UPPER_RIGHT_ASCENDING)
            sql = query.select
            assert 'A.*' in sql
            assert 'ORDER BY' in sql
            assert 'B.maxy DESC, B.maxx DESC, ' in sql
            assert 'A.NAME DESC, A.vertex_index ASC' in sql
            assert sql.strip().startswith(
                'SELECT geom "[Point]", fid, NAME, SYSTEM')
            assert 'WHERE ' in sql
            assert 'minx <= 0.0' in sql
    # End test_select_with_sort_and_spatial_and_extent method

    def test_insert(self, inputs, mem_gpkg):
        """
        Test insert
        """
        source = inputs['river_p']
        target = FeatureClass(geopackage=mem_gpkg, name='sorted_fc')
        query = QuerySortFeatureClass(
            source, target=target, sort_fields=[],
            spatial_sort_option=SpatialSortOption.NONE)
        sql = query.insert
        assert 'INTO sorted_fc(SHAPE, ORIG_FID, NAME, SYSTEM' in sql
    # End test_insert method
# End TestQuerySortFeatureClass class


if __name__ == '__main__':  # pragma: no cover
    pass
