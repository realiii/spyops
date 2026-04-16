# -*- coding: utf-8 -*-
"""
Tests for Features
"""


from collections import defaultdict
from sqlite3 import OperationalError

from fudgeo import FeatureClass, Field, GeoPackage, Table
from fudgeo.enumeration import FieldType, ShapeType
from pyproj import CRS
from pytest import mark, param, approx, raises

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.crs.util import get_crs_from_source
from spyops.environment import Extent, OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.environment.core import zm_config
from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.management import (
    add_xy_coordinates, calculate_geometry_attributes, copy_features,
    delete_features, feature_envelope_to_polygon, multipart_to_singlepart,
    xy_to_line)
from spyops.management.features import (
    check_geometry, minimum_bounding_geometry, repair_geometry,
    xy_table_to_point)
from spyops.crs.constant import EPSG, ESRI
from spyops.shared.enumeration import (
    GeometryAttribute, GeometryCheck, GroupOption, LineTypeOption,
    MinimumGeometryOption, WeightOption)
from spyops.shared.field import ORIG_FID, POINT_M, POINT_X, POINT_Y, POINT_Z

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
        geoms, ids = zip(*exploded.select([ORIG_FID]).fetchall())
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
    # End test_extent method
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
            assert approx(cursor.fetchone(), abs=0.1) == (-12719901.10, 6615598.68)
    # End test_geographic_input_projected_output method

    def test_centroid_polygon_with_holes(self, inputs, mem_gpkg):
        """
        Test centroid polygon with holes
        """
        name = 'yyc_a'
        source = inputs[name].copy(name, geopackage=mem_gpkg)
        add_xy_coordinates(source)
        sql = f"""SELECT AVG(POINT_X) AS AVG_X, AVG(POINT_Y) AS AVG_Y FROM {source.escaped_name}"""
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            assert approx(cursor.fetchone(), abs=0.0001) == (-114.05273, 51.03474)
    # End test_centroid_polygon_with_holes method

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


