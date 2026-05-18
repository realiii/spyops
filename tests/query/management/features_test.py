# -*- coding: utf-8 -*-
"""
Test for Features Query classes
"""


from sqlite3 import OperationalError
from typing import Callable

from fudgeo import FeatureClass, Field, Table
from fudgeo.enumeration import FieldType, ShapeType
from fudgeo.geometry import Point, PointM, PointZ, PointZM
from pyproj import CRS
from pytest import approx, mark, raises

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.geometry.config import GeometryConfig
from spyops.query.management.features import (
    QueryAddXYCoordinates, QueryCalculateGeometryAttributes, QueryCheckGeometry,
    QueryFeatureEnvelopeToPolygon, QueryFeatureToLine, QueryFeatureToPoint,
    QueryFeatureToPolygon, QueryFeatureToPrepare, QueryFeatureVerticesToPoints,
    QueryMinimumBoundingGeometryAll, QueryMinimumBoundingGeometryList,
    QueryMinimumBoundingGeometryNone, QueryMultiPartToSinglePart,
    QueryPolygonToLine, QueryRepairGeometry, QuerySplitLineAtVertices,
    QueryXYTableLine, QueryXYTablePoint)
from spyops.shared.enumeration import (
    GeometryAttribute, MinimumGeometryOption, PointTypeOption, WeightOption)
from spyops.shared.field import (
    ORIG_FID, ORIG_SEQ, POINT_M, POINT_X, POINT_Y, POINT_Z)


pytestmark = [mark.features, mark.query, mark.management]


class TestQueryMultiPartToSinglePart:
    """
    Tests for QueryMultiPartToSinglePart
    """
    @mark.parametrize('source_name, names', [
        ('updater_a', ('ORIG_FID', 'ID', 'NAME')),
        ('orig_fid_a', ('ORIG_FID', 'ID', 'NAME', 'orig_FID_2', 'ORIG_FID_1')),
    ])
    def test_target_fields(self, inputs, mem_gpkg, source_name, names):
        """
        Test Target Fields
        """
        source = inputs[source_name]
        target = FeatureClass(geopackage=mem_gpkg, name='asdf')
        query = QueryMultiPartToSinglePart(source, target=target)
        field_names = tuple(f.name for f in query._get_unique_fields())
        assert field_names == names
    # End test_target_fields method

    @mark.parametrize('source_name, sql', [
        ('updater_a', 'SELECT SHAPE "[Polygon]", fid, ID, NAME'),
        ('orig_fid_a', 'SELECT geom "[Polygon]", fid, ID, NAME, orig_FID, ORIG_FID_1'),
    ])
    def test_select_source(self, inputs, mem_gpkg, source_name, sql):
        """
        Test select source SQL
        """
        source = inputs[source_name]
        target = FeatureClass(geopackage=mem_gpkg, name='asdf')
        query = QueryMultiPartToSinglePart(source, target=target)
        assert sql in query.select
    # End test_select_source method

    @mark.parametrize('source_name, sql', [
        ('updater_a', 'INTO asdf(SHAPE, ORIG_FID, ID, NAME'),
        ('orig_fid_a', 'INTO asdf(SHAPE, ORIG_FID, ID, NAME, orig_FID_2, ORIG_FID_1'),
    ])
    def test_insert_target(self, inputs, mem_gpkg, source_name, sql):
        """
        Test insert target SQL
        """
        source = inputs[source_name]
        target = FeatureClass(geopackage=mem_gpkg, name='asdf')
        query = QueryMultiPartToSinglePart(source, target=target)
        assert sql in query.insert
    # End test_insert_target method

    def test_source_extent(self, world_features, mem_gpkg):
        """
        Test source extent
        """
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name='test_target')
        query = QueryMultiPartToSinglePart(source=source, target=target)
        assert approx(query._shared_extent(query.source), abs=0.001) == (-180, -90, 180, 83.6654)
        with Swap(Setting.EXTENT, Extent.from_bounds(-100, -60, 100, 90, CRS(4326))):
            assert approx(query._shared_extent(query.source), abs=0.001) == (-100, -60, 100, 83.6654)
            assert '100' in query.select
            assert '-100' in query.select
            assert '-60' in query.select
            assert '83.665' in query.select
    # End test_source_extent method
# End TestQueryMultiPartToSinglePart class


class TestQueryAddXYCoordinates:
    """
    Tests for QueryAddXYCoordinates
    """
    def test_delete_intermediate(self, grid_index):
        """
        Test delete intermediate
        """
        name = 'grid_a'
        source = grid_index[name]
        query = QueryAddXYCoordinates(source, WeightOption.TWO_D)
        with query.source.geopackage.connection as cin:
            query._delete_intermediate()
            name = query._intermediate_table
            assert name.startswith('temp.tmp_grid_a_add_xy_coords_')
            sql = f"""SELECT * FROM {name}"""
            cin.execute(sql)
            query._delete_intermediate()
            with raises(OperationalError):
                cin.execute(sql)
    # End test_delete_intermediate method

    @mark.parametrize('name, count', [
        ('grid_a', 3),
        ('grid_z_a', 4),
        ('grid_m_a', 4),
        ('grid_zm_a', 5),
    ])
    def test_intermediate_fields(self, grid_index, name, count):
        """
        Test intermediate fields
        """
        source = grid_index[name]
        query = QueryAddXYCoordinates(source, WeightOption.TWO_D)
        assert len(query._intermediate_fields) == count
    # End test_intermediate_fields method

    def test_prepare_source(self, grid_index, mem_gpkg):
        """
        Test prepare source
        """
        name = 'grid_a'
        source = grid_index[name].copy(name, geopackage=mem_gpkg)
        assert len(source.fields) == 10
        source.add_fields((POINT_X, POINT_Y, POINT_Z, POINT_M))
        assert len(source.fields) == 14
        query = QueryAddXYCoordinates(source, WeightOption.TWO_D)
        query._prepare_source()
        assert len(source.fields) == 12
        names = source.field_names
        assert POINT_X.name in names
        assert POINT_Y.name in names
        assert POINT_Z.name not in names
        assert POINT_M.name not in names
    # End test_prepare_source method

    def test_select(self, grid_index):
        """
        Test select statement
        """
        name = 'grid_zm_a'
        source = grid_index[name]
        query = QueryAddXYCoordinates(source, WeightOption.TWO_D)
        sql = query.select
        assert 'SELECT geom "[PolygonZM]", fid' in sql
        assert f'FROM {name}' in sql
    # End test_select method

    def test_insert(self, grid_index):
        """
        Test insert statement
        """
        name = 'grid_zm_a'
        source = grid_index[name]
        query = QueryAddXYCoordinates(source, WeightOption.TWO_D)
        sql = query.insert
        assert '(ORIG_FID, POINT_X, POINT_Y, POINT_Z, POINT_M) ' in sql
        assert f'temp.tmp_{name}' in sql
    # End test_insert method

    def test_update(self, grid_index):
        """
        Test update statement
        """
        name = 'grid_zm_a'
        source = grid_index[name]
        query = QueryAddXYCoordinates(source, WeightOption.TWO_D)
        sql = query.update
        assert 'UPDATE grid_zm_a ' in sql
        assert 'WHERE grid_zm_a.fid = temp.tmp_grid_zm_a_' in sql
    # End test_update method
