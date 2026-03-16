# -*- coding: utf-8 -*-
"""
Test Coordinate Reference System
"""


from fudgeo import SpatialReferenceSystem
from numpy import array
from pyproj import CRS, Transformer
from pyproj.crs import ProjectedCRS
from pytest import approx, mark, raises

from tests.constants import (
    CUSTOM_THIRD_PARTY_AUTHORITY,
    NAD_1927_StatePlane_Texas_North_Central_FIPS_4202, NAD_1927_UTM_Zone_15N,
    NAD_1983_StatePlane_Texas_North_Central_FIPS_4202, NAD_1983_UTM_Zone_15N)
from spyops.crs.util import (
    equals, check_same_crs, from_authority, get_equidistant_from_feature_class,
    get_geographic_centroid, srs_from_crs, get_crs_from_source,
    _has_same_org_name, _overlaps_builtin, _get_srs_id, validate_srs,
    get_equidistant_projections)
from spyops.shared.exception import OperationsError


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
    fc = world_features[name]
    if crs_only:
        srs = fc.spatial_reference_system
        crs = CRS.from_authority(srs.organization, srs.srs_id)
    else:
        crs = get_crs_from_source(fc)
    assert isinstance(crs, CRS)
    assert crs.name == expected
# End test_get_crs_from_source function


@mark.parametrize('auth, code, expected', [
    ('EPSG', 4326, True),
    ('ABCD', 1234, False),
])
def test_from_authority(auth, code, expected):
    """
    Test from_authority
    """
    result = from_authority(auth, code)
    assert bool(result) == expected
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
    check_same_crs(CRS(4326), CRS(4326))
    with raises(OperationsError):
        check_same_crs(CRS(4326), CRS(8780))
# End test_check_same_crs function


@mark.parametrize('expected, record', [
    (True, ('NAD83 / UTM zone 15N', 26915, 'EPSG', 26915, NAD_1983_UTM_Zone_15N, '')),
    (True, ('NAD_1927_StatePlane_Texas_North_Central_FIPS_4202', 32038, 'EPSG', 32038, NAD_1927_StatePlane_Texas_North_Central_FIPS_4202, 'NAD 1927 SPCS Zone Texas North Cent.')),
    (True, ('NAD_1983_StatePlane_Texas_North_Central_FIPS_4202', 32138, 'EPSG', 32138, NAD_1983_StatePlane_Texas_North_Central_FIPS_4202, 'NAD 1983 SPCS Zone Texas North Cent.')),
    (True, ('Batavia / UTM zone 47N', 54051, 'ThirdParty', 54051, CUSTOM_THIRD_PARTY_AUTHORITY, '')),
    (True, ('Batavia / UTM zone 47N', 54051, 'ThirdParty', 54051, CUSTOM_THIRD_PARTY_AUTHORITY, '')),
    (False, ('Batavia / UTM zone 47N', 54051, 'TP', 54051, CUSTOM_THIRD_PARTY_AUTHORITY, '')),
    (False, ('Batavia / UTM zone 47N', 50000, 'TP', 50000, CUSTOM_THIRD_PARTY_AUTHORITY, '')),
    (False, ('Batavia / UTM zone 47N', 50000, 'ThirdParty', 50000, CUSTOM_THIRD_PARTY_AUTHORITY, '')),
])
def test_has_same_org_name(crs_geopackage, record, expected):
    """
    Test _has_same_org_name
    """
    name, srs_id, org_name, org_id, wkt, description = record
    srs = SpatialReferenceSystem(
        name=name, organization=org_name, org_coord_sys_id=org_id,
        definition=wkt, description=description, srs_id=srs_id)
    assert _has_same_org_name(crs_geopackage, srs_id=srs.srs_id,
                              organization=srs.organization) is expected
# End test_has_same_org_name function


@mark.parametrize('srs_id, expected', [
    (4326, True),
    (54041, False),
    (54051, True),
    (300001, False),
    (102579, True)
])
def test_overlaps_builtin(srs_id, expected):
    """
    Test _overlaps_builtin
    """
    assert _overlaps_builtin(srs_id) is expected
# End test_overlaps_builtin function


@mark.parametrize('name, expected', [
    ('test_26915_a', 26915),
    ('test_32038_a', 32038),
    ('test_32138_p', 32138),
    ('test_undefined_p', 300002),
    ('test_custom_a', 300001),
])
def test_get_srs_id(crs_geopackage, name, expected):
    """
    Tests getting srs id from an srs
    """
    fc = crs_geopackage[name]
    srs = fc.spatial_reference_system
    wkt = srs.definition
    result = _get_srs_id(crs_geopackage, wkt)
    assert result == expected