class TestCalculateGeometryAttributes:
    """
    Test calculate geometry attributes
    """
    @mark.parametrize('attribute, average_lcc, average_dd', [
        (GeometryAttribute.POINT_X, -1257783.07, -114.26),
        (GeometryAttribute.POINT_Y, 1436251.88, 51.15),
        (GeometryAttribute.POINT_Z, 1244.70, 1244.70),
        (GeometryAttribute.POINT_M, 210530.83, 210530.83),
    ])
    def test_point(self, ntdb_zm_small, mem_gpkg, attribute, average_lcc, average_dd):
        """
        Test point options on point feature class using extent and
        output coordinate system
        """
        fc_name = 'structures_lcc_zm_p'
        source = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        name = str(attribute)
        field = Field(name, data_type=FieldType.real)
        source.add_fields([field])
        sql = f"""SELECT AVG({name}) AS AVERAGE_VALUE 
                  FROM {source.escaped_name} 
                  WHERE {name} IS NOT NULL"""
        with Swap(Setting.EXTENT, Extent.from_bounds(
                -114.3169, 51.1955, -114.2277, 51.1282, crs=CRS(4326))):
            calculate_geometry_attributes(
                source, field=field, geometry_attribute=attribute)
            with source.geopackage.connection as cin:
                cursor = cin.execute(sql)
                assert approx(cursor.fetchone()[0], abs=0.1) == average_lcc
            with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(4326)):
                calculate_geometry_attributes(
                    source, field=field, geometry_attribute=attribute)
                with source.geopackage.connection as cin:
                    cursor = cin.execute(sql)
                    assert approx(cursor.fetchone()[0], abs=0.1) == average_dd
    # End test_point method

    @mark.parametrize('fc_name, attribute, average, average_dd', [
        ('hydro_lcc_a', GeometryAttribute.CENTROID_X, -1256943.21, -114.26),
        ('hydro_lcc_a', GeometryAttribute.CENTROID_Y, 1437254.25, 51.17),
        ('hydro_lcc_a', GeometryAttribute.CENTROID_Z, None, None),
        ('hydro_lcc_a', GeometryAttribute.CENTROID_M, None, None),
        ('hydro_lcc_zm_a', GeometryAttribute.CENTROID_X, -1256943.21, -114.26),
        ('hydro_lcc_zm_a', GeometryAttribute.CENTROID_Y, 1437254.25, 51.17),
        ('hydro_lcc_zm_a', GeometryAttribute.CENTROID_Z, 1270.76, 1270.76),
        ('hydro_lcc_zm_a', GeometryAttribute.CENTROID_M, 184285.48, 184285.48),
        ('transmission_lcc_l', GeometryAttribute.CENTROID_X, -1258272.89, -114.27),
        ('transmission_lcc_l', GeometryAttribute.CENTROID_Y, 1435163.99, 51.14),
        ('transmission_lcc_l', GeometryAttribute.CENTROID_Z, None, None),
        ('transmission_lcc_l', GeometryAttribute.CENTROID_M, None, None),
        ('transmission_lcc_zm_l', GeometryAttribute.CENTROID_X, -1258272.89, -114.27),
        ('transmission_lcc_zm_l', GeometryAttribute.CENTROID_Y, 1435163.99, 51.14),
        ('transmission_lcc_zm_l', GeometryAttribute.CENTROID_Z, 1212.30, 1212.63),
        ('transmission_lcc_zm_l', GeometryAttribute.CENTROID_M, 400006.96, 400006.96),
    ])
    def test_centroid(self, ntdb_zm_small, mem_gpkg, fc_name, attribute, average, average_dd):
        """
        Test centroid options on non-point feature class using extent and
        output coordinate system
        """
        source = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        name = str(attribute)
        field = Field(name, data_type=FieldType.real)
        source.add_fields([field])
        is_extended = source.has_z or source.has_m
        if not is_extended and attribute in (
                GeometryAttribute.CENTROID_Z, GeometryAttribute.CENTROID_M):
            with raises(ValueError):
                calculate_geometry_attributes(
                    source, field=field, geometry_attribute=attribute)
            return
        sql = f"""SELECT AVG({name}) AS AVERAGE_VALUE 
                  FROM {source.escaped_name} 
                  WHERE {name} IS NOT NULL"""
        with Swap(Setting.EXTENT, Extent.from_bounds(
                -114.3169, 51.1955, -114.2277, 51.1282, crs=CRS(4326))):
            calculate_geometry_attributes(
                source, field=field, geometry_attribute=attribute)
            with source.geopackage.connection as cin:
                cursor = cin.execute(sql)
                assert approx(cursor.fetchone()[0], abs=0.1) == average
            with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(4326)):
                calculate_geometry_attributes(
                    source, field=field, geometry_attribute=attribute)
                with source.geopackage.connection as cin:
                    cursor = cin.execute(sql)
                    assert approx(cursor.fetchone()[0], abs=0.1) == average_dd
    # End test_centroid method

    @mark.parametrize('fc_name, count', [
        ('hydro_a', 11_397),
        ('hydro_zm_a', 11_397),
        ('structures_6654_zm_a', 15_525),
        ('structures_6654_zm_ma', 15_503),
        ('transmission_mp', 11),
        ('transmission_l', 451),
        ('transmission_ml', 436),
    ])
    def test_point_count(self, ntdb_zm_small, mem_gpkg, fc_name, count):
        """
        Test point count
        """
        attribute = GeometryAttribute.POINT_COUNT
        source = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        name = str(attribute)
        field = Field(name, data_type=FieldType.integer)
        source.add_fields([field])
        sql = f"""SELECT SUM({name}) AS TOTAL_VALUE 
                  FROM {source.escaped_name}"""
        calculate_geometry_attributes(
            source, field=field, geometry_attribute=attribute)
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            assert cursor.fetchone()[0] == count
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(4326)):
            calculate_geometry_attributes(
                source, field=field, geometry_attribute=attribute)
            with source.geopackage.connection as cin:
                cursor = cin.execute(sql)
                assert cursor.fetchone()[0] == count
    # End test_point_count method

    @mark.parametrize('fc_name, count', [
        ('hydro_a', 382),
        ('hydro_zm_a', 382),
        ('structures_6654_zm_a', 1453),
        ('structures_6654_zm_ma', 1452),
        ('transmission_mp', 11),
        ('transmission_l', 66),
        ('transmission_ml', 51),
    ])
    def test_part_count(self, ntdb_zm_small, mem_gpkg, fc_name, count):
        """
        Test part count
        """
        attribute = GeometryAttribute.PART_COUNT
        source = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        name = str(attribute)
        field = Field(name, data_type=FieldType.integer)
        source.add_fields([field])
        sql = f"""SELECT SUM({name}) AS TOTAL_VALUE 
                  FROM {source.escaped_name}"""
        calculate_geometry_attributes(
            source, field=field, geometry_attribute=attribute)
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            assert cursor.fetchone()[0] == count
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(4326)):
            calculate_geometry_attributes(
                source, field=field, geometry_attribute=attribute)
            with source.geopackage.connection as cin:
                cursor = cin.execute(sql)
                assert cursor.fetchone()[0] == count
    # End test_part_count method

    @mark.parametrize('fc_name, count', [
        ('hydro_a', 47),
        ('hydro_zm_a', 47),
        ('structures_6654_zm_a', 134),
        ('structures_6654_zm_ma', 133),
    ])
    def test_hole_count(self, ntdb_zm_small, mem_gpkg, fc_name, count):
        """
        Test hole count
        """
        attribute = GeometryAttribute.HOLE_COUNT
        source = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        name = str(attribute)
        field = Field(name, data_type=FieldType.integer)
        source.add_fields([field])
        sql = f"""SELECT SUM({name}) AS TOTAL_VALUE 
                  FROM {source.escaped_name}"""
        calculate_geometry_attributes(
            source, field=field, geometry_attribute=attribute)
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            assert cursor.fetchone()[0] == count
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(4326)):
            calculate_geometry_attributes(
                source, field=field, geometry_attribute=attribute)
            with source.geopackage.connection as cin:
                cursor = cin.execute(sql)
                assert cursor.fetchone()[0] == count
    # End test_hole_count method

    @mark.parametrize('fc_name, attribute, average, average_dd', [
        ('hydro_lcc_a', GeometryAttribute.EXTENT_MIN_X, -1272319.31, -114.499),
        ('hydro_lcc_a', GeometryAttribute.EXTENT_MIN_Y, 1430215.96, 51.1008),
        ('hydro_lcc_a', GeometryAttribute.EXTENT_MIN_Z, None, None),
        ('hydro_lcc_a', GeometryAttribute.EXTENT_MIN_M, None, None),
        ('hydro_lcc_zm_a', GeometryAttribute.EXTENT_MIN_X, -1272319.31, -114.499),
        ('hydro_lcc_zm_a', GeometryAttribute.EXTENT_MIN_Y, 1430215.96, 51.1008),
        ('hydro_lcc_zm_a', GeometryAttribute.EXTENT_MIN_Z, 1092.3451, 1092.34451),
        ('hydro_lcc_zm_a', GeometryAttribute.EXTENT_MIN_M, 201001.0, 201001.0),
        ('transmission_lcc_l', GeometryAttribute.EXTENT_MIN_X, -1274015.73, -114.499),
        ('transmission_lcc_l', GeometryAttribute.EXTENT_MIN_Y, 1420142.05, 51.016),
        ('transmission_lcc_l', GeometryAttribute.EXTENT_MIN_Z, None, None),
        ('transmission_lcc_l', GeometryAttribute.EXTENT_MIN_M, None, None),
        ('transmission_lcc_zm_l', GeometryAttribute.EXTENT_MIN_X, -1274015.73, -114.499),
        ('transmission_lcc_zm_l', GeometryAttribute.EXTENT_MIN_Y, 1420142.05, 51.016),
        ('transmission_lcc_zm_l', GeometryAttribute.EXTENT_MIN_Z, 1061.5443, 1061.5443),
        ('transmission_lcc_zm_l', GeometryAttribute.EXTENT_MIN_M, 400001.0, 400001.0),
        ('toponymy_10tm_mp', GeometryAttribute.EXTENT_MIN_X, 35593.418, -114.4926),
        ('toponymy_10tm_mp', GeometryAttribute.EXTENT_MIN_Y, 5647808.789, 51.0005),
        ('toponymy_10tm_mp', GeometryAttribute.EXTENT_MIN_Z, None, None),
        ('toponymy_10tm_mp', GeometryAttribute.EXTENT_MIN_M, None, None),
        ('hydro_lcc_a', GeometryAttribute.EXTENT_MAX_X, -1254197.676, -114.2059),
        ('hydro_lcc_a', GeometryAttribute.EXTENT_MAX_Y, 1443909.0185, 51.2073),
        ('hydro_lcc_a', GeometryAttribute.EXTENT_MAX_Z, None, None),
        ('hydro_lcc_a', GeometryAttribute.EXTENT_MAX_M, None, None),
        ('hydro_lcc_zm_a', GeometryAttribute.EXTENT_MAX_X, -1254197.676, -114.2059),
        ('hydro_lcc_zm_a', GeometryAttribute.EXTENT_MAX_Y, 1443909.0185, 51.2073),
        ('hydro_lcc_zm_a', GeometryAttribute.EXTENT_MAX_Z, 1316.938, 1316.938),
        ('hydro_lcc_zm_a', GeometryAttribute.EXTENT_MAX_M, 212029.0, 212029.0),
        ('transmission_lcc_l', GeometryAttribute.EXTENT_MAX_X, -1239093.5373, -113.9999),
        ('transmission_lcc_l', GeometryAttribute.EXTENT_MAX_Y, 1446983.133, 51.2215),
        ('transmission_lcc_l', GeometryAttribute.EXTENT_MAX_Z, None, None),
        ('transmission_lcc_l', GeometryAttribute.EXTENT_MAX_M, None, None),
        ('transmission_lcc_zm_l', GeometryAttribute.EXTENT_MAX_X, -1239093.5373, -113.9999),
        ('transmission_lcc_zm_l', GeometryAttribute.EXTENT_MAX_Y, 1446983.133, 51.2215),
        ('transmission_lcc_zm_l', GeometryAttribute.EXTENT_MAX_Z, 1297.9587, 1297.9587),
        ('transmission_lcc_zm_l', GeometryAttribute.EXTENT_MAX_M, 400028.0, 400028.0),
        ('toponymy_10tm_mp', GeometryAttribute.EXTENT_MAX_X, 70109.637, -114.0000),
        ('toponymy_10tm_mp', GeometryAttribute.EXTENT_MAX_Y, 5675312.072, 51.2499),
        ('toponymy_10tm_mp', GeometryAttribute.EXTENT_MAX_Z, None, None),
        ('toponymy_10tm_mp', GeometryAttribute.EXTENT_MAX_M, None, None),
    ])
    def test_extent(self, ntdb_zm_small, mem_gpkg, fc_name, attribute, average, average_dd):
        """
        Test extent options on non-point feature class using extent and
        output coordinate system
        """
        source = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        name = str(attribute)
        field = Field(name, data_type=FieldType.real)
        source.add_fields([field])
        is_extended = source.has_z or source.has_m
        if not is_extended and attribute in (
                GeometryAttribute.EXTENT_MAX_Z, GeometryAttribute.EXTENT_MAX_M,
                GeometryAttribute.EXTENT_MIN_Z, GeometryAttribute.EXTENT_MIN_M):
            with raises(ValueError):
                calculate_geometry_attributes(
                    source, field=field, geometry_attribute=attribute)
            return
        if attribute in (GeometryAttribute.EXTENT_MAX_X, GeometryAttribute.EXTENT_MAX_Y,
                         GeometryAttribute.EXTENT_MAX_Z, GeometryAttribute.EXTENT_MAX_M):
            stat = 'MAX'
        else:
            stat = 'MIN'
        sql = f"""SELECT {stat}({name}) AS STAT_VALUE 
                  FROM {source.escaped_name} 
                  WHERE {name} IS NOT NULL"""
        with Swap(Setting.EXTENT, Extent.from_bounds(
                -114.3169, 51.1955, -114.2277, 51.1282, crs=CRS(4326))):
            calculate_geometry_attributes(
                source, field=field, geometry_attribute=attribute)
            with source.geopackage.connection as cin:
                cursor = cin.execute(sql)
                assert approx(cursor.fetchone()[0], abs=0.1) == average
            with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(4326)):
                calculate_geometry_attributes(
                    source, field=field, geometry_attribute=attribute)
                with source.geopackage.connection as cin:
                    cursor = cin.execute(sql)
                    assert approx(cursor.fetchone()[0], abs=0.001) == average_dd
    # End test_extent method

    @mark.parametrize('fc_name, attribute, average, average_dd', [
        ('hydro_lcc_a', GeometryAttribute.INSIDE_X, -1256931.874, -114.2615),
        ('hydro_lcc_a', GeometryAttribute.INSIDE_Y, 1437267.177, 51.1706),
        ('transmission_lcc_l', GeometryAttribute.INSIDE_X, -1258118.115, -114.270),
        ('transmission_lcc_l', GeometryAttribute.INSIDE_Y, 1435083.744, 51.1484),
    ])
    def test_inside(self, ntdb_zm_small, mem_gpkg, fc_name, attribute, average, average_dd):
        """
        Test inside options on non-point feature class using extent and
        output coordinate system
        """
        source = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        name = str(attribute)
        field = Field(name, data_type=FieldType.real)
        source.add_fields([field])
        sql = f"""SELECT AVG({name}) AS STAT_VALUE 
                  FROM {source.escaped_name} 
                  WHERE {name} IS NOT NULL"""
        with Swap(Setting.EXTENT, Extent.from_bounds(
                -114.3169, 51.1955, -114.2277, 51.1282, crs=CRS(4326))):
            calculate_geometry_attributes(
                source, field=field, geometry_attribute=attribute)
            with source.geopackage.connection as cin:
                cursor = cin.execute(sql)
                assert approx(cursor.fetchone()[0], abs=0.1) == average
            with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(4326)):
                calculate_geometry_attributes(
                    source, field=field, geometry_attribute=attribute)
                with source.geopackage.connection as cin:
                    cursor = cin.execute(sql)
                    assert approx(cursor.fetchone()[0], abs=0.001) == average_dd
    # End test_inside method

    @mark.parametrize('fc_name, attribute, average, average_dd', [
        ('transmission_lcc_l', GeometryAttribute.LINE_START_X, -1263260.068, -114.3509),
        ('transmission_lcc_l', GeometryAttribute.LINE_START_Y, 1437753.072, 51.1592),
        ('transmission_6654_zm_ml', GeometryAttribute.LINE_START_X, 675148.261, -114.5000),
        ('transmission_6654_zm_ml', GeometryAttribute.LINE_START_Y, 5660580.401, 51.0699),
        ('transmission_6654_zm_ml', GeometryAttribute.LINE_START_Z, 1250.77354, 1250.7735),
        ('transmission_6654_zm_ml', GeometryAttribute.LINE_START_M, 211004.0, 211004.0),
        ('transmission_lcc_l', GeometryAttribute.LINE_END_X, -1253401.174, -114.1951),
        ('transmission_lcc_l', GeometryAttribute.LINE_END_Y, 1432707.341, 51.1398),
        ('transmission_6654_zm_ml', GeometryAttribute.LINE_END_X, 707375.731, -114.03608),
        ('transmission_6654_zm_ml', GeometryAttribute.LINE_END_Y, 5668602.5022, 51.1312),
        ('transmission_6654_zm_ml', GeometryAttribute.LINE_END_Z, 1094.3065, 1094.3065),
        ('transmission_6654_zm_ml', GeometryAttribute.LINE_END_M, 228680.6666, 228680.6666),
    ])
    def test_line_start_end(self, ntdb_zm_small, mem_gpkg, fc_name, attribute, average, average_dd):
        """
        Test line start and line end options on non-point feature class using
        extent and output coordinate system
        """
        source = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        name = str(attribute)
        field = Field(name, data_type=FieldType.real)
        source.add_fields([field])
        sql = f"""SELECT AVG({name}) AS STAT_VALUE 
                  FROM {source.escaped_name} 
                  WHERE {name} IS NOT NULL"""
        with Swap(Setting.EXTENT, Extent.from_bounds(
                -114.3169, 51.1955, -114.2277, 51.1282, crs=CRS(4326))):
            calculate_geometry_attributes(
                source, field=field, geometry_attribute=attribute)
            with source.geopackage.connection as cin:
                cursor = cin.execute(sql)
                assert approx(cursor.fetchone()[0], abs=0.1) == average
            with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(4326)):
                calculate_geometry_attributes(
                    source, field=field, geometry_attribute=attribute)
                with source.geopackage.connection as cin:
                    cursor = cin.execute(sql)
                    assert approx(cursor.fetchone()[0], abs=0.001) == average_dd
    # End test_line_start_end method

    @mark.parametrize('fc_name, code, attribute, min_value, max_value, unit', [
        ('transmission_lcc_zm_l', None, GeometryAttribute.LENGTH, 615.0, 75_973.1, LengthUnit.FEET_US),
        ('transmission_lcc_zm_l', None, GeometryAttribute.LENGTH_GEODESIC, 616.7, 76_194.0, LengthUnit.FEET_US),
        ('transmission_lcc_l', None, GeometryAttribute.LENGTH, 615.0, 75_973.1, LengthUnit.FEET_US),
        ('transmission_lcc_l', None, GeometryAttribute.LENGTH_GEODESIC, 616.7, 76_194.0, LengthUnit.FEET_US),
        ('transmission_lcc_l', None, GeometryAttribute.LENGTH, 187.4, 23_156.6, LengthUnit.METERS),
        ('transmission_lcc_l', None, GeometryAttribute.LENGTH_GEODESIC, 187.9, 23_224.0, LengthUnit.METERS),
        ('transmission_lcc_l', 4326, GeometryAttribute.LENGTH, 187.9, 23_224.0, LengthUnit.METERS),
        ('transmission_lcc_l', 4326, GeometryAttribute.LENGTH_GEODESIC, 187.9, 23_224.0, LengthUnit.METERS),
        ('transmission_lcc_l', 2955, GeometryAttribute.LENGTH, 188.0, 23_224.4, LengthUnit.METERS),
        ('transmission_lcc_l', 2955, GeometryAttribute.LENGTH_GEODESIC, 187.9, 23_224.0, LengthUnit.METERS),
        ('hydro_lcc_zm_a', None, GeometryAttribute.PERIMETER, 97.5, 94_073.3, LengthUnit.METERS),
        ('hydro_lcc_zm_a', None, GeometryAttribute.PERIMETER_GEODESIC, 97.8, 94_343.6, LengthUnit.METERS),
        ('hydro_lcc_a', None, GeometryAttribute.PERIMETER, 97.5, 94_073.3, LengthUnit.METERS),
        ('hydro_lcc_a', None, GeometryAttribute.PERIMETER_GEODESIC, 97.8, 94_343.6, LengthUnit.METERS),
        ('hydro_lcc_a', 4326, GeometryAttribute.PERIMETER, 97.8, 94_343.6, LengthUnit.METERS),
        ('hydro_lcc_a', 4326, GeometryAttribute.PERIMETER_GEODESIC, 97.8, 94_343.6, LengthUnit.METERS),
        ('hydro_lcc_a', 2955, GeometryAttribute.PERIMETER, 97.8, 94_353.1, LengthUnit.METERS),
        ('hydro_lcc_a', 2955, GeometryAttribute.PERIMETER_GEODESIC, 97.8, 94_343.6, LengthUnit.METERS),
        ('hydro_lcc_zm_a', None, GeometryAttribute.AREA, 0.12, 793.0, AreaUnit.ACRES_INTERNATIONAL),
        ('hydro_lcc_zm_a', None, GeometryAttribute.AREA_GEODESIC, 0.12, 797.9, AreaUnit.ACRES_INTERNATIONAL),
        ('hydro_lcc_a', None, GeometryAttribute.AREA, 0.12, 793.0, AreaUnit.ACRES_INTERNATIONAL),
        ('hydro_lcc_a', None, GeometryAttribute.AREA_GEODESIC, 0.12, 797.9, AreaUnit.ACRES_INTERNATIONAL),
        ('hydro_lcc_a', None, GeometryAttribute.AREA, 5423.4, 34_544_051.9, AreaUnit.SQUARE_FEET_US),
        ('hydro_lcc_a', None, GeometryAttribute.AREA_GEODESIC, 5459.0, 34_756_912.3, AreaUnit.SQUARE_FEET_US),
        ('hydro_lcc_a', None, GeometryAttribute.AREA, 503.8, 3_209_260.2, AreaUnit.SQUARE_METERS),
        ('hydro_lcc_a', None, GeometryAttribute.AREA_GEODESIC, 507.1, 3_229_035.7, AreaUnit.SQUARE_METERS),
        ('hydro_lcc_a', 4326, GeometryAttribute.AREA, 507.1, 3_229_035.7, AreaUnit.SQUARE_METERS),
        ('hydro_lcc_a', 4326, GeometryAttribute.AREA_GEODESIC, 507.1, 3_229_035.7, AreaUnit.SQUARE_METERS),
        ('hydro_lcc_a', 2955, GeometryAttribute.AREA, 507.2, 3_229_175.4, AreaUnit.SQUARE_METERS),
        ('hydro_lcc_a', 2955, GeometryAttribute.AREA_GEODESIC, 507.1, 3_229_035.7, AreaUnit.SQUARE_METERS),
    ])
    def test_area_and_length(self, ntdb_zm_small, mem_gpkg, fc_name, code, attribute, min_value, max_value, unit):
        """
        Test area and area geodesic + length and length geodesic (aka perimeter)
        """
        source = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        name = str(attribute)
        field = Field(name, data_type=FieldType.real)
        source.add_fields([field])
        sql = f"""SELECT MIN({name}) AS MIN_VALUE, MAX({name}) AS MAX_VALUE
                  FROM {source.escaped_name} 
                  WHERE {name} IS NOT NULL"""
        if code is None:
            crs = get_crs_from_source(source)
        else:
            crs = CRS(code)
        if unit in AreaUnit:
            kwargs = {'area_unit': unit}
        else:
            kwargs = {'length_unit': unit}
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs):
            calculate_geometry_attributes(
                source, field=field, geometry_attribute=attribute, **kwargs)
            with source.geopackage.connection as cin:
                cursor = cin.execute(sql)
                assert approx(cursor.fetchone(), abs=0.1) == (min_value, max_value)
    # End test_area_and_length method

    @mark.parametrize('fc_name, code, average', [
        ('transmission_lcc_l', None, 98.4079),
        ('transmission_lcc_l', 4326, 98.4079),
        ('transmission_lcc_l', 2955, 98.4079),
    ])
    def test_line_azimuth(self, ntdb_zm_small, mem_gpkg, fc_name, code, average):
        """
        Test line azimuth
        """
        attribute = GeometryAttribute.LINE_AZIMUTH
        source = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        name = str(attribute)
        field = Field(name, data_type=FieldType.real)
        source.add_fields([field])
        sql = f"""SELECT AVG({name}) AS AVG_VALUE
                  FROM {source.escaped_name} 
                  WHERE {name} IS NOT NULL"""
        if code is None:
            crs = get_crs_from_source(source)
        else:
            crs = CRS(code)
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs):
            calculate_geometry_attributes(
                source, field=field, geometry_attribute=attribute)
            with source.geopackage.connection as cin:
                cursor = cin.execute(sql)
                assert approx(cursor.fetchone()[0], abs=0.001) == average
    # End test_line_azimuth method
