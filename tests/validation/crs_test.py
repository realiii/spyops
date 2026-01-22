# -*- coding: utf-8 -*-
"""
Validation tests for CRS
"""


from pytest import raises, mark
from fudgeo import SpatialReferenceSystem
from pyproj import CRS

from spyops.shared.exception import OperationsError
from spyops.validation import validate_same_crs


pytestmark = [mark.validation]


def test_validate_same_crs(mem_gpkg):
    """
    Test validate same crs
    """
    @validate_same_crs('a', 'b')
    def crs_function(a, b):
        pass
    srs_a = mem_gpkg.spatial_references[4326]
    srs_b = SpatialReferenceSystem(name='NAD27', organization='EPSG', org_coord_sys_id=4267, definition=CRS(4267).to_wkt())
    fc_a = mem_gpkg.create_feature_class('aaa', srs=srs_a)
    fc_b = mem_gpkg.create_feature_class('bbb', srs=srs_b)
    with raises(OperationsError):
        crs_function(fc_a, fc_b)
# End test_validate_same_crs function


if __name__ == '__main__':  # pragma: no cover
    pass
