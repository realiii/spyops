# -*- coding: utf-8 -*-
"""
Tests for JSON Conversion Classes
"""

from pytest import mark

from spyops.crs.constant import WGS84
from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.query.conversion.json import QueryFeaturesToGeoJSON
from spyops.shared.constant import FEATURE_COLLECTION
from spyops.shared.keywords import (
    CRS_KEY, FEATURES_KEY, HASM_KEY, HASZ_KEY, TYPE_KEY)


pytestmark = [mark.conversion, mark.json, mark.query]


class TestQueryFeaturesToGeoJSON:
    """
    Test Query Features to GeoJSON
    """
    def test_select(self, ntdb_zm_small):
        """
        Test select
        """
        source = ntdb_zm_small['hydro_6654_zm_a']
        with Swap(Setting.EXTENT, Extent.from_bounds(
                -114.28, 51.125, -114.21, 51.185, crs=WGS84)):
            query = QueryFeaturesToGeoJSON(
                source, as_wgs84=True, include_z=True,
                include_m=True, use_aliases=True, where_clause='')
            assert 'minx' in query.select
    # End test_select method

    def test_field_names_and_count(self, ntdb_zm_small):
        """
        Test field names and count
        """
        source = ntdb_zm_small['hydro_6654_zm_a']
        query = QueryFeaturesToGeoJSON(
            source, as_wgs84=True, include_z=True,
            include_m=True, use_aliases=True, where_clause='')
        count, insert_names, select_names = query._field_names_and_count(source)
        assert count == 0
        assert insert_names == ''
        assert select_names == (
            'geom "[PolygonZM]", fid, FEATURE_ID, PART_ID, OBJECTID_1, ENTITY, '
            'ENTITY_NAME, VALDATE, PROVIDER, DATANAME, ACCURACY, '
            'FILE_NAME, CODE')
    # End test_field_names_and_count method

    @mark.parametrize('as_wgs84, srs_id', [
        (True, 4326),
        (False, 6654),
    ])
    def test_spatial_reference_system(self, ntdb_zm_small, as_wgs84, srs_id):
        """
        Test spatial reference system
        """
        source = ntdb_zm_small['hydro_6654_zm_a']
        query = QueryFeaturesToGeoJSON(
            source, as_wgs84=as_wgs84, include_z=True,
            include_m=True, use_aliases=True, where_clause='')
        srs = query.spatial_reference_system
        assert srs is not None
        assert query.spatial_reference_system.srs_id == srs_id
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
        query = QueryFeaturesToGeoJSON(
            source, as_wgs84=True, include_z=True,
            include_m=True, use_aliases=use_aliases, where_clause='')
        assert query._get_attribute_names() == expected
    # End test_get_attribute_names method

    @mark.parametrize('include_z, include_m, expected', [
        (True, True, {HASZ_KEY: True, HASM_KEY: True}),
        (True, False, {HASZ_KEY: True}),
        (False, True, {HASM_KEY: True}),
        (False, False, {}),
    ])
    def test_add_zm_flags(self, ntdb_zm_small, include_z, include_m, expected):
        """
        Test add zm flags
        """
        source = ntdb_zm_small['hydro_6654_zm_a']
        query = QueryFeaturesToGeoJSON(
            source, as_wgs84=True, include_z=include_z, include_m=include_m,
            use_aliases=True, where_clause='')
        data = {}
        query._add_zm_flags(data)
        assert data == expected
    # End test_add_zm_flags method

    def test_add_feature_collection(self, ntdb_zm_small):
        """
        Test add feature collection
        """
        source = ntdb_zm_small['hydro_6654_zm_a']
        query = QueryFeaturesToGeoJSON(
            source, as_wgs84=True, include_z=True, include_m=True,
            use_aliases=True, where_clause='')
        data = {}
        query._add_feature_collection(data)
        assert data == {TYPE_KEY: FEATURE_COLLECTION}
    # End test_add_feature_collection method

    @mark.parametrize('name, as_wgs84, expected', [
        ('clipper_a', True, {}),
        ('clipper_a', False, {}),
        ('yyc_a', True, {}),
        ('yyc_a', False, {CRS_KEY: 'EPSG:4269'}),
    ])
    def test_add_crs(self, inputs, name, as_wgs84, expected):
        """
        Test add CRS
        """
        source = inputs[name]
        query = QueryFeaturesToGeoJSON(
            source, as_wgs84=as_wgs84, include_z=True, include_m=True,
            use_aliases=True, where_clause='')
        data = {}
        query._add_crs(data)
        assert data == expected
    # End test_add_crs method

    @mark.parametrize('name', [
        'clipper_a',
        'yyc_a',
        'gps_p',
        'gps_lcc_l',
        'gps_ml',
        'intersect_sans_attr_a',
        'intersect_holes_a',
    ])
    def test_add_features(self, inputs, name):
        """
        Test add features
        """
        source = inputs[name]
        query = QueryFeaturesToGeoJSON(
            source, as_wgs84=True, include_z=True, include_m=True,
            use_aliases=True, where_clause='')
        data = {}
        query._add_features(data)
        assert FEATURES_KEY in data
        assert len(data[FEATURES_KEY]) == len(source)
    # End test_add_features method
# End TestQueryFeaturesToGeoJSON class


if __name__ == '__main__':  # pragma: no cover
    pass