# End TestCalculateGeometryAttributes class


class TestCheckGeometry:
    """
    Test Check Geometry
    """
    @mark.parametrize('fc_name, count', [
        param('admin_a', 211_853, marks=mark.slow),
        ('continent_a', 1958),
        param('country_a', 208_318, marks=mark.slow),
        ('disputed_boundaries_l', 3),
        ('drainage_l', 0),
        ('geogrid_l', 1),
        ('lakes_a', 40),
        param('latlong_l', 1, marks=mark.slow),
        ('railroads_l', 15),
        ('region_a', 1979),
        ('rivers_l', 1),
        param('roads_l', 239, marks=mark.slow),
        ('utmzone_a', 1202),
        ('airports_p', 0),
        ('cities_p', 0),
        param('admin_mp_a', 5824, marks=mark.slow),
        ('airports_mp_p', 0),
        param('roads_mp_l', 191, marks=mark.slow),
        ('roads_ml', 20),
    ])
    def test_defaults(self, world_features, mem_gpkg, fc_name, count):
        """
        Test Check Geometry with Default options
        """
        fc = world_features[fc_name]
        target = Table(name='cg_results', geopackage=mem_gpkg)
        result = check_geometry(fc, target)
        assert len(result) == count
    # End test_defaults function

    @mark.parametrize('fc_name, count', [
        param('admin_a', 0, marks=mark.slow),
        ('continent_a', 1),
        param('country_a', 1, marks=mark.slow),
        ('disputed_boundaries_l', 1),
        ('drainage_l', 0),
        ('geogrid_l', 1),
        ('lakes_a', 1),
        param('latlong_l', 1, marks=mark.slow),
        ('railroads_l', 0),
        ('region_a', 1),
        ('rivers_l', 1),
        param('roads_l', 1, marks=mark.slow),
        ('utmzone_a', 1),
        ('airports_p', 0),
        ('cities_p', 0),
        ('admin_mp_a', 0),
        ('airports_mp_p', 0),
        ('roads_mp_l', 0),
        ('roads_ml', 0),
    ])
    def test_check_extent(self, world_features, mem_gpkg, fc_name, count):
        """
        Test Check Extent
        """
        fc = world_features[fc_name]
        target = Table(name='cg_results', geopackage=mem_gpkg)
        result = check_geometry(fc, target, check_options=GeometryCheck.EXTENT)
        assert len(result) == count
    # End test_check_extent function

    @mark.parametrize('fc_name, counts', [
        ('hydro_m_a', (382, 1, 0, 0)),
        ('hydro_zm_a', (382, 1, 0, 0)),
        ('structures_m_a', (1453, 4, 0, 0)),
        ('structures_m_ma', (18, 16, 0, 0)),
        ('structures_m_p', (0, 0, 0, 0)),
        ('structures_ma', (18, 0, 0, 0)),
        ('structures_p', (0, 0, 0, 0)),
        ('structures_z_ma', (18, 0, 18, 0)),
        ('structures_z_p', (0, 0, 0, 0)),
        ('structures_zm_a', (1453, 4, 4, 0)),
        ('structures_zm_ma', (18, 16, 1, 0)),
        ('structures_zm_p', (0, 0, 0, 0)),
        ('topography_m_l', (485, 235, 0, 0)),
        ('topography_zm_l', (485, 235, 235, 0)),
        ('toponymy_m_mp', (0, 0, 0, 0)),
        ('toponymy_m_p', (0, 0, 0, 0)),
        ('toponymy_mp', (0, 0, 0, 0)),
        ('toponymy_p', (0, 0, 0, 0)),
        ('toponymy_z_mp', (0, 0, 0, 0)),
        ('toponymy_z_p', (0, 0, 0, 0)),
        ('toponymy_zm_mp', (0, 0, 0, 0)),
        ('toponymy_zm_p', (0, 0, 0, 0)),
        ('transmission_m_l', (0, 0, 0, 0)),
        ('transmission_m_ml', (1, 1, 0, 0)),
        ('transmission_m_mp', (0, 0, 0, 0)),
        ('transmission_m_p', (0, 0, 0, 0)),
        ('transmission_ml', (1, 0, 0, 0)),
        ('transmission_mp', (0, 0, 0, 0)),
        ('transmission_p', (0, 0, 0, 0)),
        ('transmission_z_ml', (1, 0, 1, 0)),
        ('transmission_z_mp', (0, 0, 0, 0)),
        ('transmission_z_p', (0, 0, 0, 0)),
        ('transmission_zm_l', (0, 0, 0, 0)),
        ('transmission_zm_ml', (1, 1, 1, 0)),
        ('transmission_zm_mp', (0, 0, 0, 0)),
        ('transmission_zm_p', (0, 0, 0, 0)),
    ])
    def test_check_coordinates(self, ntdb_zm_small, mem_gpkg, fc_name, counts):
        """
        Test Check Coordinates
        """
        fc = ntdb_zm_small[fc_name]
        options = (
            GeometryCheck.REPEATED_XY | GeometryCheck.REPEATED_M |
            GeometryCheck.MISMATCH_Z | GeometryCheck.MISMATCH_M
        )
        target = Table(name='cg_results', geopackage=mem_gpkg)
        result = check_geometry(fc, target, check_options=options)
        assert len(result) == sum(counts)
        checks = (GeometryCheck.REPEATED_XY, GeometryCheck.REPEATED_M,
                  GeometryCheck.MISMATCH_Z, GeometryCheck.MISMATCH_M)
        names = [check.name for check in checks]
        counter = defaultdict(int)
        cursor = result.select(('ORIG_FID', 'REASON'))
        for _, name in cursor.fetchall():
            counter[name] += 1
        assert tuple(counter[n] for n in names) == counts
    # End test_check_coordinates method

    @mark.parametrize('fc_name, counts', [
        ('hydro_m_a', (382, 1, 0, 0)),
        ('hydro_zm_a', (382, 1, 0, 0)),
        ('structures_m_a', (1453, 4, 0, 0)),
        ('structures_m_ma', (18, 16, 0, 0)),
        ('structures_m_p', (0, 0, 0, 0)),
        ('structures_ma', (18, 0, 0, 0)),
        ('structures_p', (0, 0, 0, 0)),
        ('structures_z_ma', (18, 0, 18, 0)),
        ('structures_z_p', (0, 0, 0, 0)),
        ('structures_zm_a', (1453, 4, 4, 0)),
        ('structures_zm_ma', (18, 16, 4, 0)),
        ('structures_zm_p', (0, 0, 0, 0)),
        ('topography_m_l', (627, 235, 0, 0)),
        ('topography_zm_l', (627, 235, 235, 0)),
        ('toponymy_m_mp', (1, 0, 0, 0)),
        ('toponymy_m_p', (0, 0, 0, 0)),
        ('toponymy_mp', (1, 0, 0, 0)),
        ('toponymy_p', (0, 0, 0, 0)),
        ('toponymy_z_mp', (1, 0, 0, 0)),
        ('toponymy_z_p', (0, 0, 0, 0)),
        ('toponymy_zm_mp', (1, 0, 0, 0)),
        ('toponymy_zm_p', (0, 0, 0, 0)),
        ('transmission_m_l', (4, 0, 0, 0)),
        ('transmission_m_ml', (3, 1, 0, 0)),
        ('transmission_m_mp', (0, 0, 0, 0)),
        ('transmission_m_p', (0, 0, 0, 0)),
        ('transmission_ml', (3, 0, 0, 0)),
        ('transmission_mp', (0, 0, 0, 0)),
        ('transmission_p', (0, 0, 0, 0)),
        ('transmission_z_ml', (3, 0, 1, 0)),
        ('transmission_z_mp', (0, 0, 0, 0)),
        ('transmission_z_p', (0, 0, 0, 0)),
        ('transmission_zm_l', (4, 0, 0, 0)),
        ('transmission_zm_ml', (3, 1, 1, 0)),
        ('transmission_zm_mp', (0, 0, 0, 0)),
        ('transmission_zm_p', (0, 0, 0, 0)),
    ])
    def test_check_coordinates_with_tolerance(self, ntdb_zm_small, mem_gpkg, fc_name, counts):
        """
        Test Check Coordinates with tolerance set high
        """
        fc = ntdb_zm_small[fc_name]
        options = (
            GeometryCheck.REPEATED_XY | GeometryCheck.REPEATED_M |
            GeometryCheck.MISMATCH_Z | GeometryCheck.MISMATCH_M
        )
        target = Table(name='cg_results', geopackage=mem_gpkg)
        result = check_geometry(fc, target, check_options=options,
                                xy_tolerance=0.001)
        assert len(result) == sum(counts)
        checks = (GeometryCheck.REPEATED_XY, GeometryCheck.REPEATED_M,
                  GeometryCheck.MISMATCH_Z, GeometryCheck.MISMATCH_M)
        names = [check.name for check in checks]
        counter = defaultdict(int)
        cursor = result.select(('ORIG_FID', 'REASON'))
        for _, name in cursor.fetchall():
            counter[name] += 1
        assert tuple(counter[n] for n in names) == counts
    # End test_check_coordinates_with_tolerance method
