# -*- coding: utf-8 -*-
"""
Test Editing
"""
from fudgeo import Field
from fudgeo.enumeration import FieldType
from pytest import mark

from spyops.crs.unit import DecimalDegrees, Feet, Meters
from spyops.editing import generalize
from spyops.management import add_field, calculate_geometry_attributes
from spyops.shared.enumeration import GeometryAttribute

pytestmark = [mark.editing]


class TestGeneralize:
    """
    Test Generalize
    """
    @mark.parametrize('fc_name, tolerance', [
        ('hydro_lcc_a', Meters(100)),
        ('hydro_lcc_m_a', 100),
        ('hydro_lcc_zm_a', 100),
        ('hydro_lcc_z_a', Feet(300)),
        ('topography_l', DecimalDegrees(0.0001)),
    ])
    @mark.parametrize('preserve', [
        True,
        False
    ])
    def test_where_clause(self, mem_gpkg, ntdb_zm_small, fc_name, tolerance, preserve):
        """
        Test generalize using where clause
        """
        where = """PROVIDER >= 2"""
        source = ntdb_zm_small[fc_name].copy(fc_name, geopackage=mem_gpkg)
        field = Field('POINT_COUNT', data_type=FieldType.integer)
        add_field(source, fields=[field])
        attr = GeometryAttribute.POINT_COUNT
        calculate_geometry_attributes(
            source, field=field, geometry_attribute=attr, where_clause=where)
        sql = f"""SELECT SUM(POINT_COUNT) FROM {source.name}"""
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            start_count, = cursor.fetchone()
        generalize(source, tolerance=tolerance, preserve_topology=preserve,
                   where_clause=where)
        calculate_geometry_attributes(
            source, field=field, geometry_attribute=attr, where_clause=where)
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            end_count, = cursor.fetchone()
        assert start_count > end_count
    # End test_where_clause method
# End TestGeneralize class


if __name__ == '__main__':  # pragma: no cover
    pass
