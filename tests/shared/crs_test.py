# -*- coding: utf-8 -*-
"""
Test Coordinate Reference System
"""


from fudgeo import FeatureClass
from pyproj import CRS
from pytest import approx, mark, raises

from geomio.shared.crs import (
    check_same_crs, get_crs_from_source, from_authority, equals,
    extent_from_feature_class)
from geomio.shared.exceptions import OperationsError


pytestmark = [mark.crs]


@mark.parametrize('name, crs_only, expected', [
    ('admin_a', False, 'WGS 84'),
    ('airports_p', False, 'WGS 84'),
    ('roads_l', False, 'WGS 84'),
    ('admin_a', True, 'WGS 84'),
    ('airports_p', True, 'WGS 84'),
    ('roads_l', True, 'WGS 84'),
])
def test_get_crs_from_source(world_features, name, crs_only, expected):
    """
    Test getting crs from source
    """
    fc = FeatureClass(geopackage=world_features, name=name)
    if crs_only:
        srs = fc.spatial_reference_system
        crs = CRS.from_authority(srs.organization, srs.srs_id)
    else:
        crs = get_crs_from_source(fc)
    assert isinstance(crs, CRS)
    assert crs.name == expected
# End test_get_crs_from_source function


@mark.parametrize('name, expected', [
    ('admin_a', (-180.0, -90, 180, 83.6654911040001)),
    ('airports_p', (-177.38063597699997, -54.84327804999998, 178.5592279430001, 78.24611103500007)),
    ('roads_l', (-166.52854919433594, -54.97826385498047, 178.56739807128906, 70.48219299316406)),
])
def test_extent_from_feature_class(world_features, name, expected):
    """
    Test extent from feature class
    """
    fc = FeatureClass(geopackage=world_features, name=name)
    extent = extent_from_feature_class(fc)
    assert approx(extent, abs=0.000001) == expected
# End test_extent_from_feature_class function


@mark.parametrize('auth, code, expected', [
    ('EPSG', 4326, True),
    ('ABCD', 1234, False),
])
def test_from_authority(auth, code, expected):
    """
    Test from_authority
    """
    result, _ = from_authority(auth, code)
    assert result == expected
# End test_from_authority function


@mark.parametrize('source_code, target_code, expected', [
    (8780, 8780, True),
    (8780, 2276, True),
    (2276, 2276, True),
    (2276, 8780, True),
    (8780, 4326, False),
    (4326, 8780, False),
])
def test_equals(source_code, target_code, expected):
    """
    Test Equals
    """
    assert equals(CRS(source_code), CRS(target_code)) is expected
# End test_equals function


def test_check_same_crs():
    """
    Check Same CRS
    """
    with raises(OperationsError):
        check_same_crs(CRS(4326), CRS(8780))
# End test_check_same_crs function


if __name__ == '__main__':  # pragma: no cover
    pass