# End TestCheckGeometry class


class TestRepairGeometry:
    """
    Test Repair Geometry
    """
    @mark.parametrize('fc_name, pre_count, post_count, expected_reasons', [
        ('point_p', 4, 4, ['Empty Point'] * 4),
        ('linestring_l', 1, 5, [
            'Empty LineString', 'Single Point LineString',
            'Mixed Points LineString', 'Single Empty Point LineString',
            'Multiple Empty Points LineString']),
        ('polygon_a', 3, 10, [
            'Empty Polygon', 'Multiple Empty Rings Polygon',
            'Empty Exterior Regular Rings Polygon',
            'Single Point Polygon', 'Two Point Polygon',
            'Three Point Polygon Collinear', 'Four Point Polygon Collinear',
            'Single Point Interior Ring Polygon',
            'Empty Points Exterior Becomes Invalid Polygon',
            'Empty Points Interior and Exterior Become Invalid Polygon']),
        ('multipoint_mp', 1, 1, ['Empty MultiPoint']),
        ('multilinestring_ml', 2, 6, [
            'Empty MultiLineString', 'Single Point MultiLineString',
            'Mixed Points MultiLineString',
            'Single Empty Point MultiLineString',
            'Multiple Empty Points MultiLineString',
            'Multiple Empty MultiLineString']),
        ('multipolygon_ma', 5, 12, [
            'Empty MultiPolygon', 'Multiple Empty Rings MultiPolygon',
            'Empty Exterior Regular Rings MultiPolygon',
            'Single Point MultiPolygon', 'Two Point MultiPolygon',
            'Three Point MultiPolygon Collinear',
            'Four Point MultiPolygon Collinear',
            'Single Point Interior Ring MultiPolygon',
            'Empty Points Exterior Becomes Invalid MultiPolygon',
            'Empty Points Interior and Exterior Become Invalid MultiPolygon',
            'Empty MultiPolygon', 'Multiple Empty Part MultiPolygon']
         ),
    ])
    def test_repair_geometry_no_drop(self, check_repair, mem_gpkg, fc_name,
                                     pre_count, post_count, expected_reasons):
        """
        Test Repair Geometry No Drop
        """
        source = check_repair[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        geoms = [g for g, in source.select().fetchall()]
        assert sum([g.is_empty for g in geoms]) == pre_count
        repair_geometry(source, drop_empty=False)
        records = source.select(fields=['REASON']).fetchall()
        assert sum([g.is_empty for g, _ in records]) == post_count
        reasons = [reason for g, reason in records if g.is_empty]
        assert reasons == expected_reasons
    # End test_repair_geometry_no_drop method

    @mark.parametrize('fc_name, pre_count, post_count', [
        ('point_p', 14, 10),
        ('linestring_l', 18, 13),
        ('polygon_a', 21, 11),
        ('multipoint_mp', 14, 11),
        ('multilinestring_ml', 20, 14),
        ('multipolygon_ma', 25, 13),
    ])
    def test_repair_geometry_drop_empty(self, check_repair, mem_gpkg, fc_name,
                                        pre_count, post_count):
        """
        Test Repair Geometry Drop Empty
        """
        source = check_repair[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        assert len(source) == pre_count
        repair_geometry(source, drop_empty=True)
        assert sum([g.is_empty for g, in source.select().fetchall()]) == 0
        assert len(source) == post_count
    # End test_repair_geometry_drop_empty method
# End TestRepairGeometry class


class TestXYTableToPoint:
    """
    Test XY Table to Point
    """
    @mark.parametrize('fields', [
        (POINT_X, POINT_Y, None, None),
        (POINT_X, POINT_Y, POINT_Z, None),
        (POINT_X, POINT_Y, None, POINT_M),
        (POINT_X, POINT_Y, POINT_Z, POINT_M),
    ])
    @mark.parametrize('extent, count', [
        (None, 12_950),
        (Extent.from_bounds(-114, 51, -114.1, 51.15, CRS(4326)), 35),
    ])
    def test_extent(self, inputs, mem_gpkg, fields, extent, count):
        """
        Test XY Table to Point using extent
        """
        source = inputs['xyzm_table']
        target = FeatureClass(geopackage=mem_gpkg, name='out_points')
        crs = CRS(4617)
        x_field, y_field, z_field, m_field = fields
        with Swap(Setting.EXTENT, extent):
            result = xy_table_to_point(
                source, target=target, coordinate_system=crs,
                x_field=x_field, y_field=y_field,
                z_field=z_field, m_field=m_field)
        *_, z_field, m_field = fields
        has_z = z_field is not None
        has_m = m_field is not None
        assert len(result) == count
        assert result.has_z is has_z
        assert result.has_m is has_m
    # End test_extent method

    def test_output_crs(self, inputs, mem_gpkg):
        """
        Test XY Table to Point using extent
        """
        source = inputs['xyzm_table']
        target = FeatureClass(geopackage=mem_gpkg, name='out_points')
        crs = CRS(4617)
        fields = POINT_X, POINT_Y, POINT_Z, POINT_M
        x_field, y_field, z_field, m_field = fields
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(32611)):
            result = xy_table_to_point(
                source, target=target, coordinate_system=crs,
                x_field=x_field, y_field=y_field,
                z_field=z_field, m_field=m_field)
        *_, z_field, m_field = fields
        has_z = z_field is not None
        has_m = m_field is not None
        assert len(result) == 12_950
        assert result.has_z is has_z
        assert result.has_m is has_m

        assert approx(result.extent, abs=0.001) == (
            639364.4375, 5596842.0, 783367.125, 5712288.0)
    # End test_output_crs method
# End TestXYTableToPoint class


class TestXYTableToLine:
    """
    Test XY Table to Line
    """
    @mark.parametrize('name, point_count, crs, count', [
        ('transmission_xy_4617', 0, CRS(4617), 66),
        ('transmission_xy_102179', 0, CRS('ESRI:102179'), 66),
        ('transmission_xy_4617', 10, CRS(4617), 66),
        ('transmission_xy_102179', 10, CRS('ESRI:102179'), 66),
    ])
    def test_planar(self, inputs, mem_gpkg, name, point_count, crs, count):
        """
        Test planar
        """
        source = inputs[name]
        start_x = Field('START_X', data_type=FieldType.real)
        start_y = Field('START_Y', data_type=FieldType.real)
        end_x = Field('END_X', data_type=FieldType.real)
        end_y = Field('END_Y', data_type=FieldType.real)
        target = FeatureClass(geopackage=mem_gpkg, name='out_lines')
        result = xy_to_line(
            source, target=target, coordinate_system=crs,
            start_x_field=start_x, start_y_field=start_y,
            end_x_field=end_x, end_y_field=end_y,
            line_type=LineTypeOption.PLANAR, point_count=point_count)
        assert len(result) == count
    # End test_planar method

    @mark.parametrize('name, point_count, crs, count', [
        ('transmission_xy_4617', 0, CRS(4617), 66),
        ('transmission_xy_102179', 0, CRS('ESRI:102179'), 66),
        ('transmission_xy_4617', 10, CRS(4617), 66),
        ('transmission_xy_102179', 10, CRS('ESRI:102179'), 66),
    ])
    def test_geodesic(self, inputs, mem_gpkg, name, point_count, crs, count):
        """
        Test geodesic
        """
        source = inputs[name]
        start_x = Field('START_X', data_type=FieldType.real)
        start_y = Field('START_Y', data_type=FieldType.real)
        end_x = Field('END_X', data_type=FieldType.real)
        end_y = Field('END_Y', data_type=FieldType.real)
        target = FeatureClass(geopackage=mem_gpkg, name='out_lines')
        result = xy_to_line(
            source, target=target, coordinate_system=crs,
            start_x_field=start_x, start_y_field=start_y,
            end_x_field=end_x, end_y_field=end_y,
            line_type=LineTypeOption.GEODESIC, point_count=point_count)
        assert len(result) == count
    # End test_geodesic method
# End TestXYTableToLine class


class TestFeatureEnvelopeToPolygon:
    """
    Test feature envelope to polygon
    """
    @mark.parametrize('name', [
        'hydro_a',
        'hydro_m_a',
        'hydro_z_a',
        'hydro_zm_a',
        'structures_ma',
        'structures_m_ma',
        'structures_z_ma',
        'structures_zm_ma',
        'transmission_ml',
        'transmission_m_ml',
        'transmission_z_ml',
        'transmission_zm_ml',
        'topography_l',
        'topography_m_l',
        'topography_z_l',
        'topography_zm_l',
        'toponymy_m_mp',
        'toponymy_mp',
        'toponymy_z_mp',
        'toponymy_zm_mp',
    ])
    @mark.parametrize('as_multi_part', [
        True, False
    ])
    def test_geometry_types(self, ntdb_zm_small, mem_gpkg, name, as_multi_part):
        """
        Test geometry types
        """
        source = ntdb_zm_small[name]
        assert not source.is_empty
        target = FeatureClass(geopackage=mem_gpkg, name=f'{name}_{as_multi_part}_env')
        result = feature_envelope_to_polygon(
            source=source, target=target, as_multi_part=as_multi_part)
        assert len(result) == len(source)
        if as_multi_part:
            if name.endswith('_mp'):
                assert not result.is_multi_part
            else:
                assert result.is_multi_part
        else:
            assert not result.is_multi_part
        assert result.has_z is source.has_z
        assert result.has_m is source.has_m
    # End test_geometry_types method

    def test_sans_attrs(self, world_features, mem_gpkg):
        """
        Test sans attributes
        """
        name = 'admin_sans_attr_a'
        source = world_features[name].copy(name='copied', geopackage=mem_gpkg, where_clause='fid <= 10')
        target = FeatureClass(geopackage=mem_gpkg, name=name)
        assert not source.is_empty
        result = feature_envelope_to_polygon(
            source=source, target=target, as_multi_part=False)
        assert len(result) == len(source)
    # End test_sans_attrs method

    @mark.zm
    @mark.parametrize('name', [
        'structures_a',
        'structures_m_a',
        'structures_z_a',
        'structures_zm_a',
        'structures_ma',
        'structures_m_ma',
        'structures_z_ma',
        'structures_zm_ma',
        'toponymy_mp',
        'toponymy_m_mp',
        'toponymy_z_mp',
        'toponymy_zm_mp',
        'transmission_l',
        'transmission_m_l',
        'transmission_z_l',
        'transmission_zm_l',
        'transmission_ml',
        'transmission_m_ml',
        'transmission_z_ml',
        'transmission_zm_ml',
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
    def test_output_zm(self, ntdb_zm_small, mem_gpkg, name, output_z, output_m):
        """
        Test Output ZM
        """
        source = ntdb_zm_small[name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{name}_env')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source)
            exploded = feature_envelope_to_polygon(source=source, target=target)
        assert exploded.shape_type in (
            ShapeType.linestring, ShapeType.point, ShapeType.polygon)
        assert exploded.has_z == zm.z_enabled
        assert exploded.has_m == zm.m_enabled
    # End test_output_zm method

    @mark.transform
    @mark.parametrize('name, extent', [
        ('structures_6654_ma', (-114.4954, 51., -114., 51.2425)),
        ('transmission_6654_m_ml', (-114.5, 51., -114, 51.25)),
        ('toponymy_6654_m_mp', (-114.4926, 51., -114., 51.25)),
        ('structures_10tm_zm_ma', (-114.4954, 51., -114., 51.2425)),
        ('transmission_10tm_z_ml', (-114.5, 51., -114, 51.25)),
        ('toponymy_10tm_z_mp', (-114.4926, 51., -114., 51.25)),
    ])
    def test_output_crs(self, ntdb_zm_small, mem_gpkg, name, extent):
        """
        Test output crs
        """
        source = ntdb_zm_small[name]
        srs_id = 4326
        crs = CRS(srs_id)
        target = FeatureClass(geopackage=mem_gpkg, name=f'{name}_crs')
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs), UseGrids(True):
            result = feature_envelope_to_polygon(source=source, target=target)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert approx(result.extent, abs=0.001) == extent
    # End test_output_crs method

    @mark.parametrize('fc_name, pre_count, post_count', [
        ('structures_6654_a', 1453, 371),
        ('transmission_6654_z_l', 66, 14),
        ('toponymy_6654_z_mp', 1, 1),
    ])
    def test_extent(self, ntdb_zm_small, mem_gpkg, fc_name, pre_count, post_count):
        """
        Test extent
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        crs = CRS(4326)
        assert len(source) == pre_count
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.2, 51.05, -114.05, 51.15, crs)):
            result = feature_envelope_to_polygon(source=source, target=target)
            assert len(result) == post_count
    # End test_extent method
# End TestFeatureEnvelopeToPolygon class


class TestMinimumBoundingGeometry:
    """
    Test Minimum Bounding Geometry
    """
    @mark.parametrize('fc_name, expected', [
        ('admin_a', 6),
        ('admin_mp_a', 6),
        ('admin_lcc_na_a', 6),
        ('admin_lcc_na_mp_a', 6),
    ])
    @mark.parametrize('geometry_type', [
        MinimumGeometryOption.RECTANGLE_BY_AREA,
        MinimumGeometryOption.RECTANGLE_BY_WIDTH,
        MinimumGeometryOption.CONVEX_HULL,
        MinimumGeometryOption.CIRCLE,
        MinimumGeometryOption.ENVELOPE,
    ])
    @mark.parametrize('add_attributes', [
        True,
        False,
    ])
    def test_list_polygon(self, mem_gpkg, buffering, fc_name, expected, geometry_type, add_attributes):
        """
        Test Dissolve List for Polygon
        """
        fields = 'COUNTRY', 'ADMINTYPE', 'LAND_RANK'
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_mbg')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = minimum_bounding_geometry(
                source, target=target, geometry_type=geometry_type,
                add_geometric_attributes=add_attributes,
                group_option=GroupOption.LIST, group_fields=fields)
            assert len(result) == expected
    # End test_list_polygon method

    @mark.parametrize('add_attributes', [
        True,
        False,
    ])
    def test_sans_attr(self, mem_gpkg, buffering, add_attributes):
        """
        Test Polygon with no Attributes
        """
        source = buffering['admin_sans_attr_a']
        target = FeatureClass(geopackage=mem_gpkg, name='sans_all_mbg')
        additional = 3 if add_attributes else 0
        extent = Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))
        with Swap(Setting.EXTENT, extent):
            result = minimum_bounding_geometry(
                source, target=target, group_option=GroupOption.ALL,
                add_geometric_attributes=add_attributes,
                geometry_type=MinimumGeometryOption.RECTANGLE_BY_AREA)
            assert len(result) == 1
            assert len(target.fields) == len(source.fields) + additional

        # NOTE include orig fid
        additional += 1
        target = FeatureClass(geopackage=mem_gpkg, name='sans_none_mbg')
        with Swap(Setting.EXTENT, extent):
            result = minimum_bounding_geometry(
                source, target=target, group_option=GroupOption.NONE,
                add_geometric_attributes=add_attributes,
                geometry_type=MinimumGeometryOption.RECTANGLE_BY_AREA)
            assert len(result) == 11
            assert len(target.fields) == len(source.fields) + additional
    # End test_sans_attr method

    @mark.zm
    @mark.parametrize('fc_name, group_option, extent, count', [
        ('admin_a', GroupOption.NONE, (-2306408.75, 1019980.4375, -778207.0625, 2711139.0), 2),
        ('roads_l', GroupOption.NONE, (-1388068.375, 1022292.6875, -891346.5625, 1617412.625), 967),
        ('airports_p', GroupOption.ALL, (-1358503.75, 1003277.9375, -998982.9375, 1540229.25), 1),
    ])
    def test_output_settings(self, mem_gpkg, buffering, fc_name, group_option, extent, count):
        """
        Test minimum bounding geometry with Z output and M output + reprojecting features
        """
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_mbg')
        with (Swap(Setting.EXTENT, Extent.from_bounds(-116, 48, -110, 54, crs=CRS(4326))),
              Swap(Setting.OUTPUT_M_OPTION, OutputMOption.ENABLED),
              Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.ENABLED),
              Swap(Setting.Z_VALUE, 123.456),
              Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS.from_authority('ESRI', 102009))):
            result = minimum_bounding_geometry(
                source, target=target, group_option=group_option,
                geometry_type=MinimumGeometryOption.ENVELOPE)
            assert result.has_z
            assert result.has_m
            assert result.spatial_reference_system.srs_id == 102009
            assert approx(result.extent, abs=1) == extent
            assert len(result) == count
    # End test_output_settings method

    @mark.parametrize('geometry_type, count', [
        (MinimumGeometryOption.RECTANGLE_BY_AREA, 2),
        (MinimumGeometryOption.RECTANGLE_BY_WIDTH, 2),
        (MinimumGeometryOption.CONVEX_HULL, 2),
        (MinimumGeometryOption.CIRCLE, 4),
        (MinimumGeometryOption.ENVELOPE, 4),
    ])
    @mark.parametrize('add_attributes', [
        True,
        False,
    ])
    def test_list_line(self, mem_gpkg, buffering, geometry_type, count, add_attributes):
        """
        Test List for line
        """
        fields = 'ISO_CC', 'RANK'
        source = buffering['roads_l']
        target = FeatureClass(geopackage=mem_gpkg, name='roads_mbg')
        with Swap(Setting.EXTENT, Extent.from_bounds(-116, 48, -110, 54, crs=CRS(4326))):
            result = minimum_bounding_geometry(
                source, target=target, geometry_type=geometry_type,
                add_geometric_attributes=add_attributes,
                group_option=GroupOption.LIST, group_fields=fields)
        assert len(result) == count
    # End test_list_line method

    @mark.parametrize('fc_name', [
        'airports_p',
        'airports_mp_p',
        'airports_lcc_na_p',
        'airports_lcc_na_mp_p',
    ])
    @mark.parametrize('geometry_type', [
        MinimumGeometryOption.RECTANGLE_BY_AREA,
        MinimumGeometryOption.RECTANGLE_BY_WIDTH,
        MinimumGeometryOption.CONVEX_HULL,
        MinimumGeometryOption.CIRCLE,
        MinimumGeometryOption.ENVELOPE,
    ])
    @mark.parametrize('add_attributes', [
        True,
        False,
    ])
    def test_list_point(self, mem_gpkg, buffering, fc_name, geometry_type, add_attributes):
        """
        Test List Point
        """
        if 'mp' in fc_name:
            fields = 'ISO_CC'
        else:
            fields = 'ISO_CC', 'IATA'
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_mbg')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = minimum_bounding_geometry(
                source, target=target, geometry_type=geometry_type,
                add_geometric_attributes=add_attributes,
                group_option=GroupOption.LIST, group_fields=fields)
            assert len(result) and len(result) < len(source)
    # End test_list_point method

    @mark.parametrize('fc_name', [
        'admin_a',
        'admin_mp_a',
        'admin_lcc_na_a',
        'admin_lcc_na_mp_a',
    ])
    @mark.parametrize('geometry_type', [
        MinimumGeometryOption.RECTANGLE_BY_AREA,
        MinimumGeometryOption.RECTANGLE_BY_WIDTH,
        MinimumGeometryOption.CONVEX_HULL,
        MinimumGeometryOption.CIRCLE,
        MinimumGeometryOption.ENVELOPE,
    ])
    @mark.parametrize('add_attributes', [
        True,
        False,
    ])
    def test_all_polygon(self, mem_gpkg, buffering, fc_name, geometry_type, add_attributes):
        """
        Test All for Polygon
        """
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_mbg')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = minimum_bounding_geometry(
                source, target=target, geometry_type=geometry_type,
                add_geometric_attributes=add_attributes,
                group_option=GroupOption.ALL)
            assert len(result) == 1
    # End test_all_polygon method

    @mark.parametrize('geometry_type', [
        MinimumGeometryOption.RECTANGLE_BY_AREA,
        MinimumGeometryOption.RECTANGLE_BY_WIDTH,
        MinimumGeometryOption.CONVEX_HULL,
        MinimumGeometryOption.CIRCLE,
        MinimumGeometryOption.ENVELOPE,
    ])
    @mark.parametrize('add_attributes', [
        True,
        False,
    ])
    def test_all_line(self, mem_gpkg, buffering, geometry_type, add_attributes):
        """
        Test All for line
        """
        source = buffering['roads_l']
        target = FeatureClass(geopackage=mem_gpkg, name='roads_mbg')
        with Swap(Setting.EXTENT, Extent.from_bounds(27, 45, 56, 70, crs=CRS(4326))):
            result = minimum_bounding_geometry(
                source, target=target, add_geometric_attributes=add_attributes,
                geometry_type=geometry_type, group_option=GroupOption.ALL)
            assert len(result) == 1
    # End test_all_line method

    @mark.parametrize('fc_name', [
        'airports_p',
        'airports_mp_p',
        'airports_lcc_na_p',
        'airports_lcc_na_mp_p',
    ])
    @mark.parametrize('geometry_type', [
        MinimumGeometryOption.RECTANGLE_BY_AREA,
        MinimumGeometryOption.RECTANGLE_BY_WIDTH,
        MinimumGeometryOption.CONVEX_HULL,
        MinimumGeometryOption.CIRCLE,
        MinimumGeometryOption.ENVELOPE,
    ])
    @mark.parametrize('add_attributes', [
        True,
        False,
    ])
    def test_all_point(self, mem_gpkg, buffering, fc_name, geometry_type, add_attributes):
        """
        Test All Point
        """
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_mbg')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = minimum_bounding_geometry(
                source, target=target, add_geometric_attributes=add_attributes,
                geometry_type=geometry_type, group_option=GroupOption.ALL)
            assert len(result) == 1
    # End test_all_point method

    @mark.parametrize('fc_name, expected', [
        ('admin_a', 488),
        ('admin_mp_a', 11),
        ('admin_lcc_na_a', 474),
        ('admin_lcc_na_mp_a', 11),
    ])
    @mark.parametrize('geometry_type', [
        MinimumGeometryOption.RECTANGLE_BY_AREA,
        MinimumGeometryOption.RECTANGLE_BY_WIDTH,
        MinimumGeometryOption.CONVEX_HULL,
        MinimumGeometryOption.CIRCLE,
        MinimumGeometryOption.ENVELOPE,
    ])
    @mark.parametrize('add_attributes', [
        True,
        param(False, marks=mark.large),
    ])
    def test_none_polygon(self, mem_gpkg, buffering, fc_name, expected, geometry_type, add_attributes):
        """
        Test None for Polygon
        """
        source = buffering[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_mbg')
        with Swap(Setting.EXTENT, Extent.from_bounds(-145, 45, -90, 85, crs=CRS(4326))):
            result = minimum_bounding_geometry(
                source, target=target, add_geometric_attributes=add_attributes,
                geometry_type=geometry_type, group_option=GroupOption.NONE)
            assert len(result) == expected
    # End test_none_polygon method

    @mark.parametrize('geometry_type', [
        MinimumGeometryOption.RECTANGLE_BY_AREA,
        MinimumGeometryOption.RECTANGLE_BY_WIDTH,
        MinimumGeometryOption.CONVEX_HULL,
        MinimumGeometryOption.CIRCLE,
        MinimumGeometryOption.ENVELOPE,
    ])
    @mark.parametrize('add_attributes', [
        True,
        False,
    ])
    def test_none_line(self, mem_gpkg, buffering, geometry_type, add_attributes):
        """
        Test None for line
        """
        source = buffering['roads_l']
        target = FeatureClass(geopackage=mem_gpkg, name='roads_mbg')
        with Swap(Setting.EXTENT, Extent.from_bounds(27, 45, 56, 70, crs=CRS(4326))):
            result = minimum_bounding_geometry(
                source, target=target, add_geometric_attributes=add_attributes,
                geometry_type=geometry_type, group_option=GroupOption.NONE)
            assert len(result)
    # End test_none_line method
# End TestMinimumBoundingGeometry class


if __name__ == '__main__':  # pragma: no cover
    pass
