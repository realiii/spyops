# -*- coding: utf-8 -*-
"""
Test for Features Query classes
"""


from fudgeo import FeatureClass
from pyproj import CRS
from pytest import approx, mark

from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.query.management.features import QueryMultiPartToSinglePart


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


if __name__ == '__main__':  # pragma: no cover
    pass
