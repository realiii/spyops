# -*- coding: utf-8 -*-
"""
Tests for GPS Conversion
"""


from fudgeo import FeatureClass
from fudgeo.enumeration import GeometryType
from pyproj import CRS
from pytest import mark, approx

from spyops.conversion import features_to_gpx, gpx_to_features
from spyops.environment import Setting
from spyops.environment.context import Swap

pytestmark = [mark.conversion, mark.gps]


class TestFeaturesToGPX:
    """
    Test Features to GPX
    """
    @mark.parametrize('fc_name, approx_size', [
        ('gps_p', 157_000),
        ('gps_lcc_p', 157_000),
        ('gps_mp', 157_000),
        ('gps_l', 65_000),
        ('gps_lcc_l', 65_000),
        ('gps_ml', 65_000),
    ])
    def test_sans_attr(self, inputs, tmp_path, fc_name, approx_size):
        """
        Test sans attributes
        """
        fc = inputs[fc_name]
        path = tmp_path.joinpath(fc_name)
        output = features_to_gpx(fc, target=path)
        assert output.is_file()
        assert output.stat().st_size > approx_size
    # End test_sans_attr method

    @mark.parametrize('fc_name, fields, approx_size', [
        ('gps_p', ('name', 'system', 'distance', 'dt'), 464_000),
        ('gps_lcc_p', ('name', 'system', 'distance', 'dt'), 464_000),
        ('gps_mp', ('name', 'first_system', 'avg_distance', None), 361_000),
        ('gps_l', ('name', 'system', 'depth', 'day'), 129_000),
        ('gps_lcc_l', ('name', 'system', 'depth', 'day'), 129_000),
        ('gps_ml', ('name', 'first_system', 'avg_depth', 'first_day'), 129_000),
    ])
    def test_with_attr(self, inputs, tmp_path, fc_name, fields, approx_size):
        """
        Test with attributes
        """
        fc = inputs[fc_name]
        path = tmp_path.joinpath(fc_name)
        name, description, elevation, date = fields
        output = features_to_gpx(
            fc, target=path, name_field=name, description_field=description,
            z_field=elevation, date_field=date)
        assert output.is_file()
        assert output.stat().st_size > approx_size
    # End test_with_attr method
# End TestFeaturesToGPX class


class TestGPXToFeatures:
    """
    Test GPX to Features
    """
    @mark.parametrize('as_points, name, feature_count, name_null_count', [
        (False, 'line_attr.gpx', 4, 0),
        (False, 'line_sans_attr.gpx', 4, 4),
        (False, 'multiline_attr.gpx', 66, 0),
        (False, 'multiline_attr_dt.gpx', 66, 0),
        (False, 'multiline_sans_attr.gpx', 4, 4),
        (True, 'line_attr.gpx', 1744, 1744),
        (True, 'line_sans_attr.gpx', 872, 872),
        (True, 'multiline_attr.gpx', 2255, 2255),
        (True, 'multiline_attr_dt.gpx', 2255, 2255),
        (True, 'multiline_sans_attr.gpx', 872, 872),
    ])
    def test_line(self, gpx_path, mem_gpkg, as_points, name, feature_count, name_null_count):
        """
        Test line
        """
        path = gpx_path / name
        assert path.is_file()
        fc_name = 'line_l'
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        gpx_to_features(path, target=target, as_points=as_points)
        assert len(target) == feature_count
        with target.geopackage.connection as cin:
            cursor = cin.execute(f"""
                SELECT COUNT(*) AS CNT
                FROM {fc_name} 
                WHERE NAME IS NULL
            """)
            assert cursor.fetchone()[0] == name_null_count
        assert target.spatial_reference_system.srs_id == 4326
        if as_points:
            assert target.shape_type == GeometryType.point
        else:
            assert target.shape_type == GeometryType.linestring
        assert target.has_z
    # End test_line method

    @mark.parametrize('name, feature_count, name_null_count', [
        ('multipoint_attr.gpx', 142, 0),
        ('multipoint_sans_attr.gpx', 142, 142),
        ('point_2d_sans_attr.gpx', 3912, 3912),
        ('point_all_attr.gpx', 3912, 0),
        ('point_attr_geom_elev.gpx', 3912, 0),
        ('point_sans_attr.gpx', 3912, 3912),
    ])
    def test_point(self, gpx_path, mem_gpkg, name, feature_count, name_null_count):
        """
        Test point
        """
        path = gpx_path / name
        assert path.is_file()
        fc_name = 'point_p'
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        gpx_to_features(path, target=target, as_points=True)
        assert len(target) == feature_count
        with target.geopackage.connection as cin:
            cursor = cin.execute(f"""
                SELECT COUNT(*) AS CNT
                FROM {fc_name} 
                WHERE NAME IS NULL
            """)
            assert cursor.fetchone()[0] == name_null_count
        assert target.spatial_reference_system.srs_id == 4326
        assert target.shape_type == GeometryType.point
        assert target.has_z
    # End test_point method

    @mark.parametrize('as_points, name, extent', [
        (True, 'point_attr_geom_elev.gpx', (-12746046.0, 6621341.5, -12690535.0, 6665587.5)),
        (True, 'line_attr.gpx', (-12745973.0, 6621284.5, -12690313.0, 6665627.0)),
        (False, 'line_attr.gpx', (-12745973.0, 6621284.5, -12690313.0, 6665627.0)),
    ])
    def test_output_coordinate_system(self, gpx_path, mem_gpkg, as_points, name, extent):
        """
        Test output coordinate system
        """
        path = gpx_path / name
        assert path.is_file()
        target = FeatureClass(geopackage=mem_gpkg, name='fc')
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(3857)):
            gpx_to_features(path, target=target, as_points=as_points)
            assert target.spatial_reference_system.srs_id == 3857
            assert approx(target.extent, abs=1) == extent
    # End test_output_coordinate_system method
# End TestGPXToFeatures class


if __name__ == '__main__':  # pragma: no cover
    pass
