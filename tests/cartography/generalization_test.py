# -*- coding: utf-8 -*-
"""
Tests for Generalization
"""


from fudgeo import FeatureClass, Field
from fudgeo.enumeration import FieldType
from pyproj import CRS
from pytest import mark

from spyops.cartography import simplify_line
from spyops.crs.unit import Meters
from spyops.environment import OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.management import add_field, calculate_geometry_attributes
from spyops.shared.enumeration import GeometryAttribute


class TestSimplifyLine:
    """
    Test Simplify Line
    """
    @mark.parametrize('tolerance', [
        Meters(50),
        0.0001
    ])
    @mark.parametrize('xy_tolerance', [
        None,
        0.0001
    ])
    def test_xy_tolerance(self, mem_gpkg, ntdb_zm_small, tolerance, xy_tolerance):
        """
        Test simplify line using xy tolerance
        """
        name = 'topography_l'
        source = ntdb_zm_small[name].copy(name, geopackage=mem_gpkg)
        target = FeatureClass(mem_gpkg, 'output_fc')
        field = Field('POINT_COUNT', data_type=FieldType.integer)
        add_field(source, fields=[field])
        attr = GeometryAttribute.POINT_COUNT
        calculate_geometry_attributes(
            source, field=field, geometry_attribute=attr)
        sql = """SELECT SUM(POINT_COUNT) FROM {}"""
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql.format(source.name))
            start_count, = cursor.fetchone()
        simplify_line(source, target=target, tolerance=tolerance, xy_tolerance=xy_tolerance)
        calculate_geometry_attributes(
            target, field=field, geometry_attribute=attr)
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql.format(target.name))
            end_count, = cursor.fetchone()
        assert start_count > end_count
    # End test_xy_tolerance method

    @mark.zm
    @mark.parametrize('fc_name', [
        'topography_l',
        'topography_m_l',
        'topography_z_l',
        'topography_zm_l',
    ])
    def test_output_crs_and_zm(self, mem_gpkg, ntdb_zm_small, fc_name):
        """
        Test output CRS and ZM
        """
        source = ntdb_zm_small[fc_name].copy(fc_name, geopackage=mem_gpkg)
        target = FeatureClass(mem_gpkg, 'output_fc')
        epsg_code = 6654
        with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(epsg_code)),
              Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.ENABLED),
              Swap(Setting.OUTPUT_M_OPTION, OutputMOption.ENABLED)):
            simplify_line(source, target=target, tolerance=Meters(100))
            assert target.has_z
            assert target.has_m
            assert target.spatial_reference_system.srs_id == epsg_code
    # End test_output_crs_and_zm method
# End TestSimplifyLine class


if __name__ == '__main__':  # pragma: no cover
    pass
