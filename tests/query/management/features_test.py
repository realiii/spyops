# -*- coding: utf-8 -*-
"""
Test for Features Query classes
"""


from sqlite3 import OperationalError

from fudgeo import FeatureClass, Field
from fudgeo.enumeration import FieldType
from pyproj import CRS
from pytest import approx, mark, raises

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.query.management.features import (
    QueryAddXYCoordinates, QueryCalculateGeometryAttributes,
    QueryMultiPartToSinglePart)
from spyops.shared.enumeration import GeometryAttribute, WeightOption
from spyops.shared.field import POINT_M, POINT_X, POINT_Y, POINT_Z

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


if __name__ == '__main__':  # pragma: no cover
    pass
