# -*- coding: utf-8 -*-
"""
Tests for the Projections Query Classes
"""


from fudgeo import SpatialReferenceSystem
from pyproj import CRS
from pytest import mark

from spyops.crs.util import srs_from_crs
from spyops.query.management.projections import QueryDefineProjection


pytestmark = [mark.projections, mark.query, mark.management]


class TestDefineProjection:
    """
    Test Define Projection
    """
    @mark.parametrize('spatial_reference', [
        CRS(4326),
        srs_from_crs(CRS(4326))
    ])
    def test_spatial_reference(self, spatial_reference):
        """
        Test Spatial Reference
        """
        query = QueryDefineProjection(None, None, spatial_reference)
        assert isinstance(query.spatial_reference_system, SpatialReferenceSystem)
        assert query.spatial_reference_system.srs_id == 4326
    # End test_spatial_reference method

    def test_source_transform(self):
        """
        Test Source transform
        """
        query = QueryDefineProjection(None, None, None)
        assert query.source_transformer is None
    # End test_source_transform method
# End TestDefineProjection class


if __name__ == '__main__':  # pragma: no cover
    pass
