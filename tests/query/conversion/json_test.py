# -*- coding: utf-8 -*-
"""
Tests for JSON Conversion Classes
"""


from fudgeo import FeatureClass, Field
from fudgeo.enumeration import FieldType, GeometryType
from fudgeo.geometry.linestring import LineString, MultiLineString
from fudgeo.geometry.point import MultiPoint, Point
from fudgeo.geometry.polygon import MultiPolygon, Polygon
from shapely import (
    Point as ShapelyPoint, LineString as ShapelyLineString,
    Polygon as ShapelyPolygon, MultiPoint as ShapelyMultiPoint,
    MultiLineString as ShapelyMultiLineString,
    MultiPolygon as ShapelyMultiPolygon)
from pytest import mark

from spyops.crs.constant import WGS84
from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.query.conversion.json import (
    QueryFeaturesToGeoJSON, QueryGeoJSONToFeaturesLineString,
    QueryGeoJSONToFeaturesMultiLineString, QueryGeoJSONToFeaturesMultiPoint,
    QueryGeoJSONToFeaturesMultiPolygon, QueryGeoJSONToFeaturesPoint,
    QueryGeoJSONToFeaturesPolygon, geojson_query_factory)
from spyops.shared.constant import FEATURE_COLLECTION
from spyops.shared.enumeration import GeoJSONGeometryType
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


