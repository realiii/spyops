# -*- coding: utf-8 -*-
"""
Tests for Generalization Cartography Classes
"""


from fudgeo import FeatureClass
from pyproj import CRS
from pytest import mark, approx

from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.query.cartography.generalization import QuerySimplifyLine
from spyops.shared.enumeration import SimplifyAlgorithmOption


pytestmark = [mark.cartography, mark.generalization, mark.query]


class TestQuerySimplifyLine:
    """
    Test QuerySimplifyLine
    """
    def test_extent_where_clause(self, ntdb_zm_small):
        """
        Test extent and where clause
        """
        source = ntdb_zm_small['topography_l']
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.5, 50.75, -112.5, 51.25, crs=CRS(4326))):
            where = """PART_ID = 1"""
            query = QuerySimplifyLine(
                source, target=None, where_clause=where,
                algorithm_option=SimplifyAlgorithmOption.POINT_REMOVE,
                xy_tolerance=None)
            sql = query.select
            assert where in sql
            assert 'WHERE minx <= -113.' in sql
    # End test_extent_where_clause method

    @mark.parametrize('crs', [
        CRS(4326),
        CRS(6654),
    ])
    def test_output_coordinate_system(self, ntdb_zm_small, crs):
        """
        Test output coordinate system and tolerance
        """
        source = ntdb_zm_small['topography_l']
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs):
            query = QuerySimplifyLine(
                source, target=None, where_clause='',
                algorithm_option=SimplifyAlgorithmOption.POINT_REMOVE,
                xy_tolerance=None)
            assert query.source_transformer is not None
    # End test_output_coordinate_system method

    def test_insert(self, mem_gpkg, ntdb_zm_small):
        """
        Test insert
        """
        source = ntdb_zm_small['topography_l']
        target = FeatureClass(mem_gpkg, 'output_fc')
        query = QuerySimplifyLine(
            source, target=target, where_clause='',
            algorithm_option=SimplifyAlgorithmOption.POINT_REMOVE,
            xy_tolerance=None)
        sql = query.insert
        assert 'INTO output_fc(SHAPE, FEATURE_ID, PART_ID, ENTITY, ' in sql
    # End test_insert method

    def test_simplifier(self, ntdb_zm_small):
        """
        Test simplifier
        """
        source = ntdb_zm_small['topography_l']
        query = QuerySimplifyLine(
            source, target=None, where_clause='',
            algorithm_option=SimplifyAlgorithmOption.POINT_REMOVE,
            xy_tolerance=None)
        assert query.simplifier is simplify
    # End test_simplifier method
# End TestQuerySimplifyLine class


if __name__ == '__main__':  # pragma: no cover
    pass
