# -*- coding: utf-8 -*-
"""
Validation tests for CRS
"""


from pytest import raises, mark
from fudgeo import SpatialReferenceSystem
from pyproj import CRS

from spyops.shared.exception import OperationsError
from spyops.validation import validate_supported_crs


pytestmark = [mark.validation]


def test_validate_crs_same(mem_gpkg):
    """
    Test validate crs -- same
    """
    @validate_supported_crs('a', 'b', same=True)
    def crs_function(a, b):
        pass
    srs_a = mem_gpkg.spatial_references[4326]
    srs_b = SpatialReferenceSystem(name='NAD27', organization='EPSG', org_coord_sys_id=4267, definition=CRS(4267).to_wkt())
    fc_a = mem_gpkg.create_feature_class('aaa', srs=srs_a)
    fc_b = mem_gpkg.create_feature_class('bbb', srs=srs_b)
    with raises(OperationsError):
        crs_function(fc_a, fc_b)
# End test_validate_crs_same function


def test_validate_crs_invalid(mem_gpkg):
    """
    Test validate crs -- invalid Spatial Reference System
    """
    @validate_supported_crs('a', 'b')
    def crs_function(a, b):
        pass
    srs_a = mem_gpkg.spatial_references[4326]
    srs_b = SpatialReferenceSystem(name='Unk', organization='ABCD', org_coord_sys_id=-1, definition='Undefined')
    fc_a = mem_gpkg.create_feature_class('aaa', srs=srs_a)
    fc_b = mem_gpkg.create_feature_class('bbb', srs=srs_b)
    with raises(OperationsError):
        crs_function(fc_a, fc_b)
# End test_validate_crs_invalid function


if __name__ == '__main__':  # pragma: no cover
    pass
