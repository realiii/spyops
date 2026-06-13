# -*- coding: utf-8 -*-
"""
Tests for GPS Conversion Classes
"""
from fudgeo import Field
from fudgeo.enumeration import FieldType
from pyproj import CRS
from pytest import mark

from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.query.conversion.gps import QueryFeaturesToGPXPoint

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


if __name__ == '__main__':  # pragma: no cover
    pass
