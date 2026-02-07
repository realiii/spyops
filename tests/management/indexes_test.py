# -*- coding: utf-8 -*-
"""
Tests for Indexes
"""

from fudgeo.enumeration import ShapeType

from spyops.management import add_spatial_index


def test_add_spatial_index(mem_gpkg):
    """
    Test add spatial index
    """
    srs = mem_gpkg.spatial_references[4326]
    source = mem_gpkg.create_feature_class(
        'test_fc', shape_type=ShapeType.polygon, srs=srs,
        spatial_index=False)
    assert source.has_spatial_index is False
    result = add_spatial_index(source)
    assert result is source
    assert source.has_spatial_index is True
# End test_add_spatial_index function


if __name__ == '__main__':  # pragma: no cover
    pass
