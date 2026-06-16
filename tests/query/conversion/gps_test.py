# -*- coding: utf-8 -*-
"""
Tests for GPS Conversion Classes
"""


from fudgeo import FeatureClass, Field
from fudgeo.enumeration import FieldType, GeometryType
from pyproj import CRS
from pytest import mark

from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.query.conversion.gps import (
    QueryFeaturesToGPXPoint,
    QueryGPXToFeaturesLineString, QueryGPXToFeaturesPoint)

pytestmark = [mark.conversion, mark.gps, mark.query]


class TestQueryFeaturesToGPXPoint:
    """
    Test Query Features To GPX Point
    """
    def test_get_attribute_select(self, inputs):
        """
        Test get attribute select
        """
        fc = inputs['gps_p']
        query = QueryFeaturesToGPXPoint(
            fc, name_field=None, description_field=None,
            z_field=None, date_field=None, where_clause='')
        assert query._get_attribute_select() == 'NULL, NULL, NULL, NULL'

        name_field = Field('name', data_type=FieldType.text)
        desc_field = Field('system', data_type=FieldType.text)
        z_field = Field('distance', data_type=FieldType.real)
        date_field = Field('dt', data_type=FieldType.datetime)
        query = QueryFeaturesToGPXPoint(
            fc, name_field=name_field, description_field=desc_field,
            z_field=z_field, date_field=date_field, where_clause='')
        assert query._get_attribute_select() == 'name, system, distance, dt'
    # End test_get_attribute_select method

    def test_spatial_reference_system(self, inputs):
        """
        Test spatial reference system
        """
        fc = inputs['gps_p']
        query = QueryFeaturesToGPXPoint(
            fc, name_field=None, description_field=None,
            z_field=None, date_field=None, where_clause='')
        assert query.spatial_reference_system.srs_id == 4326
    # End test_spatial_reference_system method

    @mark.parametrize('name, expected', [
        ('gps_p', True),
        ('gps_lcc_p', False),
    ])
    def test_source_transformer(self, inputs, name, expected):
        """
        Test source transformer
        """
        fc = inputs[name]
        query = QueryFeaturesToGPXPoint(
            fc, name_field=None, description_field=None,
            z_field=None, date_field=None, where_clause='')
        assert (query.source_transformer is None) == expected
    # End test_source_transformer method

    def test_select(self, inputs):
        """
        Test select
        """
        fc = inputs['gps_p']
        name_field = Field('name', data_type=FieldType.text)
        desc_field = Field('system', data_type=FieldType.text)
        where = 'fid = 1234'
        query = QueryFeaturesToGPXPoint(
            fc, name_field=name_field, description_field=desc_field,
            z_field=None, date_field=None, where_clause=where)
        sql = query.select
        assert where in sql
        assert 'geom "[Point]", name, system, NULL, NULL' in sql
    # End test_select method

    def test_select_extent(self, inputs):
        """
        Test select with extent
        """
        fc = inputs['gps_p']
        name_field = Field('name', data_type=FieldType.text)
        desc_field = Field('system', data_type=FieldType.text)
        where = 'fid = 1234'
        with Swap(Setting.EXTENT, Extent.from_bounds(-180, -90, 180, 90, crs=CRS(4326))):
            query = QueryFeaturesToGPXPoint(
                fc, name_field=name_field, description_field=desc_field,
                z_field=None, date_field=None, where_clause=where)
            sql = query.select
        assert where in sql
        assert 'geom "[Point]", name, system, NULL, NULL' in sql
        assert 'minx <= -71.2' in sql
    # End test_select_extent method
# End TestQueryFeaturesToGPXPoint class


class TestQueryGPXToFeaturesPoint:
    """
    Test Query GPX to Features Point
    """
    def test_source_crs(self):
        """
        Test source crs
        """
        query = QueryGPXToFeaturesPoint(None)
        assert query.source_crs == CRS(4326)
    # End test_source_crs method

    @mark.parametrize('crs, expected', [
        (CRS(4326), True),
        (CRS(4617), False),
    ])
    def test_source_transformer(self, crs, expected):
        """
        Test source transformer
        """
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs):
            query = QueryGPXToFeaturesPoint(None)
            assert (query.source_transformer is None) == expected
    # End test_source_transformer method

    def test_has_zm(self):
        """
        Test Has ZM
        """
        query = QueryGPXToFeaturesPoint(None)
        assert query._has_zm == (True, False)
    # End test_has_zm method

    def test_insert(self, mem_gpkg):
        """
        Test insert
        """
        fc = FeatureClass(geopackage=mem_gpkg, name='points_p')
        query = QueryGPXToFeaturesPoint(fc)
        sql = query.insert
        assert 'INTO points_p(SHAPE, NAME, DESCRIPTION, TYPE, COMMENT,' in sql
    # End test_insert method

    def test_zm_config(self):
        """
        Test ZM Config
        """
        query = QueryGPXToFeaturesPoint(None)
        assert query.zm_config == (False, True, False)
    # End test_zm_config method

    def test_get_target_shape_type(self):
        """
        Test get target shape type
        """
        query = QueryGPXToFeaturesPoint(None)
        assert query._get_target_shape_type() == GeometryType.point
    # End test_get_target_shape_type method

    def test_get_unique_fields(self):
        """
        Test _get_unique_fields
        """
        query = QueryGPXToFeaturesPoint(None)
        assert [f.name for f in query._get_unique_fields()] == [
            'NAME', 'DESCRIPTION', 'TYPE', 'COMMENT', 'SYMBOL',
            'ELEVATION', 'DT']
    # End test_get_unique_fields method
# End TestQueryGPXToFeaturesPoint class


class TestQueryGPXToFeaturesLineString:
    """
    Test Query GPX to Features Line String
    """
    def test_get_target_shape_type(self):
        """
        Test get target shape type
        """
        query = QueryGPXToFeaturesLineString(None)
        assert query._get_target_shape_type() == GeometryType.linestring
    # End test_get_target_shape_type method

    def test_get_unique_fields(self):
        """
        Test _get_unique_fields
        """
        query = QueryGPXToFeaturesLineString(None)
        assert [f.name for f in query._get_unique_fields()] == [
            'NAME', 'DESCRIPTION', 'TYPE']
    # End test_get_unique_fields method
# End TestQueryGPXToFeaturesLineString class


if __name__ == '__main__':  # pragma: no cover
    pass
