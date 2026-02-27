# -*- coding: utf-8 -*-
"""
Test Check Geometry
"""


from collections import defaultdict

from pytest import mark, param

from spyops.geometry.check import check_feature_class_geometry
from spyops.shared.enumeration import ALL_GEOM_CHECKS, GeometryCheck

pytestmark = [mark.geometry]


class TestCheckFeatureClassGeometry:
    """
    Test Check Feature Class Geometry
    """
    @mark.parametrize('fc_name, counts', [
        ('point_p', {'EMPTY': 4, 'EXTENT': 1}),
        ('linestring_l',
         {'EMPTY': 1, 'EMPTY_POINT': 5, 'EXTENT': 1,
          'POINT_COUNT': 2, 'REPEATED_XY': 1}),
        ('polygon_a',
         {'EMPTY': 1, 'EMPTY_POINT': 4, 'EMPTY_RING': 3, 'EXTENT': 1,
          'ORIENTATION': 15, 'OUTSIDE_RING': 2, 'OVERLAP_RING': 1,
          'POINT_COUNT': 7, 'REPEATED_XY': 7, 'SELF_INTERSECTION': 4,
          'UNCLOSED': 6}),
        ('multipoint_mp', {'EXTENT': 1, 'EMPTY': 1, 'EMPTY_POINT': 3}),
        ('multilinestring_ml',
         {'EMPTY': 1, 'EMPTY_PART': 2, 'EMPTY_POINT': 5, 'EXTENT': 1,
          'POINT_COUNT': 4}),
        ('multipolygon_ma',
         {'EMPTY': 1, 'EMPTY_PART': 3, 'EMPTY_POINT': 5, 'EMPTY_RING': 3,
          'EXTENT': 1, 'ORIENTATION': 17, 'OUTSIDE_RING': 2, 'OVERLAP_RING': 1,
          'POINT_COUNT': 7, 'REPEATED_XY': 8, 'SELF_INTERSECTION': 4,
          'UNCLOSED': 6}),
    ])
    def test_check_repair(self, check_repair, mem_gpkg, fc_name, counts):
        """
        Test check repair
        """
        source = check_repair[fc_name]
        records = check_feature_class_geometry(source, options=ALL_GEOM_CHECKS)
        grouper = defaultdict(int)
        for _, name in records:
            grouper[name] += 1
        assert grouper == counts
    # End test_check_repair method

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
    def test_check_extent(self, world_features, fc_name, count):
        """
        Test Check Extent
        """
        fc = world_features[fc_name]
        records = check_feature_class_geometry(
            fc, options=GeometryCheck.EXTENT)
        assert len(records) == count
    # End test_check_extent function

    @mark.parametrize('fc_name, count', [
        param('admin_a', 0, marks=mark.slow),
        ('continent_a', 0),
        param('country_a', 0, marks=mark.slow),
        ('disputed_boundaries_l', 0),
        ('drainage_l', 0),
        ('geogrid_l', 0),
        ('lakes_a', 0),
        param('latlong_l', 0, marks=mark.slow),
        ('railroads_l', 0),
        ('region_a', 0),
        ('rivers_l', 0),
        param('roads_l', 0, marks=mark.slow),
        ('utmzone_a', 0),
        ('airports_p', 0),
        ('cities_p', 0),
        ('admin_mp_a', 0),
        ('airports_mp_p', 0),
        ('roads_mp_l', 0),
        ('roads_ml', 0),
    ])
    def test_check_empty_feature(self, world_features, fc_name, count):
        """
        Test Check Empty Feature
        """
        fc = world_features[fc_name]
        records = check_feature_class_geometry(
            fc, options=GeometryCheck.EMPTY)
        assert len(records) == count
    # End test_check_empty_feature method

    @mark.parametrize('fc_name, count', [
        ('admin_mp_a', 0),
        ('airports_mp_p', 0),
        ('roads_mp_l', 0),
        ('roads_ml', 0),
    ])
    def test_check_empty_part(self, world_features, fc_name, count):
        """
        Test Check Empty Part
        """
        fc = world_features[fc_name]
        records = check_feature_class_geometry(
            fc, options=GeometryCheck.EMPTY_PART)
        assert len(records) == count
    # End test_check_empty_part method

    @mark.parametrize('fc_name, count', [
        param('admin_a', 0, marks=mark.slow),
        ('continent_a', 0),
        param('country_a', 0, marks=mark.slow),
        ('lakes_a', 0),
        ('region_a', 0),
        ('utmzone_a', 0),
        param('admin_mp_a', 0, marks=mark.slow),
        ('airports_mp_p', 0),
    ])
    def test_check_empty_ring(self, world_features, fc_name, count):
        """
        Test Check Empty Ring
        """
        fc = world_features[fc_name]
        records = check_feature_class_geometry(
            fc, options=GeometryCheck.EMPTY_RING)
        assert len(records) == count
    # End test_check_empty_ring method

    @mark.parametrize('fc_name, count', [
        param('admin_a', 0, marks=mark.slow),
        ('continent_a', 0),
        param('country_a', 0, marks=mark.slow),
        ('disputed_boundaries_l', 0),
        ('drainage_l', 0),
        ('geogrid_l', 0),
        ('lakes_a', 0),
        param('latlong_l', 0, marks=mark.slow),
        ('railroads_l', 0),
        ('region_a', 0),
        ('rivers_l', 0),
        param('roads_l', 0, marks=mark.slow),
        ('utmzone_a', 0),
        ('airports_p', 0),
        ('cities_p', 0),
        ('admin_mp_a', 0),
        ('airports_mp_p', 0),
        param('roads_mp_l', 0, marks=mark.slow),
        ('roads_ml', 0),
    ])
    def test_check_empty_point(self, world_features, fc_name, count):
        """
        Test Check Empty Point
        """
        fc = world_features[fc_name]
        records = check_feature_class_geometry(
            fc, options=GeometryCheck.EMPTY_POINT)
        assert len(records) == count
    # End test_check_empty_point method

    @mark.parametrize('fc_name, counts', [
        param('admin_a', (0, 0, 0, 0, 207, 0), marks=mark.slow),
        ('continent_a', (0, 0, 0, 0, 0, 0)),
        param('country_a', (0, 0, 0, 0, 162, 0), marks=mark.slow),
        ('lakes_a', (0, 0, 0, 0, 0, 0)),
        ('region_a', (0, 0, 0, 0, 0, 0)),
        ('utmzone_a', (0, 0, 0, 0, 0, 0)),
        param('admin_mp_a', (0, 0, 0, 0, 82, 0), marks=mark.slow),
        ('airports_mp_p', (0, 0, 0, 0, 0, 0)),
    ])
    def test_check_polygon(self, world_features, fc_name, counts):
        """
        Test Check Polygon
        """
        fc = world_features[fc_name]
        options = (
            GeometryCheck.ORIENTATION | GeometryCheck.UNCLOSED |
            GeometryCheck.SELF_INTERSECTION | GeometryCheck.OUTSIDE_RING |
            GeometryCheck.OVERLAP_RING | GeometryCheck.POINT_COUNT
        )
        records = check_feature_class_geometry(fc, options=options)
        assert len(records) == sum(counts)
        checks = (GeometryCheck.ORIENTATION, GeometryCheck.UNCLOSED,
                  GeometryCheck.SELF_INTERSECTION, GeometryCheck.OUTSIDE_RING,
                  GeometryCheck.OVERLAP_RING, GeometryCheck.POINT_COUNT)
        names = [check.name for check in checks]
        counter = defaultdict(int)
        for _, name in records:
            counter[name] += 1
        assert tuple(counter[n] for n in names) == counts
    # End test_check_polygon method

    @mark.parametrize('fc_name, count', [
        ('disputed_boundaries_l', 0),
        ('drainage_l', 0),
        ('geogrid_l', 0),
        param('latlong_l', 0, marks=mark.slow),
        ('railroads_l', 0),
        ('rivers_l', 0),
        param('roads_l', 0, marks=mark.slow),
        ('roads_mp_l', 0),
        ('roads_ml', 0),
    ])
    def test_check_line(self, world_features, fc_name, count):
        """
        Test Check Line
        """
        fc = world_features[fc_name]
        records = check_feature_class_geometry(
            fc, options=GeometryCheck.POINT_COUNT)
        assert len(records) == count
    # End test_check_line function

    @mark.parametrize('fc_name, count', [
        ('hydro_a', 0),
        ('structures_a', 0),
        ('structures_m_a', 0),
        ('structures_m_ma', 0),
        ('structures_ma', 0),
        ('structures_p', 0),
        ('structures_vcs_z_a', 0),
        ('structures_vcs_z_ma', 0),
        ('structures_vcs_zm_a', 0),
        ('structures_vcs_zm_ma', 0),
        ('structures_z_a', 0),
        ('structures_z_ma', 0),
        ('structures_zm_a', 0),
        ('structures_zm_ma', 0),
        ('topography_l', 0),
        ('toponymy_mp', 0),
        ('toponymy_p', 0),
        ('toponymy_vcs_z_mp', 0),
        ('toponymy_vcs_z_p', 0),
        ('toponymy_z_mp', 0),
        ('toponymy_z_p', 0),
        ('transmission_l', 0),
        ('transmission_m_l', 0),
        ('transmission_ml', 0),
        ('transmission_p', 0),
        ('transmission_vcs_z_l', 0),
        ('transmission_vcs_z_ml', 0),
        ('transmission_vcs_zm_l', 0),
        ('transmission_z_l', 0),
        ('transmission_zm_l', 0),
    ])
    def test_check_nan_z(self, ntdb_zm_meh_small, fc_name, count):
        """
        Test check nan z
        """
        fc = ntdb_zm_meh_small[fc_name]
        records = check_feature_class_geometry(
            fc, options=GeometryCheck.NAN_Z)
        assert len(records) == count
    # End test_check_nan_z method

    @mark.parametrize('fc_name, count', [
        ('hydro_a', 0),
        ('structures_a', 0),
        ('structures_m_a', 1453),
        ('structures_m_ma', 18),
        ('structures_ma', 0),
        ('structures_p', 0),
        ('structures_vcs_z_a', 0),
        ('structures_vcs_z_ma', 0),
        ('structures_vcs_zm_a', 1453),
        ('structures_vcs_zm_ma', 18),
        ('structures_z_a', 0),
        ('structures_z_ma', 0),
        ('structures_zm_a', 1453),
        ('structures_zm_ma', 18),
        ('topography_l', 0),
        ('toponymy_mp', 0),
        ('toponymy_p', 0),
        ('toponymy_vcs_z_mp', 0),
        ('toponymy_vcs_z_p', 0),
        ('toponymy_z_mp', 0),
        ('toponymy_z_p', 0),
        ('transmission_l', 0),
        ('transmission_m_l', 66),
        ('transmission_ml', 0),
        ('transmission_p', 0),
        ('transmission_vcs_z_l', 0),
        ('transmission_vcs_z_ml', 0),
        ('transmission_vcs_zm_l', 66),
        ('transmission_z_l', 0),
        ('transmission_zm_l', 66),
    ])
    def test_check_nan_m(self, ntdb_zm_meh_small, fc_name, count):
        """
        Test check nan m
        """
        fc = ntdb_zm_meh_small[fc_name]
        records = check_feature_class_geometry(
            fc, options=GeometryCheck.NAN_M)
        assert len(records) == count
    # End test_check_nan_m method

    @mark.parametrize('fc_name, counts', [
        ('structures_m_ma', (18, 16, 0, 0)),
        ('structures_zm_ma', (18, 16, 1, 0)),
        ('hydro_m_a', (382, 1, 0, 0)),
        ('hydro_zm_a', (382, 1, 0, 0)),
        ('structures_m_a', (1453, 4, 0, 0)),
        ('structures_zm_a', (1453, 4, 4, 0)),
        ('transmission_m_ml', (1, 1, 0, 0)),
        ('transmission_zm_ml', (1, 1, 1, 0)),
        ('topography_m_l', (485, 235, 0, 0)),
        ('topography_zm_l', (485, 235, 235, 0)),
        ('transmission_m_l', (0, 0, 0, 0)),
        ('transmission_zm_l', (0, 0, 0, 0)),
        ('toponymy_m_mp', (0, 0, 0, 0)),
        ('toponymy_zm_mp', (0, 0, 0, 0)),
        ('transmission_m_mp', (0, 0, 0, 0)),
        ('transmission_zm_mp', (0, 0, 0, 0)),
        ('structures_m_p', (0, 0, 0, 0)),
        ('structures_zm_p', (0, 0, 0, 0)),
        ('toponymy_m_p', (0, 0, 0, 0)),
        ('toponymy_zm_p', (0, 0, 0, 0)),
        ('transmission_m_p', (0, 0, 0, 0)),
        ('transmission_zm_p', (0, 0, 0, 0)),
        ('structures_ma', (18, 0, 0, 0)),
        ('structures_p', (0, 0, 0, 0)),
        ('toponymy_mp', (0, 0, 0, 0)),
        ('toponymy_p', (0, 0, 0, 0)),
        ('transmission_ml', (1, 0, 0, 0)),
        ('transmission_mp', (0, 0, 0, 0)),
        ('transmission_p', (0, 0, 0, 0)),
        ('toponymy_z_mp', (0, 0, 0, 0)),
        ('transmission_z_mp', (0, 0, 0, 0)),
        ('transmission_z_p', (0, 0, 0, 0)),
        ('toponymy_z_p', (0, 0, 0, 0)),
        ('structures_z_p', (0, 0, 0, 0)),
        ('transmission_z_ml', (1, 0, 1, 0)),
        ('structures_z_ma', (18, 0, 18, 0)),
    ])
    def test_check_coordinates(self, ntdb_zm_small, fc_name, counts):
        """
        Test Check Coordinates
        """
        fc = ntdb_zm_small[fc_name]
        options = (
            GeometryCheck.REPEATED_XY | GeometryCheck.REPEATED_M |
            GeometryCheck.MISMATCH_Z | GeometryCheck.MISMATCH_M
        )
        records = check_feature_class_geometry(fc, options=options)
        assert len(records) == sum(counts)
        checks = (GeometryCheck.REPEATED_XY, GeometryCheck.REPEATED_M,
                  GeometryCheck.MISMATCH_Z, GeometryCheck.MISMATCH_M)
        names = [check.name for check in checks]
        counter = defaultdict(int)
        for _, name in records:
            counter[name] += 1
        assert tuple(counter[n] for n in names) == counts
    # End test_check_coordinates method
# End TestCheckFeatureClassGeometry class


if __name__ == '__main__':  # pragma: no cover
    pass