# End TestQueryAddXYCoordinates class


class TestQueryCalculateGeometryAttributes:
    """
    Tests for QueryCalculateGeometryAttributes
    """
    def test_delete_intermediate(self, grid_index):
        """
        Test delete intermediate
        """
        name = 'grid_a'
        source = grid_index[name]
        query = QueryCalculateGeometryAttributes(
            source, field=Field('left', data_type=FieldType.real),
            geometry_attribute=GeometryAttribute.POINT_M,
            weight_option=WeightOption.TWO_D, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        with query.source.geopackage.connection as cin:
            query._delete_intermediate()
            name = query._intermediate_table
            assert name.startswith('temp.tmp_grid_a_calc_geom_attrs_')
            sql = f"""SELECT * FROM {name}"""
            cin.execute(sql)
            query._delete_intermediate()
            with raises(OperationalError):
                cin.execute(sql)
    # End test_delete_intermediate method

    @mark.parametrize('name, count', [
        ('grid_a', 2),
        ('grid_z_a', 2),
        ('grid_m_a', 2),
        ('grid_zm_a', 2),
    ])
    def test_intermediate_fields(self, grid_index, name, count):
        """
        Test intermediate fields
        """
        source = grid_index[name]
        query = QueryCalculateGeometryAttributes(
            source, field=Field('left', data_type=FieldType.real),
            geometry_attribute=GeometryAttribute.POINT_M,
            weight_option=WeightOption.TWO_D, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        assert len(query._intermediate_fields) == count
    # End test_intermediate_fields method

    def test_prepare_source(self, grid_index, mem_gpkg):
        """
        Test prepare source
        """
        name = 'grid_a'
        source = grid_index[name].copy(name, geopackage=mem_gpkg)
        assert len(source.fields) == 10
        query = QueryCalculateGeometryAttributes(
            source, field=Field('left', data_type=FieldType.real),
            geometry_attribute=GeometryAttribute.POINT_M,
            weight_option=WeightOption.TWO_D, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        query._prepare_source()
        assert len(source.fields) == 10
    # End test_prepare_source method

    def test_select(self, grid_index):
        """
        Test select statement
        """
        name = 'grid_zm_a'
        source = grid_index[name]
        query = QueryCalculateGeometryAttributes(
            source, field=Field('left', data_type=FieldType.real),
            geometry_attribute=GeometryAttribute.POINT_M,
            weight_option=WeightOption.TWO_D, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        sql = query.select
        assert 'SELECT geom "[PolygonZM]", fid' in sql
        assert f'FROM {name}' in sql
    # End test_select method

    def test_insert(self, grid_index):
        """
        Test insert statement
        """
        name = 'grid_zm_a'
        source = grid_index[name]
        query = QueryCalculateGeometryAttributes(
            source, field=Field('left', data_type=FieldType.real),
            geometry_attribute=GeometryAttribute.POINT_M,
            weight_option=WeightOption.TWO_D, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        sql = query.insert
        assert '(ORIG_FID, VALUE) ' in sql
        assert f'temp.tmp_{name}' in sql
    # End test_insert method

    def test_update(self, grid_index):
        """
        Test update statement
        """
        name = 'grid_zm_a'
        source = grid_index[name]
        query = QueryCalculateGeometryAttributes(
            source, field=Field('left', data_type=FieldType.real),
            geometry_attribute=GeometryAttribute.POINT_M,
            weight_option=WeightOption.TWO_D, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        sql = query.update
        assert 'UPDATE grid_zm_a ' in sql
        assert 'SET "left" = temp.tmp_grid_zm_a_' in sql
        assert 'WHERE grid_zm_a.fid = temp.tmp_grid_zm_a_' in sql
    # End test_update method
# End TestQueryCalculateGeometryAttributes class


class TestQueryCheckGeometry:
    """
    Test QueryCheckGeometry
    """
    def test_target(self, world_features, mem_gpkg):
        """
        Test target
        """
        source = world_features['admin_a']
        name = 'geom_check'
        target = Table(geopackage=mem_gpkg, name=name)
        query = QueryCheckGeometry(source, target, xy_tolerance=None)
        assert query.target.name == name
        assert len(query.target.fields) == 3
        assert query.target.field_names == ['fid', 'ORIG_FID', 'REASON']
    # End test_target method

    @mark.parametrize('xy_tolerance', [
        None,
        0.001
    ])
    def test_grid_size(self, world_features, mem_gpkg, xy_tolerance):
        """
        Test grid size
        """
        source = world_features['admin_a']
        name = 'geom_check'
        target = Table(geopackage=mem_gpkg, name=name)
        query = QueryCheckGeometry(source, target, xy_tolerance=xy_tolerance)
        assert query.grid_size == xy_tolerance
    # End test_grid_size method

    def test_insert(self, world_features, mem_gpkg):
        """
        Test insert
        """
        source = world_features['admin_a']
        name = 'geom_check'
        target = Table(geopackage=mem_gpkg, name=name)
        query = QueryCheckGeometry(source, target, xy_tolerance=None)
        sql = query.insert
        assert name in sql
        assert '(ORIG_FID, REASON)' in sql
    # End test_insert method
# End TestQueryCheckGeometry class


class TestQueryRepairGeometry:
    """
    Test QueryRepairGeometry
    """
    def test_insert(self, world_features):
        """
        Test insert
        """
        source = world_features['admin_a']
        query = QueryRepairGeometry(source)
        sql = query.insert
        assert '(ORIG_FID, SHAPE)' in sql
    # End test_insert method

    def test_insert_identifiers(self, world_features):
        """
        Test insert identifiers
        """
        source = world_features['admin_a']
        query = QueryRepairGeometry(source)
        sql = query.insert_identifiers
        assert '(ORIG_FID)' in sql
    # End test_insert_identifiers method

    def test_update(self, world_features):
        """
        Test update query
        """
        source = world_features['admin_a']
        query = QueryRepairGeometry(source)
        sql = query.update
        assert 'SET SHAPE = ' in sql
        assert '.SHAPE' in sql
        assert 'FROM temp.tmp_admin_a_repair_geom_20' in sql
    # End test_update method

    def test_drop_empty(self, world_features):
        """
        Test drop_empty
        """
        source = world_features['admin_a']
        query = QueryRepairGeometry(source)
        sql = query.drop_empty
        assert 'WHERE fid IN (' in sql
        assert 'SELECT ORIG_FID FROM temp.tmp_admin_a_repair_geom_20' in sql
    # End test_drop_empty method

    def test_truncate(self, world_features):
        """
        Test truncate
        """
        source = world_features['admin_a']
        query = QueryRepairGeometry(source)
        sql = query.truncate
        assert 'DELETE FROM temp.tmp_admin_a_repair_geom_20' in sql
    # End test_truncate method
# End TestQueryRepairGeometry class


class TestQueryXYTablePoint:
    """
    Test Query XY Table Point
    """
    def test_get_target_shape_type(self):
        """
        Test Get Target Shape Type
        """
        query = QueryXYTablePoint(None, None, fields=(), coordinate_system=None)
        assert query._get_target_shape_type() == 'POINT'
    # End test_get_target_shape_type method

    @mark.parametrize('fields, expected', [
        ((POINT_X, POINT_Y, None, None), Point),
        ((POINT_X, POINT_Y, POINT_Z, None), PointZ),
        ((POINT_X, POINT_Y, None, POINT_M), PointM),
        ((POINT_X, POINT_Y, POINT_Z, POINT_M), PointZM),
    ])
    def test_point_class(self, fields, expected):
        """
        Test point class
        """
        query = QueryXYTablePoint(None, None, fields=fields, coordinate_system=None)
        assert query.point_class is expected
    # End test_point_class method

    @mark.parametrize('fields, expected', [
        ((POINT_X, POINT_Y, None, None), (10, 11)),
        ((POINT_X, POINT_Y, POINT_Z, None), (10, 11, 12)),
        ((POINT_X, POINT_Y, None, POINT_M), (10, 11, 13)),
        ((POINT_X, POINT_Y, POINT_Z, POINT_M), (10, 11, 12, 13)),
    ])
    def test_item_getter(self, inputs, fields, expected):
        """
        Test item getter
        """
        source = inputs['xyzm_table']
        query = QueryXYTablePoint(
            source, None, fields=fields, coordinate_system=None)
        assert query.item_getter(range(len(source.fields))) == expected
    # End test_item_getter method

    def test_select(self, inputs):
        """
        Test Select
        """
        source = inputs['xyzm_table']
        query = QueryXYTablePoint(
            source, None, fields=(), coordinate_system=None)
        sql = query.select
        select = """SELECT FEATURE_ID, PART_ID, ENTITY, ENTITY_NAME, """
        more = """VALDATE, PROVIDER, DATANAME, ACCURACY, FILE_NAME, """
        plus = """CODE, POINT_X, POINT_Y, POINT_Z, POINT_M"""
        assert select in sql
        assert more in sql
        assert plus in sql
        assert 'FROM xyzm_table' in sql
        assert 'WHERE ROWID > -1' in sql
    # End test_select method

    def test_insert(self, inputs, mem_gpkg):
        """
        Test Insert
        """
        source = inputs['xyzm_table']
        target = FeatureClass(geopackage=mem_gpkg, name='asdf')
        fields = POINT_X, POINT_Y, POINT_Z, POINT_M
        crs = CRS(4326)
        query = QueryXYTablePoint(
            source, target=target, fields=fields, coordinate_system=crs)
        sql = query.insert
        insert = """ INTO asdf(SHAPE, FEATURE_ID, PART_ID, ENTITY, ENTITY_NAME, """
        more = """VALDATE, PROVIDER, DATANAME, ACCURACY, FILE_NAME, """
        plus = """CODE, POINT_X, POINT_Y, POINT_Z, POINT_M)"""
        assert insert in sql
        assert more in sql
        assert plus in sql
    # End test_insert method

    def test_source_transformer(self, inputs, mem_gpkg):
        """
        Test source transformer
        """
        source = inputs['xyzm_table']
        target = FeatureClass(geopackage=mem_gpkg, name='asdf')
        fields = POINT_X, POINT_Y, POINT_Z, POINT_M
        crs = CRS(4617)
        query = QueryXYTablePoint(
            source, target=target, fields=fields, coordinate_system=crs)
        assert query.source_transformer is None

        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(4326)):
            query = QueryXYTablePoint(
                source, target=target, fields=fields, coordinate_system=crs)
            assert query.source_transformer is not None
    # End test_source_transformer method

    def test_filter_extent(self):
        """
        Test filter extent
        """
        crs = CRS(4617)
        query = QueryXYTablePoint(
            None, target=None, fields=(), coordinate_system=crs)
        assert query.filter_extent is None
        with Swap(Setting.EXTENT, Extent.from_bounds(-100, -60, 100, 90, CRS(4326))):
            assert approx(query.filter_extent.bounds, abs=1e-6) == (
                -99.9999731, -60.0000257, 99.9999828, 89.999988)
    # End test_filter_extent method
# End TestQueryXYTablePoint class


class TestQueryXYTableLine:
    """
    Test Query XY Table Line
    """
    def test_get_target_shape_type(self):
        """
        Test Get Target Shape Type
        """
        query = QueryXYTableLine(None, None, fields=(), coordinate_system=None)
        assert query._get_target_shape_type() == 'LINESTRING'
    # End test_get_target_shape_type method

    def test_item_getter(self, inputs):
        """
        Test item getter
        """
        fields = (
            Field('START_X', data_type=FieldType.real),
            Field('START_Y', data_type=FieldType.real),
            Field('END_X', data_type=FieldType.real),
            Field('END_Y', data_type=FieldType.real),
        )
        source = inputs['transmission_xy_4617']
        query = QueryXYTableLine(
            source, None, fields=fields, coordinate_system=None)
        assert query.item_getter(range(len(source.fields))) == (10, 11, 12, 13)
    # End test_item_getter method

    def test_select(self, inputs):
        """
        Test Select
        """
        source = inputs['transmission_xy_4617']
        query = QueryXYTableLine(
            source, None, fields=(), coordinate_system=None)
        sql = query.select
        select = """SELECT FEATURE_ID, PART_ID, ENTITY, ENTITY_NAME, """
        more = """VALDATE, PROVIDER, DATANAME, ACCURACY, FILE_NAME, """
        plus = """CODE, START_X, START_Y, END_X, END_Y"""
        assert select in sql
        assert more in sql
        assert plus in sql
        assert 'FROM transmission_xy_4617' in sql
        assert 'WHERE ROWID > -1' in sql
    # End test_select method

    def test_insert(self, inputs, mem_gpkg):
        """
        Test Insert
        """
        source = inputs['transmission_xy_4617']
        target = FeatureClass(geopackage=mem_gpkg, name='asdf')
        fields = (
            Field('START_X', data_type=FieldType.real),
            Field('START_Y', data_type=FieldType.real),
            Field('END_X', data_type=FieldType.real),
            Field('END_Y', data_type=FieldType.real),
        )
        crs = CRS(4326)
        query = QueryXYTablePoint(
            source, target=target, fields=fields, coordinate_system=crs)
        sql = query.insert
        insert = """ INTO asdf(SHAPE, FEATURE_ID, PART_ID, ENTITY, ENTITY_NAME, """
        more = """VALDATE, PROVIDER, DATANAME, ACCURACY, FILE_NAME, """
        plus = """CODE, START_X, START_Y, END_X, END_Y)"""
        assert insert in sql
        assert more in sql
        assert plus in sql
    # End test_insert method

    def test_source_transformer(self, inputs, mem_gpkg):
        """
        Test source transformer
        """
        source = inputs['xyzm_table']
        target = FeatureClass(geopackage=mem_gpkg, name='asdf')
        fields = POINT_X, POINT_Y, POINT_Z, POINT_M
        crs = CRS(4617)
        query = QueryXYTablePoint(
            source, target=target, fields=fields, coordinate_system=crs)
        assert query.source_transformer is None
    # End test_source_transformer method

    def test_filter_extent(self):
        """
        Test filter extent
        """
        crs = CRS(4617)
        query = QueryXYTablePoint(
            None, target=None, fields=(), coordinate_system=crs)
        assert query.filter_extent is None
    # End test_filter_extent method
# End TestQueryXYTableLine class


class TestQueryFeatureEnvelopeToPolygon:
    """
    Test QueryFeatureEnvelopeToPolygon
    """
    @mark.parametrize('fc_name, as_multi_part, shape_type', [
        ('hydro_a', True, ShapeType.multi_polygon),
        ('hydro_a', False, ShapeType.polygon),
        ('transmission_ml', True, ShapeType.multi_polygon),
        ('transmission_ml', False, ShapeType.polygon),
        ('transmission_mp', True, ShapeType.polygon),
        ('transmission_mp', False, ShapeType.polygon),
    ])
    def test_get_target_shape_type(self, ntdb_zm_small, fc_name, as_multi_part, shape_type):
        """
        Test get_target_shape_type
        """
        source = ntdb_zm_small[fc_name]
        query = QueryFeatureEnvelopeToPolygon(
            source, None, as_multi_part=as_multi_part)
        assert query._get_target_shape_type() == shape_type
    # End test_get_target_shape_type method

    @mark.parametrize('fc_name, expected', [
        ('hydro_a', (False, False, False)),
        ('hydro_m_a', (True, False, True)),
        ('hydro_z_a', (True, True, False)),
        ('hydro_zm_a', (True, True, True)),
    ])
    def test_zm_config(self, ntdb_zm_small, fc_name, expected):
        """
        Test zm_config
        """
        source = ntdb_zm_small[fc_name]
        query = QueryFeatureEnvelopeToPolygon(
            source, None, as_multi_part=True)
        assert query.zm_config == expected
    # End test_zm_config method
# End TestQueryFeatureEnvelopeToPolygon class


class TestQueryMinimumBoundingGeometryList:
    """
    Test QueryMinimumBoundingGeometryList
    """
    def test_get_target_shape_type(self):
        """
        Test _get_target_shape_type
        """
        query = QueryMinimumBoundingGeometryList(
            None, None, geometry_type=MinimumGeometryOption.CONVEX_HULL,
            add_geometric_attributes=True, fields=())
        assert query._get_target_shape_type() == ShapeType.polygon
    # End test_get_target_shape_type method

    @mark.parametrize('add_attributes, expected', [
        (True, ['MBG_WIDTH', 'MBG_LENGTH', 'MBG_ORIENTATION', 'COUNTRY']),
        (False, ['COUNTRY'])
    ])
    def test_get_unique_fields(self, add_attributes, expected):
        """
        Test _get_unique_fields
        """
        fields = [Field('COUNTRY', data_type=FieldType.text)]
        query = QueryMinimumBoundingGeometryList(
            None, None, geometry_type=MinimumGeometryOption.CONVEX_HULL,
            add_geometric_attributes=add_attributes, fields=fields)
        assert [f.name for f in query._get_unique_fields()] == expected
    # End test_get_unique_fields method

    def test_select(self, buffering):
        """
        Test select
        """
        source = buffering['admin_a']
        fields = [Field('COUNTRY', data_type=FieldType.text)]
        query = QueryMinimumBoundingGeometryList(
            source, None, geometry_type=MinimumGeometryOption.CONVEX_HULL,
            add_geometric_attributes=True, fields=fields
        )
        sql = query.select
        assert 'ORDER BY COUNTRY) AS __DRID__, COUNTRY' in sql
        assert 'MBG' not in sql
    # End test_select method

    def test_select_geometry(self, buffering):
        """
        Test select geometry
        """
        fields = [Field('COUNTRY', data_type=FieldType.text)]
        source = buffering['admin_a']
        query = QueryMinimumBoundingGeometryList(
            source, None, geometry_type=MinimumGeometryOption.CONVEX_HULL,
            add_geometric_attributes=True, fields=fields)
        sql = query.select_geometry
        assert 'FROM (SELECT geom "[Polygon]", dense_rank() OVER (' in sql
        assert 'MBG' not in sql
    # End test_select_geometry method
# End TestQueryMinimumBoundingGeometryList class


class TestQueryMinimumBoundingGeometryAll:
    """
    Test QueryMinimumBoundingGeometryAll
    """
    @mark.parametrize('add_attributes, expected', [
        (True, ['MBG_WIDTH', 'MBG_LENGTH', 'MBG_ORIENTATION']),
        (False, [])
    ])
    def test_get_unique_fields(self, add_attributes, expected):
        """
        Test _get_unique_fields
        """
        query = QueryMinimumBoundingGeometryAll(
            None, None, geometry_type=MinimumGeometryOption.CONVEX_HULL,
            add_geometric_attributes=add_attributes, fields=[])
        assert [f.name for f in query._get_unique_fields()] == expected
    # End test_get_unique_fields method

    def test_select(self):
        """
        Test select
        """
        query = QueryMinimumBoundingGeometryAll(
            None, None, geometry_type=MinimumGeometryOption.CONVEX_HULL,
            add_geometric_attributes=True, fields=[])
        sql = query.select
        assert not sql
        assert 'MBG' not in sql
    # End test_select method

    def test_select_geometry(self, buffering):
        """
        Test select geometry
        """
        source = buffering['admin_a']
        query = QueryMinimumBoundingGeometryAll(
            source, None, geometry_type=MinimumGeometryOption.CONVEX_HULL,
            add_geometric_attributes=True, fields=[])
        sql = query.select_geometry
        assert 'SELECT geom "[Polygon]"' in sql
        assert 'MBG' not in sql
    # End test_select_geometry method
# End TestQueryMinimumBoundingGeometryAll class


class TestQueryMinimumBoundingGeometryNone:
    """
    Test QueryMinimumBoundingGeometryNone
    """
    @mark.parametrize('add_attributes, expected', [
        (True, ['ORIG_FID', 'MBG_WIDTH', 'MBG_LENGTH', 'MBG_ORIENTATION',
                'FEATURE_ID', 'PART_ID', 'COUNTRY', 'ISO_CODE',
                'ISO_CC', 'ISO_SUB', 'ADMINTYPE', 'CONTINENT', 'LAND_TYPE',
                'LAND_RANK', 'NUM_DIST', 'LIN_UNIT', 'ANG_UNIT', 'MIX_UNIT']),
        (False, ['ORIG_FID', 'FEATURE_ID', 'PART_ID', 'COUNTRY', 'ISO_CODE',
                 'ISO_CC', 'ISO_SUB', 'ADMINTYPE', 'CONTINENT', 'LAND_TYPE',
                 'LAND_RANK', 'NUM_DIST', 'LIN_UNIT', 'ANG_UNIT', 'MIX_UNIT'])
    ])
    def test_get_unique_fields(self, buffering, add_attributes, expected):
        """
        Test _get_unique_fields
        """
        source = buffering['admin_a']
        query = QueryMinimumBoundingGeometryNone(
            source, None, geometry_type=MinimumGeometryOption.CONVEX_HULL,
            add_geometric_attributes=add_attributes, fields=[])
        assert [f.name for f in query._get_unique_fields()] == expected
    # End test_get_unique_fields method

    def test_select(self, buffering):
        """
        Test select
        """
        source = buffering['admin_a']
        query = QueryMinimumBoundingGeometryNone(
            source, None, geometry_type=MinimumGeometryOption.CONVEX_HULL,
            add_geometric_attributes=True, fields=[])
        sql = query.select
        assert 'SELECT fid, fid, FEATURE_ID, PART_ID, COUNTRY, ISO_CODE, ' in sql
    # End test_select method

    def test_select_geometry(self, buffering):
        """
        Test select geometry
        """
        fields = [Field('COUNTRY', data_type=FieldType.text)]
        source = buffering['admin_a']
        query = QueryMinimumBoundingGeometryNone(
            source, None, geometry_type=MinimumGeometryOption.CONVEX_HULL,
            add_geometric_attributes=True, fields=fields)
        sql = query.select_geometry
        assert 'SELECT geom "[Polygon]", fid' in sql
    # End test_select_geometry method
# End TestQueryMinimumBoundingGeometryNone class


class TestQueryFeatureToPoint:
    """
    Test QueryFeatureToPoint
    """
    def test_get_unique_fields(self, world_features):
        """
        Test get unique fields
        """
        source = world_features['admin_sans_attr_a']
        query = QueryFeatureToPoint(
            source, None, inside=False, weight_option=WeightOption.TWO_D)
        assert [f.name for f in query._get_unique_fields()] == [ORIG_FID.name]
    # End test_get_unique_fields method

    def test_get_target_shape_type(self, world_features):
        """
        Test get target shape type
        """
        source = world_features['admin_a']
        query = QueryFeatureToPoint(
            source, None, inside=False, weight_option=WeightOption.TWO_D)
        assert query._get_target_shape_type() == ShapeType.point
    # End test_get_target_shape_type method

    @mark.parametrize('inside', [
        True,
        False,
    ])
    def test_coordinate_getter(self, world_features, inside):
        """
        Test Coordinate Getter
        """
        source = world_features['admin_a']
        query = QueryFeatureToPoint(
            source, None, inside=inside, weight_option=WeightOption.TWO_D)
        assert isinstance(query.coordinate_getter, Callable)
    # End test_coordinate_getter method

    @mark.parametrize('inside', [
        True,
        False,
    ])
    def test_zm_config(self, world_features, inside):
        """
        Test ZM Config
        """
        source = world_features['admin_a']
        query = QueryFeatureToPoint(
            source, None, inside=inside, weight_option=WeightOption.TWO_D)
        assert not query.zm_config.is_different
    # End test_zm_config method
# End TestQueryFeatureToPoint class


class TestQueryFeatureVerticesToPoints:
    """
    Test QueryFeatureVerticesToPoints
    """
    def test_get_unique_fields(self, world_features):
        """
        Test get unique fields
        """
        source = world_features['admin_sans_attr_a']
        query = QueryFeatureVerticesToPoints(
            source, None, point_type=PointTypeOption.MID)
        assert [f.name for f in query._get_unique_fields()] == [ORIG_FID.name]
    # End test_get_unique_fields method

    def test_get_target_shape_type(self, world_features):
        """
        Test get target shape type
        """
        source = world_features['admin_a']
        query = QueryFeatureVerticesToPoints(
            source, None, point_type=PointTypeOption.MID)
        assert query._get_target_shape_type() == ShapeType.point
    # End test_get_target_shape_type method

    @mark.parametrize('point_type', [
        PointTypeOption.ALL,
        PointTypeOption.MID,
        PointTypeOption.START,
        PointTypeOption.END,
        PointTypeOption.BOTH_ENDS
    ])
    def test_vertex_getter(self, world_features, point_type):
        """
        Test Vertex Getter
        """
        source = world_features['admin_a']
        query = QueryFeatureVerticesToPoints(
            source, None, point_type=point_type)
        assert isinstance(query.vertex_getter, Callable)
    # End test_vertex_getter method
# End TestQueryFeatureVerticesToPoints class


class TestQuerySplitLineAtVertices:
    """
    Test QuerySplitLineAtVertices
    """
    def test_get_unique_fields(self, world_features):
        """
        Test get unique fields
        """
        source = world_features['admin_sans_attr_a']
        query = QuerySplitLineAtVertices(source, None)
        assert [f.name for f in query._get_unique_fields()] == [ORIG_FID.name, ORIG_SEQ.name]
    # End test_get_unique_fields method

    def test_get_target_shape_type(self, world_features):
        """
        Test get target shape type
        """
        source = world_features['admin_a']
        query = QuerySplitLineAtVertices(source, None)
        assert query._get_target_shape_type() == ShapeType.linestring
    # End test_get_target_shape_type method

    @mark.parametrize('fc_name', [
        'admin_a',
        'admin_mp_a',
        'roads_l',
        'roads_ml',
    ])
    def test_segment_getter(self, world_features, fc_name):
        """
        Test Segment Getter
        """
        source = world_features[fc_name]
        query = QuerySplitLineAtVertices(source, None)
        assert isinstance(query.segment_getter, Callable)
    # End test_segment_getter method
# End TestQuerySplitLineAtVertices class


class TestQueryPolygonToLine:
    """
    Test QueryPolygonToLine
    """
    def test_get_unique_fields(self, world_features):
        """
        Test get unique fields
        """
        source = world_features['admin_sans_attr_a']
        query = QueryPolygonToLine(source, None)
        assert [f.name for f in query._get_unique_fields()] == [ORIG_FID.name]
    # End test_get_unique_fields method

    def test_get_target_shape_type(self, world_features):
        """
        Test get target shape type
        """
        source = world_features['admin_a']
        query = QueryPolygonToLine(source, None)
        assert query._get_target_shape_type() == ShapeType.linestring
    # End test_get_target_shape_type method

    @mark.parametrize('fc_name', [
        'admin_a',
        'admin_mp_a',
    ])
    def test_part_getter(self, world_features, fc_name):
        """
        Test Part Getter
        """
        source = world_features[fc_name]
        query = QueryPolygonToLine(source, None)
        assert isinstance(query.polygon_getter, Callable)
    # End test_part_getter method
# End TestQueryPolygonToLine class


class TestQueryFeatureToPolygonPrepare:
    """
    Test QueryFeatureToPolygonPrepare
    """
    def _shared_query(self, inputs, mem_gpkg):
        source = inputs['int_flavor_a']
        target = FeatureClass(mem_gpkg, name=source.name)
        return QueryFeatureToPrepare(
            source, target=target, xy_tolerance=10 ** -6)
    # End _shared_query method

    def test_select(self, inputs, mem_gpkg):
        """
        Test select
        """
        query = self._shared_query(inputs, mem_gpkg)
        sql = query.select
        assert 'SELECT geom "[MultiPolygon]"' in sql
        assert 'FROM int_flavor_a' in sql
        assert 'WHERE ROWID > -1' in sql
    # End test_select method

    def test_insert(self, inputs, mem_gpkg):
        """
        Test insert
        """
        query = self._shared_query(inputs, mem_gpkg)
        sql = query.insert
        assert 'INTO int_flavor_a(SHAPE)' in sql
        assert 'VALUES (?)' in sql
    # End test_insert method

    def test_source_transformer(self, inputs, mem_gpkg):
        """
        Test source transformer
        """
        query = self._shared_query(inputs, mem_gpkg)
        assert query.source_transformer is None
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(6654)):
            query = self._shared_query(inputs, mem_gpkg)
            assert query.source_transformer is not None
    # End test_source_transformer method

    def test_target(self, inputs, mem_gpkg):
        """
        Test Target
        """
        query = self._shared_query(inputs, mem_gpkg)
        assert isinstance(query.target, FeatureClass)
    # End test_target method

    def test_geometry_config(self, inputs, mem_gpkg):
        """
        Test geometry config
        """
        query = self._shared_query(inputs, mem_gpkg)
        assert isinstance(query.geometry_config, GeometryConfig)
    # End test_geometry_config method

    def test_grid_size(self, inputs, mem_gpkg):
        """
        Test grid size
        """
        query = self._shared_query(inputs, mem_gpkg)
        assert query.grid_size == 10**-6
    # End test_grid_size method
# End TestQueryFeatureToPolygonPrepare class


class TestQueryFeatureToPolygon:
    """
    Test QueryFeatureToPolygon
    """
    def test_get_target_shape_type(self):
        """
        Test get target shape type
        """
        query = QueryFeatureToPolygon([None], None, None, None)
        assert query._get_target_shape_type() == ShapeType.polygon
    # End test_get_target_shape_type method

    def test_spatial_reference_system(self, inputs, mem_gpkg):
        """
        Test spatial reference system
        """
        source = inputs['int_flavor_a']
        target = FeatureClass(mem_gpkg, name='polygons_a')
        query = QueryFeatureToPolygon([source], target, None, None)
        srs = source.spatial_reference_system
        assert query.spatial_reference_system == srs
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(6654)):
            query = QueryFeatureToPolygon([source], target, None, None)
            assert query.spatial_reference_system != srs
    # End test_spatial_reference_system method

    @mark.parametrize('names, z_enabled, m_enabled', [
        (('hydro_4617_a', 'hydro_a'), False, False),
        (('hydro_4617_zm_a', 'hydro_a'), True, True),
        (('hydro_4617_m_a', 'hydro_a'), False, True),
    ])
    def test_zm_config(self, ntdb_zm_small, names, z_enabled, m_enabled):
        """
        Test ZM config and has zm
        """
        source = [ntdb_zm_small[n] for n in names]
        query = QueryFeatureToPolygon(source, None, None, None)
        assert query.zm_config.z_enabled is z_enabled
        assert query.zm_config.m_enabled is m_enabled
        assert query._has_zm == (z_enabled, m_enabled)
    # End test_zm_config method

    @mark.parametrize('fc_name, expected', [
        ('<does not exist>', []),
        ('structures_4617_zm_p', ['ENTITY', 'ENTITY_NAME', 'VALDATE', 'PROVIDER', 'DATANAME', 'ACCURACY', 'FILE_NAME', 'CODE']),
    ])
    def test_get_unique_fields(self, ntdb_zm_small, fc_name, expected):
        """
        Test get unique fields
        """
        label = ntdb_zm_small[fc_name]
        query = QueryFeatureToPolygon([None], None, label, None)
        fields = query._get_unique_fields()
        assert [f.name for f in fields] == expected
    # End test_get_unique_fields method

    @mark.parametrize('fc_name, expected', [
        ('<does not exist>', ()),
        ('structures_4617_zm_p', (None, None, None, None, None, None, None, None)),
    ])
    def test_get_null_record(self, ntdb_zm_small, fc_name, expected):
        """
        Get Null Record
        """
        label = ntdb_zm_small[fc_name]
        query = QueryFeatureToPolygon([None], None, label, None)
        assert query._get_null_record() == expected
    # End test_get_null_record method

    @mark.parametrize('fc_name, expected', [
        ('<does not exist>', 'INTO polygons_a(SHAPE)'),
        ('structures_4617_zm_p', 'INTO polygons_a(SHAPE, ENTITY, ENTITY_NAME, VALDATE'),
    ])
    def test_insert(self, mem_gpkg, ntdb_zm_small, fc_name, expected):
        """
        Test insert
        """
        source = [ntdb_zm_small['hydro_a']]
        label = ntdb_zm_small[fc_name]
        target = FeatureClass(mem_gpkg, name='polygons_a')
        query = QueryFeatureToPolygon(source, target, label, None)
        assert expected in query.insert
    # End test_insert method

    @mark.parametrize('code, xy', [
        (4617, (-114.0575, 51.0373)),
        (6654, (706283.9953, 5658093.1593)),
    ])
    def test_get_points_attributes(self, ntdb_zm_small, mem_gpkg, code, xy):
        """
        Test get points attributes
        """
        source = [ntdb_zm_small['hydro_a']]
        label = ntdb_zm_small['structures_4617_zm_p']
        target = FeatureClass(mem_gpkg, name='polygons_a')
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(code)):
            query = QueryFeatureToPolygon(source, target, label, None)
            points, attributes = query._get_points_attributes()
            assert len(points) == len(attributes)
            assert len(points) == 3912
            point, *_ = points
            assert approx((point.x, point.y), abs=0.001) == xy
    # End test_get_points_attributes method

    def test_get_points_attributes_sans_label(self, ntdb_zm_small, mem_gpkg):
        """
        Test get points attributes sans label
        """
        source = [ntdb_zm_small['hydro_a']]
        target = FeatureClass(mem_gpkg, name='polygons_a')
        query = QueryFeatureToPolygon(source, target, None, None)
        points, attributes = query._get_points_attributes()
        assert len(points) == len(attributes)
        assert len(points) == 0
    # End test_get_points_attributes_sans_label method

    @mark.parametrize('xy_tol, count', [
        (None, 8572),
        (10**-5, 8695),
    ])
    def test_get_lines(self, ntdb_zm_small, mem_gpkg, xy_tol, count):
        """
        Test get lines
        """
        names = ['topography_zm_l', 'hydro_a', 'structures_6654_ma']
        source = [ntdb_zm_small[name] for name in names]
        target = FeatureClass(mem_gpkg, name='polygons_a')
        query = QueryFeatureToPolygon(source, target, None, xy_tol)
        lines, *_ = query._get_lines(mem_gpkg)
        assert len(lines) == count
        assert all(line.has_z for line in lines)
        assert all(line.has_m for line in lines)
    # End test_get_lines method

    def test_build_polygons(self, ntdb_zm_small, mem_gpkg):
        """
        Test build polygons
        """
        names = ['topography_zm_l', 'hydro_a', 'structures_6654_ma']
        source = [ntdb_zm_small[name] for name in names]
        target = FeatureClass(mem_gpkg, name='polygons_a')
        query = QueryFeatureToPolygon(source, target, None, None)
        lines, *_ = query._get_lines(mem_gpkg)
        polygons = query._build_polygons(lines)
        assert len(polygons) == 4044
    # End test_build_polygons method

    def test_add_attributes(self, ntdb_zm_small, mem_gpkg):
        """
        Test add attributes
        """
        names = ['topography_zm_l', 'hydro_a', 'structures_6654_ma']
        source = [ntdb_zm_small[name] for name in names]
        label = ntdb_zm_small['structures_4617_zm_p']
        target = FeatureClass(mem_gpkg, name='polygons_a')
        query = QueryFeatureToPolygon(source, target, label, None)
        lines, *_ = query._get_lines(mem_gpkg)
        polygons = query._build_polygons(lines)
        results = query._add_attributes(polygons)
        assert len(results) == 5823
        _, attributes = zip(*results)
        assert len(attributes[0]) == 8
        assert attributes.count((None,) * 8) == 3739
    # End test_add_attributes method

    def test_index_overlay(self, ntdb_zm_small, mem_gpkg):
        """
        Test index overlay
        """
        names = ['topography_zm_l', 'hydro_a', 'structures_6654_ma']
        source = [ntdb_zm_small[name] for name in names]
        label = ntdb_zm_small['structures_4617_zm_p']
        target = FeatureClass(mem_gpkg, name='polygons_a')
        query = QueryFeatureToPolygon(source, target, label, None)
        points, _ = query._get_points_attributes()
        lines, *_ = query._get_lines(mem_gpkg)
        polygons = query._build_polygons(lines)
        grouper = query._index_overlay(points, polygons)
        assert len(grouper) == 305
    # End test_index_overlay method
# End TestQueryFeatureToPolygon class


class TestQueryFeatureToLine:
    """
    Test QueryFeatureToLine
    """
    def test_get_target_shape_type(self):
        """
        Test get target shape type
        """
        query = QueryFeatureToLine([None], None, None)
        assert query._get_target_shape_type() == ShapeType.linestring
    # End test_get_target_shape_type method

    def test_spatial_reference_system(self, inputs, mem_gpkg):
        """
        Test spatial reference system
        """
        source = inputs['int_flavor_a']
        target = FeatureClass(mem_gpkg, name='lines_l')
        query = QueryFeatureToLine([source], target, None)
        srs = source.spatial_reference_system
        assert query.spatial_reference_system == srs
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(6654)):
            query = QueryFeatureToLine([source], target, None)
            assert query.spatial_reference_system != srs
    # End test_spatial_reference_system method

    @mark.parametrize('names, z_enabled, m_enabled', [
        (('hydro_4617_a', 'hydro_a'), False, False),
        (('hydro_4617_zm_a', 'hydro_a'), True, True),
        (('hydro_4617_m_a', 'hydro_a'), False, True),
    ])
    def test_zm_config(self, ntdb_zm_small, names, z_enabled, m_enabled):
        """
        Test ZM config and has zm
        """
        source = [ntdb_zm_small[n] for n in names]
        query = QueryFeatureToLine(source, None, None)
        assert query.zm_config.z_enabled is z_enabled
        assert query.zm_config.m_enabled is m_enabled
        assert query._has_zm == (z_enabled, m_enabled)
    # End test_zm_config method

    def test_get_unique_fields(self):
        """
        Test get unique fields
        """
        query = QueryFeatureToLine([None], None, None)
        assert not query._get_unique_fields()
    # End test_get_unique_fields method

    def test_get_null_record(self):
        """
        Get Null Record
        """
        query = QueryFeatureToLine([None], None, None)
        assert not query._get_null_record()
    # End test_get_null_record method

    def test_insert(self, mem_gpkg, ntdb_zm_small):
        """
        Test insert
        """
        source = [ntdb_zm_small['hydro_a']]
        target = FeatureClass(mem_gpkg, name='lines_l')
        query = QueryFeatureToLine(source, target, None)
        assert 'INTO lines_l(SHAPE)' in query.insert
    # End test_insert method

    @mark.parametrize('xy_tol, count', [
        (None, 8572),
        (10**-5, 8695),
    ])
    def test_get_lines(self, ntdb_zm_small, mem_gpkg, xy_tol, count):
        """
        Test get lines
        """
        names = ['topography_zm_l', 'hydro_a', 'structures_6654_ma']
        source = [ntdb_zm_small[name] for name in names]
        target = FeatureClass(mem_gpkg, name='lines_l')
        query = QueryFeatureToLine(source, target, xy_tol)
        lines, *_ = query._get_lines(mem_gpkg)
        assert len(lines) == count
        assert all(line.has_z for line in lines)
        assert all(line.has_m for line in lines)
    # End test_get_lines method
# End TestQueryFeatureToLine class


if __name__ == '__main__':  # pragma: no cover
    pass
