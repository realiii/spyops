# -*- coding: utf-8 -*-
"""
Test for Features Query classes
"""


from fudgeo import FeatureClass
from pytest import mark

from spyops.query.management.features import QueryMultiPartToSinglePart


pytestmark = [mark.features, mark.query]


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
# End TestQueryMultiPartToSinglePart class


if __name__ == '__main__':  # pragma: no cover
    pass
