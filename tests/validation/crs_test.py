# -*- coding: utf-8 -*-
"""
Validation tests for CRS
"""


from pytest import raises, mark
from fudgeo import SpatialReferenceSystem
from pyproj import CRS

from spyops.crs.transform import get_transform_best_guess
from spyops.shared.exception import OperationsError
from spyops.validation import (
    validate_coordinate_system,
    validate_supported_crs, validate_transform)

pytestmark = [mark.validation]


def test_validate_supported_crs_same(mem_gpkg):
    """
    Test validate supported crs -- same
    """
    @validate_supported_crs('a', 'b', same=True)
    def crs_function(a, b):
        pass
    srs_a = mem_gpkg.spatial_references[4326]
    srs_b = SpatialReferenceSystem(
        name='NAD27', organization='EPSG', org_coord_sys_id=4267,
        definition=CRS(4267).to_wkt())
    fc_a = mem_gpkg.create_feature_class('aaa', srs=srs_a)
    fc_b = mem_gpkg.create_feature_class('bbb', srs=srs_b)
    with raises(OperationsError):
        crs_function(fc_a, fc_b)
# End test_validate_supported_crs_same function


def test_validate_supported_crs_invalid(mem_gpkg):
    """
    Test validate supported crs -- invalid Spatial Reference System
    """
    @validate_supported_crs('a', 'b')
    def crs_function(a, b):
        pass
    srs_a = mem_gpkg.spatial_references[4326]
    srs_b = SpatialReferenceSystem(
        name='Unk', organization='ABCD', org_coord_sys_id=-1,
        definition='Undefined')
    fc_a = mem_gpkg.create_feature_class('aaa', srs=srs_a)
    fc_b = mem_gpkg.create_feature_class('bbb', srs=srs_b)
    with raises(OperationsError):
        crs_function(fc_a, fc_b)
# End test_validate_supported_crs_invalid function


def test_validate_coordinate_system(mem_gpkg):
    """
    Test validate coordinate system -- same
    """
    @validate_coordinate_system('coord_sys')
    def crs_function(coord_sys):
        return coord_sys
    srs = SpatialReferenceSystem(
        name='NAD27', organization='EPSG', org_coord_sys_id=4267,
        definition=CRS(4267).to_wkt())
    assert crs_function(srs) is srs
# End test_validate_coordinate_system function


def test_validate_coordinate_system_invalid(mem_gpkg):
    """
    Test validate coordinate system -- invalid Spatial Reference System
    """
    @validate_coordinate_system('coord_sys')
    def crs_function(coord_sys):
        return coord_sys
    srs = SpatialReferenceSystem(
        name='Unk', organization='ABCD', org_coord_sys_id=-1, definition='Undefined')
    with raises(OperationsError):
        crs_function(srs)
# End test_validate_coordinate_system_invalid function


def test_validate_transform(mem_gpkg):
    """
    Test validate transform -- same
    """
    @validate_transform('xform')
    def crs_function(xform):
        return xform
    t = get_transform_best_guess(CRS(4326), CRS(4267))
    assert crs_function(t) is t
    assert crs_function(None) is None
# End test_validate_transform function


def test_validate_transform_invalid(mem_gpkg):
    """
    Test validate transform
    """
    @validate_transform('xform')
    def crs_function(xform):
        return xform
    t = Ellipsis
    with raises(TypeError):
        crs_function(t)
# End test_validate_transform_invalid function


if __name__ == '__main__':  # pragma: no cover
    pass
