# -*- coding: utf-8 -*-
"""
Tests for Features
"""


from sqlite3 import OperationalError

from fudgeo import FeatureClass, GeoPackage
from fudgeo.enumeration import ShapeType
from pyproj import CRS
from pytest import mark, param, approx, raises

from spyops.environment import Extent, OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.environment.core import zm_config
from spyops.geometry.constant import FUDGEO_GEOMETRY_LOOKUP
from spyops.management import (
    add_xy_coordinates, copy_features, delete_features,
    multipart_to_singlepart)
from spyops.shared.constant import EPSG, ESRI
from spyops.shared.enumeration import WeightOption
from spyops.shared.field import ORIG_FID, POINT_M, POINT_Z

from tests.util import UseGrids


pytestmark = [mark.management, mark.features]


class TestMultiPartToSinglePart:
    """
    Test multipart to single-part
    """
    @mark.zm
    @mark.parametrize('fc_name, count', [
        ('structures_ma', 1452),
        ('structures_m_ma', 1452),
        ('structures_z_ma', 1452),
        ('structures_zm_ma', 1452),
        ('toponymy_mp', 142),
        ('toponymy_m_mp', 142),
        ('toponymy_z_mp', 142),
        ('toponymy_zm_mp', 142),
        ('transmission_ml', 51),
        ('transmission_m_ml', 51),
        ('transmission_z_ml', 51),
        ('transmission_zm_ml', 51),
        ('transmission_mp', 11),
        ('transmission_m_mp', 11),
        ('transmission_z_mp', 11),
        ('transmission_zm_mp', 11),
    ])
    @mark.parametrize('output_z', [
        param(OutputZOption.SAME, marks=mark.large),
        OutputZOption.ENABLED,
        param(OutputZOption.DISABLED, marks=mark.large),
    ])
    @mark.parametrize('output_m', [
        param(OutputMOption.SAME, marks=mark.large),
        OutputMOption.ENABLED,
        param(OutputMOption.DISABLED, marks=mark.large),
    ])
    def test_output_zm(self, ntdb_zm_small, mem_gpkg, fc_name, count, output_z, output_m):
        """
        Test multipart to single-part using Output ZM
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_explode')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source)
            exploded = multipart_to_singlepart(source=source, target=target)
        assert exploded.shape_type in (
            ShapeType.linestring, ShapeType.point, ShapeType.polygon)
        cls = FUDGEO_GEOMETRY_LOOKUP[exploded.shape_type][exploded.has_z, exploded.has_m]
        assert exploded.is_multi_part is False
        assert exploded.has_z == zm.z_enabled
        assert exploded.has_m == zm.m_enabled
        assert len(exploded) == count
        assert len(exploded.fields) == len(source.fields) + 1
        geoms, ids = zip(*exploded.select(ORIG_FID).fetchall())
        assert len(set(ids)) == len(source)
        assert all(isinstance(g, cls) for g in geoms)
    # End test_output_zm method

    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('structures_6654_ma', EPSG, 2955, False, (674894.5, 5653715.0, 710369.625, 5680768.5)),
        ('structures_6654_zm_ma', EPSG, 2955, False, (674894.5, 5653715.0, 710369.625, 5680768.5)),
        ('transmission_6654_m_ml', EPSG, 2955, False, (674555.1875, 5652839.5, 710282.9375, 5681615.5)),
        ('transmission_6654_z_ml', EPSG, 2955, False, (674555.1875, 5652839.5, 710282.9375, 5681615.5)),
        ('toponymy_6654_m_mp', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0)),
        ('toponymy_6654_z_mp', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0)),
        ('structures_10tm_ma', ESRI, 102179, False, (35292.07421875, 5647691.0, 70171.859375, 5674681.0)),
        ('structures_10tm_zm_ma', ESRI, 102179, False, (35292.07421875, 5647691.0, 70171.859375, 5674681.0)),
        ('transmission_10tm_m_ml', ESRI, 102179, False, (34970.6953125, 5647467.0, 70035.03125, 5675514.0)),
        ('transmission_10tm_z_ml', ESRI, 102179, False, (34970.6953125, 5647467.0, 70035.03125, 5675514.0)),
        ('toponymy_10tm_m_mp', ESRI, 102179, False, (35593.41796875, 5647808.0, 70109.640625, 5675312.5)),
        ('toponymy_10tm_z_mp', ESRI, 102179, False, (35593.41796875, 5647808.0, 70109.640625, 5675312.5)),
    ])
    def test_output_crs(self, ntdb_zm_small, mem_gpkg, fc_name, auth_name,
                        srs_id, flag, extent):
        """
        Test multi to single with output CRS and different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        crs = CRS.from_authority(auth_name=auth_name, code=srs_id)
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs), UseGrids(flag):
            zm = zm_config(source)
            result = multipart_to_singlepart(source=source, target=target)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert len(result) > len(source)
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs method

    @mark.parametrize('fc_name, pre_count, post_count', [
        ('structures_6654_ma', 18, 1442),
        ('structures_6654_zm_ma', 18, 1442),
        ('transmission_6654_m_ml', 4, 50),
        ('transmission_6654_z_ml', 4, 50),
        ('toponymy_6654_m_mp', 1, 142),
        ('toponymy_6654_z_mp', 1, 142),
        ('structures_10tm_ma', 18, 1442),
        ('structures_10tm_zm_ma', 18, 1442),
        ('transmission_10tm_m_ml', 4, 50),
        ('transmission_10tm_z_ml', 4, 50),
        ('toponymy_10tm_m_mp', 1, 142),
        ('toponymy_10tm_z_mp', 1, 142),
    ])
    def test_extent(self, ntdb_zm_small, mem_gpkg, fc_name, pre_count, post_count):
        """
        Test multi to single with extent set, because these features are
        so highly grouped the small extent does not filter out many, extent
        is applied to the source features before processing
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        crs = CRS(4326)
        assert len(source) == pre_count
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.2, 51.05, -114.05, 51.15, crs)):
            result = multipart_to_singlepart(source=source, target=target)
            assert len(result) == post_count
    # End test_output_crs method
# End TestMultiPartToSinglePart class


def test_delete_features(grid_index, fresh_gpkg):
    """
    Test delete_features
    """
    name = 'grid_a_copy'
    grid = grid_index['grid_a'].copy(name, geopackage=fresh_gpkg)
    assert len(grid) == 8
    delete_features(grid, where_clause='FID >= 5')
    assert len(grid) == 4
    delete_features(grid)
    assert len(grid) == 0
    path = fresh_gpkg.path
    assert path.exists()
    fresh_gpkg.connection.close()
    gpkg = GeoPackage(path)
    fc = gpkg[name]
    assert fc
    assert fc.is_empty
# End test_delete_features function


class TestCopyFeatures:
    """
    Test copy_features
    """
    @mark.parametrize('fc_name, where_clause, count', [
        ('lakes_a', None, 39),
        ('lakes_a', '', 39),
        ('lakes_a', 'SQKM > 5000', 28),
        ('disputed_boundaries_l', None, 561),
        ('disputed_boundaries_l', '', 561),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary"', 364),
        ('cities_p', None, 2540),
        ('cities_p', '', 2540),
        ('cities_p', 'POP IS NULL', 1377),
        ('cities_p', 'POP < 0', 0),
    ])
    def test_copy_features(self, world_features, mem_gpkg, fc_name, where_clause, count):
        """
        Test copy_features
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = copy_features(source=source, target=target, where_clause=where_clause)
        assert len(result) == count
    # End test_copy_features method

    @mark.parametrize('fc_name, where_clause, count', [
        ('lakes_a', None, 7),
        ('lakes_a', '', 7),
        ('lakes_a', 'SQKM > 5000', 5),
        ('disputed_boundaries_l', None, 40),
        ('disputed_boundaries_l', '', 40),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary"', 40),
        ('cities_p', None, 310),
        ('cities_p', '', 310),
        ('cities_p', 'POP IS NULL', 241),
        ('cities_p', 'POP > 0', 69),
    ])
    def test_extent(self, world_features, mem_gpkg, fc_name, where_clause, count):
        """
        Test with Extent
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with Swap(Setting.EXTENT, Extent.from_bounds(0, -20, 45, 30, CRS(4326))):
            result = copy_features(source=source, target=target, where_clause=where_clause)
            assert len(result) == count
    # End test_extent method

    @mark.zm
    @mark.parametrize('fc_name, where_clause, output_z_option, output_m_option, count', [
        ('lakes_a', 'SQKM > 5000', OutputZOption.SAME, OutputMOption.SAME, 28),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary"', OutputZOption.SAME, OutputMOption.SAME, 364),
        ('cities_p', 'POP IS NULL', OutputZOption.SAME, OutputMOption.SAME, 1377),
        ('lakes_a', 'SQKM > 5000', OutputZOption.ENABLED, OutputMOption.ENABLED, 28),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary"', OutputZOption.ENABLED, OutputMOption.ENABLED, 364),
        ('cities_p', 'POP IS NULL', OutputZOption.ENABLED, OutputMOption.ENABLED, 1377),
        ('lakes_a', 'SQKM > 5000', OutputZOption.DISABLED, OutputMOption.DISABLED, 28),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary"', OutputZOption.DISABLED, OutputMOption.DISABLED, 364),
        ('cities_p', 'POP IS NULL', OutputZOption.DISABLED, OutputMOption.DISABLED, 1377),
    ])
    def test_zm(self, world_features, mem_gpkg, fc_name, where_clause, output_z_option, output_m_option, count):
        """
        Test with ZM settings
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z_option),
              Swap(Setting.OUTPUT_M_OPTION, output_m_option),
              Swap(Setting.Z_VALUE, 123.456)):
            zm = zm_config(source)
            result = copy_features(source=source, target=target, where_clause=where_clause)
        assert len(result) == count
        assert target.has_z == zm.z_enabled
        assert target.has_m == zm.m_enabled
    # End test_zm method

    def test_sans_attrs(self, inputs, world_features, mem_gpkg):
        """
        Test sans attributes
        """
        where_clause = 'fid <= 10'
        fc_name = 'intersect_sans_attr_a'
        source = inputs[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = copy_features(source=source, target=target, where_clause=where_clause)
        assert len(result) == 5
        fc_name = 'admin_sans_attr_a'
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = copy_features(source=source, target=target, where_clause=where_clause)
        assert len(result) == 10
    # End test_sans_attrs method

    @mark.parametrize('fc_name, where_clause', [
        ('admin_a', 'ISO = "BR"'),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary'),
        ('cities_p', 'POP ISNULL()'),
        ('cities_p', 'POP <<>> 0'),
    ])
    def test_bad_sql(self, world_features, mem_gpkg, fc_name, where_clause):
        """
        Test bad SQL
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with raises(OperationalError):
            copy_features(source=source, target=target, where_clause=where_clause)
    # End test_bad_sql method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('hydro_4617_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('hydro_4617_zm_a', EPSG, 2955, False, (674655.0625, 5653054.0, 710481.625, 5681614.0)),
        ('transmission_4617_m_l', EPSG, 2955, False, (674555.1875, 5652839.5, 710282.9375, 5681615.5)),
        ('transmission_4617_z_l', EPSG, 2955, False, (674555.1875, 5652839.5, 710282.9375, 5681615.5)),
        ('toponymy_4617_m_p', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0)),
        ('toponymy_4617_z_p', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0)),
        ('hydro_4617_a', ESRI, 102179, False, (35000.796875, 5647522.5, 70211.8828125, 5675482.0)),
        ('hydro_4617_zm_a', ESRI, 102179, False, (35000.796875, 5647522.5, 70211.8828125, 5675482.0)),
        ('transmission_4617_m_l', ESRI, 102179, False, (34973.9453125, 5647476.0, 70037.765625, 5675522.0)),
        ('transmission_4617_z_l', ESRI, 102179, False, (34973.9453125, 5647476.0, 70037.765625, 5675522.0)),
        ('toponymy_4617_m_p', ESRI, 102179, False, (35596.453125, 5647816.0, 70112.4921875, 5675320.0)),
        ('toponymy_4617_z_p', ESRI, 102179, False, (35596.453125, 5647816.0, 70112.4921875, 5675320.0)),
        ('hydro_4617_a', ESRI, 102179, True, (34997.60546875, 5647514.0, 70209.1640625, 5675475.0)),
        ('hydro_4617_zm_a', ESRI, 102179, True, (34997.60546875, 5647514.0, 70209.1640625, 5675475.0)),
        ('transmission_4617_m_l', ESRI, 102179, True, (34970.6953125, 5647467.0, 70035.03125, 5675514.0)),
        ('transmission_4617_z_l', ESRI, 102179, True, (34970.6953125, 5647467.0, 70035.03125, 5675514.0)),
        ('toponymy_4617_m_p', ESRI, 102179, True, (35593.41796875, 5647808.0, 70109.640625, 5675312.5)),
        ('toponymy_4617_z_p', ESRI, 102179, True, (35593.41796875, 5647808.0, 70109.640625, 5675312.5)),
    ])
    @mark.parametrize('output_z', [
        OutputZOption.SAME,
        param(OutputZOption.ENABLED, marks=mark.large),
        param(OutputZOption.DISABLED, marks=mark.large),
    ])
    @mark.parametrize('output_m', [
        OutputMOption.SAME,
        param(OutputMOption.ENABLED, marks=mark.large),
        param(OutputMOption.DISABLED, marks=mark.large),
    ])
    def test_output_crs(self, ntdb_zm_small, mem_gpkg, fc_name, auth_name,
                        srs_id, flag, extent, output_z, output_m):
        """
        Test with output CRS and different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        crs = CRS.from_authority(auth_name=auth_name, code=srs_id)
        with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs),
              Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m),
              UseGrids(flag)):
            zm = zm_config(source)
            result = copy_features(source=source, target=target)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert len(result) == len(source)
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name', [
        param('hydro_6654_a', marks=mark.large),
        param('hydro_6654_m_a', marks=mark.large),
        'hydro_6654_z_a',
        'hydro_6654_zm_a',
    ])
    @mark.parametrize('output_z', [
        OutputZOption.SAME,
        param(OutputZOption.ENABLED, marks=mark.large),
        param(OutputZOption.DISABLED, marks=mark.large),
    ])
    @mark.parametrize('output_m', [
        OutputMOption.SAME,
        param(OutputMOption.ENABLED, marks=mark.large),
        param(OutputMOption.DISABLED, marks=mark.large),
    ])
    def test_output_crs_include_vertical(self, ntdb_zm_small, mem_gpkg, fc_name, output_z, output_m):
        """
        Test with output compound CRS coming from a compound CRS
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        srs_id = 6893
        crs = CRS(srs_id)
        assert crs.is_compound
        with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs),
              Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m),
              UseGrids(True)):
            zm = zm_config(source)
            result = copy_features(source=source, target=target)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert len(result) == len(source)
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs_include_vertical method
# End TestCopyFeatures class


class TestAddXYCoordinates:
    """
    Test Add XY Coordinates
    """
    @mark.parametrize('fc_name, count', [
        ('hydro_a', 349),
        ('transmission_p', 11),
        ('transmission_l', 60),
        ('structures_ma', 10),
        ('toponymy_mp', 0),
        ('transmission_ml', 0),
    ])
    def test_reduced(self, ntdb_zm_small, mem_gpkg, fc_name, count):
        """
        Test extent -- reduced data for faster testing
        """
        source = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        sql = f"""SELECT COUNT(1) AS CNT FROM {source.escaped_name} WHERE POINT_X IS NULL"""
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.5, 51.15, -114.375, 51.25, crs=CRS(4326))):
            add_xy_coordinates(source)
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            assert cursor.fetchone()[0] == count
    # End test_reduced method

    @mark.transform
    def test_geographic_input_projected_output(self, ntdb_zm_small, mem_gpkg):
        """
        Test feature class with geographic input and projected output
        """
        name = 'hydro_4617_a'
        source = ntdb_zm_small[name].copy(name, geopackage=mem_gpkg)
        crs = CRS(6893)
        assert crs.is_compound
        add_xy_coordinates(source)
        sql = f"""SELECT AVG(POINT_X) AS AVG_X, AVG(POINT_Y) AS AVG_Y FROM {source.escaped_name}"""
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            assert approx(cursor.fetchone(), abs=0.001) == (-114.2650, 51.1558)
        with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs), UseGrids(True)):
            add_xy_coordinates(source)
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            assert approx(cursor.fetchone(), abs=0.1) == (-12719924.87, 6615617.49)
    # End test_geographic_input_projected_output method

    @mark.zm
    def test_missing_zm_values(self, ntdb_zm_meh_small, mem_gpkg):
        """
        Test feature classes with enabled with Z or M and missing Z or M values
        """
        name = 'structures_vcs_zm_a'
        source = ntdb_zm_meh_small[name].copy(name, geopackage=mem_gpkg)
        add_xy_coordinates(source)
        sql = f"""SELECT COUNT(1) AS CNT FROM {source.escaped_name} WHERE POINT_M = 0"""
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            assert cursor.fetchone()[0] == len(source)
    # End test_missing_zm_values method

    @mark.zm
    @mark.transform
    @mark.parametrize('fc_name, in_count, out_count', [
        ('hydro_6654_a', 12, 14),
        ('hydro_6654_z_a', 13, 16),
        ('hydro_6654_m_a', 13, 16),
        ('hydro_6654_zm_a', 13, 17),
    ])
    @mark.parametrize('weight_option', [
        WeightOption.TWO_D,
        WeightOption.THREE_D,
    ])
    def test_output_crs_include_vertical(self, ntdb_zm_small, mem_gpkg,
                                         fc_name, in_count, out_count,
                                         weight_option):
        """
        Test with output compound CRS coming from a compound CRS
        """
        crs = CRS(6893)
        assert crs.is_compound
        source = ntdb_zm_small[fc_name].copy(fc_name, geopackage=mem_gpkg)
        assert len(source.fields) == in_count
        with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs), UseGrids(True)):
            result = add_xy_coordinates(source, weight_option=weight_option)
        assert len(result) == len(source)
        assert len(result.fields) == out_count
        with source.geopackage.connection as cin:
            cursor = cin.execute(f"""SELECT COUNT(1) AS CNT FROM {result.escaped_name} WHERE POINT_X IS NULL OR POINT_Y IS NULL""")
            assert cursor.fetchone()[0] == 0
            if POINT_Z.name in result.field_names:
                cursor = cin.execute(f"""SELECT  COUNT(1) AS CNT FROM {result.escaped_name} WHERE POINT_Z IS NULL""")
                assert cursor.fetchone()[0] == 0
            if POINT_M.name in result.field_names:
                cursor = cin.execute(f"""SELECT  COUNT(1) AS CNT FROM {result.escaped_name} WHERE POINT_M IS NULL""")
                assert cursor.fetchone()[0] == 0
    # End test_output_crs_include_vertical method
# End TestAddXYCoordinates class


if __name__ == '__main__':  # pragma: no cover
    pass
