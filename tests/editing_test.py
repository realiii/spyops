# -*- coding: utf-8 -*-
"""
Test Editing
"""


from fudgeo import Field
from fudgeo.enumeration import FieldType
from pytest import approx, mark

from spyops.crs.unit import DecimalDegrees, Feet, Meters
from spyops.editing import densify, erase_point, flip, generalize
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
        ('topography_m_l', Meters(100)),
        ('topography_zm_l', Feet(300)),
        ('topography_z_l', 0.0001),
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


class TestDensify:
    """
    Test Densify
    """
    @mark.parametrize('fc_name, distance', [
        ('hydro_lcc_a', Meters(100)),
        ('hydro_lcc_m_a', 100),
        ('hydro_lcc_zm_a', 100),
        ('hydro_lcc_z_a', Feet(300)),
        ('structures_a', Meters(100)),
        ('structures_m_a', 0.0001),
        ('structures_zm_a', 0.0001),
        ('structures_z_a', Feet(300)),
        ('structures_10tm_ma', Feet(300)),
        ('structures_10tm_m_ma', Feet(300)),
        ('structures_10tm_z_ma', Feet(300)),
        ('structures_10tm_zm_ma', Feet(300)),
        ('topography_l', DecimalDegrees(0.0001)),
        ('topography_m_l', Meters(100)),
        ('topography_zm_l', Feet(300)),
        ('topography_z_l', 0.0001),
        ('transmission_l', DecimalDegrees(0.0001)),
        ('transmission_m_l', Meters(100)),
        ('transmission_zm_l', Feet(300)),
        ('transmission_z_l', 0.0001),
        ('transmission_10tm_ml', Meters(100)),
        ('transmission_10tm_m_ml', Meters(100)),
        ('transmission_10tm_z_ml', Meters(100)),
        ('transmission_10tm_zm_ml', Meters(100)),
    ])
    def test_where_clause(self, mem_gpkg, ntdb_zm_small, fc_name, distance):
        """
        Test densify using where clause
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
        densify(source, distance=distance, where_clause=where)
        calculate_geometry_attributes(
            source, field=field, geometry_attribute=attr, where_clause=where)
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            end_count, = cursor.fetchone()
        assert start_count < end_count
    # End test_where_clause method
# End TestDensify class


class TestFlip:
    """
    Test Flip
    """
    @mark.parametrize('fc_name', [
        'topography_l',
        'topography_m_l',
        'topography_zm_l',
        'topography_z_l',
        'transmission_10tm_ml',
        'transmission_10tm_m_ml',
        'transmission_10tm_z_ml',
        'transmission_10tm_zm_ml',
    ])
    def test_where_clause(self, mem_gpkg, ntdb_zm_small, fc_name):
        """
        Test flip using where clause
        """
        where = """PROVIDER >= 2"""
        source = ntdb_zm_small[fc_name].copy(fc_name, geopackage=mem_gpkg)
        field = Field('LINE_START_X', data_type=FieldType.integer)
        add_field(source, fields=[field])
        attr = GeometryAttribute.LINE_START_X
        calculate_geometry_attributes(
            source, field=field, geometry_attribute=attr, where_clause=where)
        sql = f"""SELECT AVG(LINE_START_X) FROM {source.name}"""
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            pre_x, = cursor.fetchone()
        flip(source, where_clause=where)
        calculate_geometry_attributes(
            source, field=field, geometry_attribute=attr, where_clause=where)
        with source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            post_x, = cursor.fetchone()
        if '10tm' in fc_name:
            tol = 1
        else:
            tol = 10**-6
        assert approx(post_x, abs=tol) != pre_x
    # End test_where_clause method
# End TestFlip class


class TestErasePoint:
    """
    Test Erase Point
    """
    @mark.parametrize('name, remove_inside, expected', [
        ('structures_p', False, 918),
        ('structures_m_p', False, 918),
        ('structures_z_p', False, 918),
        ('structures_zm_p', False, 918),
        ('structures_p', True, 2994),
        ('structures_m_p', True, 2994),
        ('structures_z_p', True, 2994),
        ('structures_zm_p', True, 2994),
    ])
    def test_points(self, mem_gpkg, ntdb_zm_tile, name, remove_inside, expected):
        """
        Test Points
        """
        source = ntdb_zm_tile[name].copy(name, geopackage=mem_gpkg)
        count = source.count
        operator = ntdb_zm_tile['index_a'].copy(
            'index_subset_a', geopackage=mem_gpkg, where_clause="""FID = 5""")
        erase_point(source, operator, remove_inside=remove_inside)
        assert source.count < count
        assert source.count == expected
    # End test_points method    
    
    @mark.parametrize('name, remove_inside, expected', [
        ('toponymy_mp', False, 2),
        ('toponymy_m_mp', False, 2),
        ('toponymy_z_mp', False, 2),
        ('toponymy_zm_mp', False, 2),
        ('toponymy_mp', True, 6),
        ('toponymy_m_mp', True, 6),
        ('toponymy_z_mp', True, 6),
        ('toponymy_zm_mp', True, 6),
    ])
    def test_multi_points(self, mem_gpkg, ntdb_zm_tile, name, remove_inside, expected):
        """
        Test Multi Points
        """
        source = ntdb_zm_tile[name].copy(name, geopackage=mem_gpkg)
        count = source.count
        operator = ntdb_zm_tile['index_a'].copy(
            'index_subset_a', geopackage=mem_gpkg, where_clause="""FID IN (1, 5)""")
        erase_point(source, operator, remove_inside=remove_inside)
        assert source.count < count
        assert source.count == expected
    # End test_multi_points method
# End TestErasePoint class


if __name__ == '__main__':  # pragma: no cover
    pass
