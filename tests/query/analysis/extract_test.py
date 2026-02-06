# -*- coding: utf-8 -*-
"""
Test for Extract Query classes
"""


from fudgeo import FeatureClass, Field
from fudgeo.constant import COMMA_SPACE
from fudgeo.enumeration import FieldType
from pyproj import CRS
from pytest import approx, mark, raises

from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.query.analysis.extract import (
    QueryClip, QuerySelect, QuerySplit, QuerySplitByAttributes)
from spyops.geometry.config import GeometryConfig


pytestmark = [mark.extract, mark.query]


class TestQuerySelect:
    """
    Test Query Select
    """
    def test_select_and_insert(self, world_features, mem_gpkg):
        """
        Test select and insert statements
        """
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name='test_target')
        query = QuerySelect(source=source, target=target)
        assert query.select.strip().startswith('SELECT SHAPE "[Polygon]"')
        assert 'INTO test_target' in query.insert
    # End test_select_and_insert method

    def test_grid_size(self, world_features, mem_gpkg):
        """
        Test grid size
        """
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name='test_target')
        query = QuerySelect(source=source, target=target)
        assert query.grid_size is None
    # End test_grid_size method

    def test_source_extent(self, world_features, mem_gpkg):
        """
        Test source extent
        """
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name='test_target')
        where_clause = 'ASDF = 1234'
        query = QuerySelect(source=source, target=target, where_clause=where_clause)
        assert approx(query._shared_extent(query.source), abs=0.001) == (-180, -90, 180, 83.6654)
        assert where_clause in query.select
        with Swap(Setting.EXTENT, Extent.from_bounds(-100, -60, 100, 90, CRS(4326))):
            assert approx(query._shared_extent(query.source), abs=0.001) == (-100, -60, 100, 83.6654)
            assert '100' in query.select
            assert '-100' in query.select
            assert '-60' in query.select
            assert '83.665' in query.select
            assert where_clause in query.select
    # End test_source_extent method
# End TestQuerySelect class


class TestQuerySplitByAttributes:
    """
    Test Query Split By Attributes
    """
    @mark.parametrize('name, fix_name, group_names', [
        ('cities', 'world_tables', ('FIPS_CNTRY', 'CNTRY_NAME', 'STATUS')),
        ('lakes_a', 'world_features', ('FEATURE_ID', 'PART_ID', 'NAME')),
    ])
    def test_select_and_insert(self, request, name, fix_name, group_names):
        """
        Test select and insert statements
        """
        gpkg = request.getfixturevalue(fix_name)
        element = gpkg[name]
        fields = [Field(n, data_type=FieldType.text) for n in group_names]
        group_names = COMMA_SPACE.join(group_names)
        query = QuerySplitByAttributes(element, fields)
        assert f'FROM {element.name}' in query.groups
        assert 'INTO {}(' in query.insert.strip()
        assert f'dense_rank() OVER (ORDER BY {group_names}' in query.select
    # End test_select_and_insert method

    def test_grid_size(self, world_features, mem_gpkg):
        """
        Test grid size
        """
        element = world_features['lakes_a']
        group_names = ('FEATURE_ID', 'PART_ID', 'NAME')
        fields = [Field(n, data_type=FieldType.text) for n in group_names]
        query = QuerySplitByAttributes(element, fields)
        assert query.grid_size is None
    # End test_grid_size method

    def test_source_extent(self, world_features, mem_gpkg):
        """
        Test source extent
        """
        source = world_features['admin_a']
        fields = (Field('ISO_CC', data_type=FieldType.text),
                  Field('LAND_TYPE', data_type=FieldType.text))
        query = QuerySplitByAttributes(source, fields=fields)
        with Swap(Setting.EXTENT, Extent.from_bounds(20, 10, 30, 20, crs=CRS(4326))):
            assert '20' in query.select
            assert '30' in query.groups
    # End test_source_extent method
# End TestQuerySplitByAttributes class


class TestQueryClip:
    """
    Test Query Clip
    """
    def test_select_and_insert(self, world_features, inputs, mem_gpkg):
        """
        Test select and insert statements
        """
        target = FeatureClass(mem_gpkg, 'test_target')
        source = world_features['cities_p']
        operator = inputs['clipper_a']
        query = QueryClip(source, target, operator, xy_tolerance=None)
        assert query.has_intersection is True
        assert approx(query.operator_extent, abs=0.0001) == (
            6.74573, 46.49314, 16.47727, 51.70966)
        assert approx(query.source_extent, abs=0.001) == (
            -176.15156, -54.79199, 179.19906, 78.20000)
        assert query.select == query.select_intersect
        assert query.select.strip().startswith('SELECT SHAPE "[Point]"')
        assert 'INTO test_target(' in query.insert
        assert query.select_disjoint
        assert query.operator is operator
        assert isinstance(query.geometry_config, GeometryConfig)
        with raises(ValueError):
            _ = query.target_full
        assert 'FROM clipper_a' in query.select_operator
    # End test_select_and_insert method

    @mark.parametrize('epsg_code, expected', [
        (4326, 8.988709851109888e-05),
        (6654, 10),
    ])
    @mark.parametrize('op_name', [
        'grid_a',
        'grid_10tm_a',
    ])
    def test_grid_size_output(self, ntdb_zm_small, grid_index, mem_gpkg, epsg_code, expected, op_name):
        """
        Test grid size when output coordinate system is set
        """
        target = FeatureClass(mem_gpkg, 'test_target')
        source = ntdb_zm_small['hydro_6654_a']
        operator = grid_index[op_name]
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(epsg_code)):
            query = QueryClip(source, target, operator, xy_tolerance=10)
            assert approx(query.grid_size, abs=10**-9) == expected
        assert query.has_intersection is True
    # End test_grid_size method

    def test_extent(self, world_features, inputs, mem_gpkg):
        """
        Test extent
        """
        source = world_features['admin_a']
        operator = inputs['clipper_a']
        target = FeatureClass(mem_gpkg, 'test_target')
        query = QueryClip(source, operator=operator, target=target, xy_tolerance=None)
        with Swap(Setting.EXTENT, Extent.from_bounds(6.75, 46.5, 16.5, 51.5, crs=CRS(4326))):
            assert '46.5' in query.select_source
            assert '51.5' in query.select_operator
    # End test_extent method
# End TestQueryClip class


class TestQuerySplit:
    """
    Test QuerySplit class
    """
    def test_extent(self, world_features, inputs, mem_gpkg):
        """
        Test extent
        """
        splitter = inputs['splitter_a']
        source = world_features['admin_a']
        query = QuerySplit(source, operator=splitter, target=None, xy_tolerance=None)
        with Swap(Setting.EXTENT, Extent.from_bounds(7, 47, 16, 52, crs=CRS(4326))):
            assert ' 7.0 ' in query.select_source
            assert ' 52.0 ' in query.select_operator
    # End test_extent method
# End TestQuerySplit class


if __name__ == '__main__':  # pragma: no cover
    pass