# End test_get_srs_id function


@mark.parametrize('name, expected', [
    ('test_26915_a', ('NAD83 / UTM zone 15N', 26915, 'EPSG', 26915, NAD_1983_UTM_Zone_15N, '')),
    ('test_32038_a', ('NAD_1927_StatePlane_Texas_North_Central_FIPS_4202', 32038, 'EPSG', 32038, NAD_1927_StatePlane_Texas_North_Central_FIPS_4202, 'NAD 1927 SPCS Zone Texas North Cent.')),
    ('test_32138_p', ('NAD_1983_StatePlane_Texas_North_Central_FIPS_4202', 32138, 'EPSG', 32138, NAD_1983_StatePlane_Texas_North_Central_FIPS_4202, 'NAD 1983 SPCS Zone Texas North Cent.')),
    ('test_undefined_p', ('Undefined Geographic SRS', 0, 'NONE', 0, 'Undefined', '')),
    ('test_custom_p', ('Custom', 300001, 'CUSTOM', 0, NAD_1927_UTM_Zone_15N, '')),
    ('test_custom_a', ('Custom', 300001, 'CUSTOM', 0, NAD_1927_UTM_Zone_15N, ''))
])
def test_validate_srs(crs_geopackage, name, expected):
    """
    Test validate_srs where custom already exists in geopackage
    """
    fc = crs_geopackage[name]
    srs = fc.spatial_reference_system
    result = validate_srs(crs_geopackage, srs)
    assert result.as_record() == expected
# End test_validate_srs function


@mark.parametrize('replace_id', [
    54051, 67890
])
def test_validate_srs_custom_in_range(crs_geopackage, replace_id):
    """
    Test validate SRS, custom using a srs id that is within range
    """
    wkt = CUSTOM_THIRD_PARTY_AUTHORITY.replace('54051', str(replace_id))
    srs = srs_from_crs(CRS.from_wkt(wkt))
    srs = validate_srs(crs_geopackage, srs)
    assert srs.organization == 'ThirdParty'
    assert srs.srs_id == replace_id
# End test_validate_srs_custom_in_range function


@mark.parametrize('epsg_code, coords', [
    (4326, [(0, 0), (1, 1), (-1, -1)]),
    (3857, [(-100_000, -100_000), (100_000, 100_000)]),
    (26915, [(600_000, 5_500_000)]),
])
def test_get_equidistant_projections(epsg_code, coords):
    """
    Test get_equidistant_projections returns appropriate projections for various CRS
    """
    crs = CRS(epsg_code)
    coords = array(coords, dtype=float)
    xform = Transformer.from_crs(crs, crs.geodetic_crs, always_xy=True)
    xs, ys = xform.transform(coords[:, 0], coords[:, 1])
    coords[:, 0] = xs
    coords[:, 1] = ys
    result = get_equidistant_projections(crs, coords)
    assert all(isinstance(proj, ProjectedCRS) for proj in result)
    assert len(result) == len(coords)
# End test_get_equidistant_projections function


@mark.parametrize('name', [
    'hydro_6654_a',
    'hydro_a',
    'hydro_lcc_a',
    'hydro_utm11_a',
])
def test_get_equidistant_from_feature_class(ntdb_zm_small, name):
    """
    Test get equidistant projection from feature class
    """
    source = ntdb_zm_small[name]
    result = get_equidistant_from_feature_class(source)
    assert isinstance(result, ProjectedCRS)
# End test_get_equidistant_from_feature_class function


@mark.parametrize('epsg_code, extent, expected', [
    (4326, (0, 0, 1, 1), (0.5, 0.5)),
    (3857, (-100_000, -100_000, 100_000, 100_000), (0, 0)),
    (26915, (600_000, 5_500_000, 650_000, 5_550_000), (-91.2606, 49.8643)),
])
def test_get_geographic_centroid(epsg_code, extent, expected):
    """
    Test get_geographic_centroid
    """
    crs = CRS(epsg_code)
    pt = get_geographic_centroid(crs, extent)
    assert approx((pt.x, pt.y), abs=0.001) == expected
# End test_get_geographic_centroid function


if __name__ == '__main__':  # pragma: no cover
    pass
