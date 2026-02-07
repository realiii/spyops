# -*- coding: utf-8 -*-
"""
Tests for Indexes
"""

from fudgeo.enumeration import ShapeType
from pytest import mark

from spyops.management import add_spatial_index, remove_spatial_index


pytestmark = [mark.management, mark.indexes]


def test_add_spatial_index(mem_gpkg):
    """
    Test add spatial index
    """
    srs = mem_gpkg.spatial_references[4326]
    source = mem_gpkg.create_feature_class(
        'test_fc', shape_type=ShapeType.polygon, srs=srs,
        spatial_index=False)
    assert not source.has_spatial_index
    result = add_spatial_index(source)
    assert result is source
    assert source.has_spatial_index
# End test_add_spatial_index function


def test_remove_spatial_index(mem_gpkg):
    """
    Test add spatial index
    """
    srs = mem_gpkg.spatial_references[4326]
    source = mem_gpkg.create_feature_class(
        'test_fc', shape_type=ShapeType.polygon, srs=srs,
        spatial_index=True)
    assert source.has_spatial_index
    result = remove_spatial_index(source)
    assert result is source
    assert not source.has_spatial_index
# End test_remove_spatial_index function


if __name__ == '__main__':  # pragma: no cover
    pass