class TestQueryGeoJSONToFeaturesPoint:
    """
    Test QueryGeoJSONToFeaturesPoint
    """
    def _get_query(self, path):
        """
        Get Query
        """
        source = path.joinpath('point.geojson')
        assert source.is_file()
        return QueryGeoJSONToFeaturesPoint(source, None)
    # End _get_query method

    def test_data(self, geojson_path):
        """
        Test data
        """
        query = self._get_query(geojson_path)
        assert isinstance(query._data, dict)
    # End test_data method
    
    def test_fields(self, geojson_path):
        """
        Test fields
        """
        query = self._get_query(geojson_path)
        assert query._fields == (
            Field('ENTITY', data_type=FieldType.text),
            Field('ENTITY_NAME', data_type=FieldType.text),
            Field('VALDATE', data_type=FieldType.text),
            Field('PROVIDER', data_type=FieldType.integer),
            Field('DATANAME', data_type=FieldType.text),
            Field('ACCURACY', data_type=FieldType.integer),
            Field('FILE_NAME', data_type=FieldType.text),
            Field('CODE', data_type=FieldType.integer)
        )
    # End test_fields method

    @mark.parametrize('field_names, expected', [
        (['AA', 'AA'], ['AA', 'AA_1']),
        (['AA', 'aa'], ['AA', 'aa_1']),
        (['AA', 'BB'], ['AA', 'BB']),
        (['AA', 'BB', 'AA', 'BB'], ['AA', 'BB', 'AA_1', 'BB_1']),
        (['AA', 'AA', 'AA'], ['AA', 'AA_1', 'AA_2']),
    ])
    def test_make_unique_fields(self, field_names, expected):
        """
        Test make unique fields
        """
        fields = [Field(name, data_type=FieldType.text) for name in field_names]
        names = [n.casefold() for n in field_names]
        result = QueryGeoJSONToFeaturesPoint._make_unique_fields(fields, names)
        assert [f.name for f in result] == expected
    # End test_make_unique_fields method
    
    def test_get_fields_from_source(self, geojson_path):
        """
        Test get fields from source
        """
        query = self._get_query(geojson_path)
        assert query._get_fields_from_source() == [
            Field('ENTITY', data_type=FieldType.text),
            Field('ENTITY_NAME', data_type=FieldType.text),
            Field('VALDATE', data_type=FieldType.text),
            Field('PROVIDER', data_type=FieldType.integer),
            Field('DATANAME', data_type=FieldType.text),
            Field('ACCURACY', data_type=FieldType.integer),
            Field('FILE_NAME', data_type=FieldType.text),
            Field('CODE', data_type=FieldType.integer)
        ]
    # End test_get_fields_from_source method
    
    def test_get_unique_fields(self, geojson_path):
        """
        Test get unique fields
        """
        query = self._get_query(geojson_path)
        assert query._get_unique_fields() == (
            Field('ENTITY', data_type=FieldType.text),
            Field('ENTITY_NAME', data_type=FieldType.text),
            Field('VALDATE', data_type=FieldType.text),
            Field('PROVIDER', data_type=FieldType.integer),
            Field('DATANAME', data_type=FieldType.text),
            Field('ACCURACY', data_type=FieldType.integer),
            Field('FILE_NAME', data_type=FieldType.text),
            Field('CODE', data_type=FieldType.integer)
        )
    # End test_get_unique_fields method

    @mark.parametrize('name, code', [
        ('point.geojson', 'EPSG:4617'),
        ('point_alias_formatted.geojson', 'EPSG:4617'),
        ('point_formatted.geojson', 'EPSG:4617'),
        ('point_wgs84.geojson', 'EPSG:4326'),
        ('point_wgs84_formatted.geojson', 'EPSG:4326'),
        ('point_zm.geojson', 'EPSG:4617'),
        ('point_zm_formatted.geojson', 'EPSG:4617'),
        ('point_zm_wgs84.geojson', 'EPSG:4326'),
        ('point_zm_wgs84_formatted.geojson', 'EPSG:4326'),
    ])
    def test_source_crs(self, geojson_path, name, code):
        """
        Test source crs
        """
        source = geojson_path.joinpath(name)
        assert source.is_file()
        query = QueryGeoJSONToFeaturesPoint(source, None)
        assert query.source_crs.to_string() == code
    # End test_source_crs method
    
    def test_source_transformer(self, geojson_path):
        """
        Test source transformer
        """
        query = self._get_query(geojson_path)
        assert query.source_transformer is None
    # End test_source_transformer method

    @mark.parametrize('name, srs_id', [
        ('point.geojson', 4617),
        ('point_alias_formatted.geojson', 4617),
        ('point_formatted.geojson', 4617),
        ('point_wgs84.geojson', 4326),
        ('point_wgs84_formatted.geojson', 4326),
        ('point_zm.geojson', 4617),
        ('point_zm_formatted.geojson', 4617),
        ('point_zm_wgs84.geojson', 4326),
        ('point_zm_wgs84_formatted.geojson', 4326),
    ])
    def test_spatial_reference_system(self, geojson_path, name, srs_id):
        """
        Test spatial reference system
        """
        source = geojson_path.joinpath(name)
        assert source.is_file()
        query = QueryGeoJSONToFeaturesPoint(source, None)
        assert query.spatial_reference_system.srs_id == srs_id
    # End test_spatial_reference_system method

    @mark.parametrize('name, zm', [
        ('point.geojson', (False, False)),
        ('point_alias_formatted.geojson', (False, False)),
        ('point_formatted.geojson', (False, False)),
        ('point_wgs84.geojson', (False, False)),
        ('point_wgs84_formatted.geojson', (False, False)),
        ('point_zm.geojson', (True, True)),
        ('point_zm_formatted.geojson', (True, True)),
        ('point_zm_wgs84.geojson', (True, True)),
        ('point_zm_wgs84_formatted.geojson', (True, True)),
    ])
    def test_has_zm(self, geojson_path, name, zm):
        """
        Test Has ZM
        """
        source = geojson_path.joinpath(name)
        assert source.is_file()
        query = QueryGeoJSONToFeaturesPoint(source, None)
        assert query._has_zm == zm
    # End test_has_zm method

    def test_insert(self, geojson_path, mem_gpkg):
        """
        Test insert
        """
        source = geojson_path.joinpath('point.geojson')
        assert source.is_file()
        target = FeatureClass(mem_gpkg, 'test')
        query = QueryGeoJSONToFeaturesPoint(source, target=target)
        sql = query.insert
        assert 'INTO test(SHAPE, ENTITY, ENTITY_NAME, VALDATE, PROVIDER' in sql
    # End test_insert method

    @mark.parametrize('name, zm', [
        ('point.geojson', (False, False, False)),
        ('point_alias_formatted.geojson', (False, False, False)),
        ('point_formatted.geojson', (False, False, False)),
        ('point_wgs84.geojson', (False, False, False)),
        ('point_wgs84_formatted.geojson', (False, False, False)),
        ('point_zm.geojson', (False, True, True)),
        ('point_zm_formatted.geojson', (False, True, True)),
        ('point_zm_wgs84.geojson', (False, True, True)),
        ('point_zm_wgs84_formatted.geojson', (False, True, True)),
    ])
    def test_zm_config(self, geojson_path, name, zm):
        """
        Test ZM Config
        """
        source = geojson_path.joinpath(name)
        assert source.is_file()
        query = QueryGeoJSONToFeaturesPoint(source, None)
        assert query.zm_config == zm
    # End test_zm_config method

    def test_get_geometry_class(self, geojson_path):
        """
        Test get geometry class
        """
        query = self._get_query(geojson_path)
        assert query._get_geometry_class() is Point
    # End test_get_geometry_class method

    def test_features(self, geojson_path):
        """
        Test features
        """
        query = self._get_query(geojson_path)
        features = query.features(None)
        assert len(features) == 11
        assert all(isinstance(g, ShapelyPoint) for g, *_ in features)
    # End test_features method

    def test_get_target_shape_type(self, geojson_path):
        """
        Test get target shape type
        """
        query = self._get_query(geojson_path)
        assert query._get_target_shape_type() == GeometryType.point
    # End test_get_target_shape_type method
