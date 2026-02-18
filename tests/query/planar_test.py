# -*- coding: utf-8 -*-
"""
Test for Planarization
"""

from pyproj import CRS
from pytest import mark

from spyops.crs.util import get_crs_from_source
from spyops.environment import Extent
from spyops.environment.context import Swap
from spyops.environment.enumeration import (
    Setting)
from spyops.query.planar import (
    PlanarizeLineStringOperator, PlanarizeLineStringSource,
    PlanarizePointSource, PlanarizePolygonOperator, PlanarizePolygonSource)


pytestmark = [mark.query, mark.planarization]


class TestPlanarizePolygon:
    """
    Test Planarize Polygon
    """
    def test_source(self, inputs):
        """
        Test Planarize Source
        """
        operator = inputs['intersect_a']
        source = inputs['int_flavor_a']
        ps = PlanarizePolygonSource(source=source, operator=operator,
                                    use_full_extent=False, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'fid_int_flavor_a'
        fc, fid_fld = ps()
        assert fid_fld.name == 'fid'
        assert fc.field_names == ['fid', 'SHAPE', 'fid_int_flavor_a', 'id']
        assert len(fc) == 268
    # End test_source method

    def test_source_zm(self, grid_index, ntdb_zm_meh):
        """
        Test Planarize Source ZM
        """
        operator = grid_index['grid_a']
        source = ntdb_zm_meh['structures_zm_a']
        ps = PlanarizePolygonSource(source=source, operator=operator,
                                    use_full_extent=False, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'fid_structures_zm_a'
        fc, fid_fld = ps()
        assert fid_fld.name == 'fid'
        assert fc.field_names == [
            'fid', 'SHAPE', 'fid_structures_zm_a', 'OBJECTID',
            'ENTITY', 'ENTITY_NAME', 'VALDATE', 'PROVIDER', 'DATANAME',
            'ACCURACY', 'FILE_NAME', 'CODE']
        assert len(fc) == 1550
    # End test_source_zm method

    def test_operator(self, inputs):
        """
        Test Planarize Operator
        """
        operator = inputs['intersect_a']
        source = inputs['int_flavor_a']
        po = PlanarizePolygonOperator(source=source, operator=operator,
                                      use_full_extent=False, xy_tolerance=None)
        assert po.temporary_fid_field.name == 'fid_intersect_a'
        fc, fid_field = po()
        assert fid_field.name == 'fid'
        assert fc.field_names == [
            'fid', 'SHAPE', 'fid_intersect_a', 'ID', 'NAME', 'WHEN',
            'EXAMPLE_JSON', 'BOB', 'NOT_NOW']
        assert len(fc) == 9
    # End test_operator method

    def test_operator_holes(self, inputs):
        """
        Test Planarize Operator using feature class with holes
        """
        operator = inputs['intersect_holes_a']
        source = inputs['int_flavor_a']
        po = PlanarizePolygonOperator(source=source, operator=operator,
                                      use_full_extent=False, xy_tolerance=None)
        assert po.temporary_fid_field.name == 'fid_intersect_holes_a'
        fc, fid_field = po()
        assert fid_field.name == 'fid'
        assert fc.field_names == [
            'fid', 'SHAPE', 'fid_intersect_holes_a', 'ID', 'NAME', 'WHEN',
            'EXAMPLE_JSON', 'BOB', 'NOT_NOW']
        assert len(fc) == 13
    # End test_operator_holes method

    def test_source_multi_part_non_fid(self, inputs, world_features):
        """
        Test Planarize Source Multi Part on a non FID column
        """
        operator = inputs['rivers_portion_l']
        source = world_features['admin_mp_a']
        ps = PlanarizePolygonSource(source=source, operator=operator,
                                    use_full_extent=False, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'OBJECTID_admin_mp_a'
    # End test_source_multi_part_non_fid method

    def test_source_multi_part(self, planar, inputs):
        """
        Test Planarize Source Multi Part
        """
        operator = inputs['int_flavor_a']
        source = planar['hydro_ma']
        assert len(source) == 6
        ps = PlanarizePolygonSource(source=source, operator=operator,
                                    use_full_extent=True, xy_tolerance=None)
        fc, fid_field = ps()
        assert len(fc) == 380
        assert fid_field.name == 'fid'
    # End test_source_multi_part method

    @mark.parametrize('cls', [
        PlanarizePolygonSource,
        PlanarizePolygonOperator
    ])
    @mark.parametrize('use_full_extent', [
        True, False
    ])
    def test_extent(self, cls, inputs, world_features, use_full_extent):
        """
        Test Planarize using Extent
        """
        operator = inputs['rivers_portion_l']
        source = world_features['admin_mp_a']
        ps = cls(
            source=source, operator=operator,
            use_full_extent=use_full_extent, xy_tolerance=None)
        with Swap(Setting.EXTENT, Extent.from_bounds(7, 47, 16, 52, crs=CRS(4326))):
            assert ' 7.0 ' in ps.select
            assert ' 52.0 ' in ps.select
    # End test_extent method
# End TestPlanarizePolygon class


class TestPlanarizeLineString:
    """
    Test Planarize LineString
    """
    def test_source(self, grid_index, planar):
        """
        Test Planarize Source
        """
        operator = grid_index['grid_a']
        source = planar['road_seg_dis_l']
        crs = get_crs_from_source(source)
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.28, 51.125, -114.21, 51.185, crs=crs)):
            ps = PlanarizeLineStringSource(
                source=source, operator=operator,
                use_full_extent=False, xy_tolerance=None)
            assert ps.temporary_fid_field.name == 'fid_road_seg_dis_l'
            fc, fid_fld = ps()
        assert fid_fld.name == 'fid'
        assert fc.field_names == ['fid', 'SHAPE', 'fid_road_seg_dis_l', 'L_STNAME_C', 'L_PLACENAM']
        assert len(fc) == 1474
    # End test_source method

    def test_source_zm(self, grid_index, planar):
        """
        Test Planarize Source ZM
        """
        operator = grid_index['grid_a']
        source = planar['transmission_zm_l']
        assert len(source) == 66
        ps = PlanarizeLineStringSource(
            source=source, operator=operator,
            use_full_extent=False, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'fid_transmission_zm_l'
        fc, fid_fld = ps()
        assert fid_fld.name == 'fid'
        assert fc.field_names == [
            'fid', 'SHAPE', 'fid_transmission_zm_l', 'FEATURE_ID', 'PART_ID',
            'OBJECTID_1', 'ENTITY', 'ENTITY_NAME', 'VALDATE', 'PROVIDER',
            'DATANAME', 'ACCURACY', 'FILE_NAME', 'CODE']
        assert len(fc) == 95
    # End test_source_zm method

    def test_operator(self, grid_index, planar):
        """
        Test Planarize Operator
        """
        source = grid_index['grid_a']
        operator = planar['transmission_zm_l']
        po = PlanarizeLineStringOperator(
            source=source, operator=operator,
            use_full_extent=False, xy_tolerance=None)
        assert po.temporary_fid_field.name == 'fid_transmission_zm_l'
        fc, fid_fld = po()
        assert fid_fld.name == 'fid'
        assert fc.field_names == [
            'fid', 'SHAPE', 'fid_transmission_zm_l', 'FEATURE_ID', 'PART_ID',
            'OBJECTID_1', 'ENTITY', 'ENTITY_NAME', 'VALDATE', 'PROVIDER',
            'DATANAME', 'ACCURACY', 'FILE_NAME', 'CODE']
        assert len(fc) == 95
    # End test_operator method
# End TestPlanarizeLineString class


class TestPlanarizePoint:
    """
    Test Planarize Points
    """
    @mark.parametrize('use_full_extent', [
        True, False
    ])
    def test_extent(self, inputs, world_features, mem_gpkg, use_full_extent):
        """
        Test Planarize Source Multi Part on a non FID column and using extent
        """
        operator = inputs['rivers_portion_l']
        source = world_features['admin_mp_a']
        ps = PlanarizePointSource(
            source=source, operator=operator,
            use_full_extent=use_full_extent, xy_tolerance=None)
        with Swap(Setting.EXTENT, Extent.from_bounds(7, 47, 16, 52, crs=CRS(4326))):
            assert ' 7.0 ' in ps.select
            assert ' 52.0 ' in ps.select
    # End test_extent method

    def test_source_point(self, inputs, mem_gpkg):
        """
        Test Planarize Source Point
        """
        operator = inputs['rivers_portion_l']
        source = inputs['river_p']
        ps = PlanarizePointSource(source=source, operator=operator,
                                  use_full_extent=False, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'fid_river_p'
        fc, fid_fld = ps()
        assert fid_fld.name == 'fid'
        assert fc.field_names == [
            'fid', 'SHAPE', 'fid_river_p', 'NAME', 'SYSTEM', 'vertex_index',
            'vertex_part', 'vertex_part_index', 'distance', 'angle']
        assert len(fc) == 20620
    # End test_source_point method

    def test_source_multi_part(self, inputs, world_features, mem_gpkg):
        """
        Test Planarize Source Multi Part on a non FID column
        """
        operator = inputs['rivers_portion_l']
        source = world_features['admin_mp_a']
        ps = PlanarizePointSource(source=source, operator=operator,
                                  use_full_extent=False, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'OBJECTID_admin_mp_a'
    # End test_source_multi_part method
# End TestPlanarizePoint class


if __name__ == '__main__':  # pragma: no cover
    pass