# End TestQueryGeoJSONToFeaturesPoint class


class TestQueryGeoJSONToFeaturesMultiPoint:
    """
    Test QueryGeoJSONToFeaturesMultiPoint
    """
    def test_get_target_shape_type(self, geojson_path):
        """
        Test get target shape type
        """
        source = geojson_path.joinpath('multipoint_formatted.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesMultiPoint(source, None)
        assert query._get_target_shape_type() == GeometryType.multi_point
    # End test_get_target_shape_type method

    def test_features(self, geojson_path):
        """
        Test features
        """
        source = geojson_path.joinpath('multipoint_formatted.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesMultiPoint(source, None)
        features = query.features(None)
        assert len(features) == 1
        assert all(isinstance(g, ShapelyMultiPoint) for g, *_ in features)
    # End test_features method

    def test_get_geometry_class(self, geojson_path):
        """
        Test get geometry class
        """
        source = geojson_path.joinpath('multipoint_formatted.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesMultiPoint(source, None)
        assert query._get_geometry_class() is MultiPoint
    # End test_get_geometry_class method
# End TestQueryGeoJSONToFeaturesLineString class


class TestQueryGeoJSONToFeaturesLineString:
    """
    Test QueryGeoJSONToFeaturesLineString
    """
    def test_get_target_shape_type(self, geojson_path):
        """
        Test get target shape type
        """
        source = geojson_path.joinpath('line_formatted.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesLineString(source, None)
        assert query._get_target_shape_type() == GeometryType.linestring
    # End test_get_target_shape_type method

    def test_features(self, geojson_path):
        """
        Test features
        """
        source = geojson_path.joinpath('line_formatted.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesLineString(source, None)
        features = query.features(None)
        assert len(features) == 66
        assert all(isinstance(g, ShapelyLineString) for g, *_ in features)
    # End test_features method

    def test_get_geometry_class(self, geojson_path):
        """
        Test get geometry class
        """
        source = geojson_path.joinpath('line_formatted.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesLineString(source, None)
        assert query._get_geometry_class() is LineString
    # End test_get_geometry_class method
# End TestQueryGeoJSONToFeaturesLineString class


class TestQueryGeoJSONToFeaturesMultiLineString:
    """
    Test QueryGeoJSONToFeaturesMultiLineString
    """
    def test_get_target_shape_type(self, geojson_path):
        """
        Test get target shape type
        """
        source = geojson_path.joinpath('multiline.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesMultiLineString(source, None)
        assert query._get_target_shape_type() == GeometryType.multi_linestring
    # End test_get_target_shape_type method

    def test_features(self, geojson_path):
        """
        Test features
        """
        source = geojson_path.joinpath('multiline.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesMultiLineString(source, None)
        features = query.features(None)
        assert len(features) == 4
        assert all(isinstance(g, ShapelyMultiLineString) for g, *_ in features)
    # End test_features method

    def test_get_geometry_class(self, geojson_path):
        """
        Test get geometry class
        """
        source = geojson_path.joinpath('multiline.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesMultiLineString(source, None)
        assert query._get_geometry_class() is MultiLineString
    # End test_get_geometry_class method
# End TestQueryGeoJSONToFeaturesMultiLineString class


class TestQueryGeoJSONToFeaturesPolygon:
    """
    Test QueryGeoJSONToFeaturesPolygon
    """
    def test_get_target_shape_type(self, geojson_path):
        """
        Test get target shape type
        """
        source = geojson_path.joinpath('polygon.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesPolygon(source, None)
        assert query._get_target_shape_type() == GeometryType.polygon
    # End test_get_target_shape_type method

    def test_features(self, geojson_path):
        """
        Test features
        """
        source = geojson_path.joinpath('polygon.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesPolygon(source, None)
        features = query.features(None)
        assert len(features) == 382
        assert all(isinstance(g, ShapelyPolygon) for g, *_ in features)
    # End test_features method

    def test_get_geometry_class(self, geojson_path):
        """
        Test get geometry class
        """
        source = geojson_path.joinpath('polygon.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesPolygon(source, None)
        assert query._get_geometry_class() is Polygon
    # End test_get_geometry_class method
# End TestQueryGeoJSONToFeaturesPolygon class


class TestQueryGeoJSONToFeaturesMultiPolygon:
    """
    Test QueryGeoJSONToFeaturesPolygon
    """
    def test_get_target_shape_type(self, geojson_path):
        """
        Test get target shape type
        """
        source = geojson_path.joinpath('multipolygon.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesMultiPolygon(source, None)
        assert query._get_target_shape_type() == GeometryType.multi_polygon
    # End test_get_target_shape_type method

    def test_features(self, geojson_path):
        """
        Test features
        """
        source = geojson_path.joinpath('multipolygon.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesMultiPolygon(source, None)
        features = query.features(None)
        assert len(features) == 18
        assert all(isinstance(g, ShapelyMultiPolygon) for g, *_ in features)
    # End test_features method

    def test_get_geometry_class(self, geojson_path):
        """
        Test get geometry class
        """
        source = geojson_path.joinpath('multipolygon.geojson')
        assert source.is_file()
        query = QueryGeoJSONToFeaturesMultiPolygon(source, None)
        assert query._get_geometry_class() is MultiPolygon
    # End test_get_geometry_class method
# End TestQueryGeoJSONToFeaturesMultiPolygon class


@mark.parametrize('name, type_, cls', [
    ('line_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesLineString),
    ('line_wgs84_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesLineString),
    ('line_zm.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesLineString),
    ('line_zm_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesLineString),
    ('line_zm_wgs84_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesLineString),
    ('multiline.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiLineString),
    ('multiline_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiLineString),
    ('multiline_wgs84.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiLineString),
    ('multiline_wgs84_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiLineString),
    ('multipoint_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPoint),
    ('multipoint_wgs84.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPoint),
    ('multipoint_wgs84_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPoint),
    ('multipoint_zm.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPoint),
    ('multipoint_zm_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPoint),
    ('multipoint_zm_wgs84.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPoint),
    ('multipoint_zm_wgs84_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPoint),
    ('multipolygon.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_wgs84.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_wgs84_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_zm.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_zm_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_zm_wgs84.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_zm_wgs84_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesMultiPolygon),
    ('point.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPoint),
    ('point_alias_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPoint),
    ('point_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPoint),
    ('point_wgs84.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPoint),
    ('point_wgs84_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPoint),
    ('point_zm.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPoint),
    ('point_zm_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPoint),
    ('point_zm_wgs84.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPoint),
    ('point_zm_wgs84_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPoint),
    ('polygon.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPolygon),
    ('polygon_wgs84.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPolygon),
    ('polygon_wgs84_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPolygon),
    ('polygon_zm_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPolygon),
    ('polygon_zm_wgs84_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesPolygon),    ('line_formatted.geojson', GeoJSONGeometryType.AUTO, QueryGeoJSONToFeaturesLineString),
    ('line_wgs84_formatted.geojson', GeoJSONGeometryType.LINESTRING, QueryGeoJSONToFeaturesLineString),
    ('line_zm.geojson', GeoJSONGeometryType.LINESTRING, QueryGeoJSONToFeaturesLineString),
    ('line_zm_formatted.geojson', GeoJSONGeometryType.LINESTRING, QueryGeoJSONToFeaturesLineString),
    ('line_zm_wgs84_formatted.geojson', GeoJSONGeometryType.LINESTRING, QueryGeoJSONToFeaturesLineString),
    ('multiline.geojson', GeoJSONGeometryType.MULTI_LINESTRING, QueryGeoJSONToFeaturesMultiLineString),
    ('multiline_formatted.geojson', GeoJSONGeometryType.MULTI_LINESTRING, QueryGeoJSONToFeaturesMultiLineString),
    ('multiline_wgs84.geojson', GeoJSONGeometryType.MULTI_LINESTRING, QueryGeoJSONToFeaturesMultiLineString),
    ('multiline_wgs84_formatted.geojson', GeoJSONGeometryType.MULTI_LINESTRING, QueryGeoJSONToFeaturesMultiLineString),
    ('multipoint_formatted.geojson', GeoJSONGeometryType.MULTI_POINT, QueryGeoJSONToFeaturesMultiPoint),
    ('multipoint_wgs84.geojson', GeoJSONGeometryType.MULTI_POINT, QueryGeoJSONToFeaturesMultiPoint),
    ('multipoint_wgs84_formatted.geojson', GeoJSONGeometryType.MULTI_POINT, QueryGeoJSONToFeaturesMultiPoint),
    ('multipoint_zm.geojson', GeoJSONGeometryType.MULTI_POINT, QueryGeoJSONToFeaturesMultiPoint),
    ('multipoint_zm_formatted.geojson', GeoJSONGeometryType.MULTI_POINT, QueryGeoJSONToFeaturesMultiPoint),
    ('multipoint_zm_wgs84.geojson', GeoJSONGeometryType.MULTI_POINT, QueryGeoJSONToFeaturesMultiPoint),
    ('multipoint_zm_wgs84_formatted.geojson', GeoJSONGeometryType.MULTI_POINT, QueryGeoJSONToFeaturesMultiPoint),
    ('multipolygon.geojson', GeoJSONGeometryType.MULTI_POLYGON, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_formatted.geojson', GeoJSONGeometryType.MULTI_POLYGON, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_wgs84.geojson', GeoJSONGeometryType.MULTI_POLYGON, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_wgs84_formatted.geojson', GeoJSONGeometryType.MULTI_POLYGON, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_zm.geojson', GeoJSONGeometryType.MULTI_POLYGON, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_zm_formatted.geojson', GeoJSONGeometryType.MULTI_POLYGON, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_zm_wgs84.geojson', GeoJSONGeometryType.MULTI_POLYGON, QueryGeoJSONToFeaturesMultiPolygon),
    ('multipolygon_zm_wgs84_formatted.geojson', GeoJSONGeometryType.MULTI_POLYGON, QueryGeoJSONToFeaturesMultiPolygon),
    ('point.geojson', GeoJSONGeometryType.POINT, QueryGeoJSONToFeaturesPoint),
    ('point_alias_formatted.geojson', GeoJSONGeometryType.POINT, QueryGeoJSONToFeaturesPoint),
    ('point_formatted.geojson', GeoJSONGeometryType.POINT, QueryGeoJSONToFeaturesPoint),
    ('point_wgs84.geojson', GeoJSONGeometryType.POINT, QueryGeoJSONToFeaturesPoint),
    ('point_wgs84_formatted.geojson', GeoJSONGeometryType.POINT, QueryGeoJSONToFeaturesPoint),
    ('point_zm.geojson', GeoJSONGeometryType.POINT, QueryGeoJSONToFeaturesPoint),
    ('point_zm_formatted.geojson', GeoJSONGeometryType.POINT, QueryGeoJSONToFeaturesPoint),
    ('point_zm_wgs84.geojson', GeoJSONGeometryType.POINT, QueryGeoJSONToFeaturesPoint),
    ('point_zm_wgs84_formatted.geojson', GeoJSONGeometryType.POINT, QueryGeoJSONToFeaturesPoint),
    ('polygon.geojson', GeoJSONGeometryType.POLYGON, QueryGeoJSONToFeaturesPolygon),
    ('polygon_wgs84.geojson', GeoJSONGeometryType.POLYGON, QueryGeoJSONToFeaturesPolygon),
    ('polygon_wgs84_formatted.geojson', GeoJSONGeometryType.POLYGON, QueryGeoJSONToFeaturesPolygon),
    ('polygon_zm_formatted.geojson', GeoJSONGeometryType.POLYGON, QueryGeoJSONToFeaturesPolygon),
    ('polygon_zm_wgs84_formatted.geojson', GeoJSONGeometryType.POLYGON, QueryGeoJSONToFeaturesPolygon),
])
def test_geojson_query_factory(geojson_path, name, type_, cls):
    """
    Test geojson_query_factory
    """
    path = geojson_path.joinpath(name)
    assert path.is_file()
    assert geojson_query_factory(path, type_) is cls
# End test_geojson_query_factory function


if __name__ == '__main__':  # pragma: no cover
    pass
