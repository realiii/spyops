# -*- coding: utf-8 -*-
"""
Tests for Feature Class Capabilities
"""


from fudgeo.enumeration import GeometryType
from pyproj import CRS
from pytest import mark

from geomio.crs.util import from_crs, validate_srs
from geomio.shared.constant import CUSTOM_UPPER
from geomio.shared.feature import create_feature_class
from tests.constants import (
    CUSTOM_THIRD_PARTY_AUTHORITY, CUSTOM_THIRD_PARTY_AUTHORITY_60000,
    NAD_1927_StatePlane_Texas_North_Central_FIPS_4202, NAD_1927_UTM_Zone_15N,
    NAD_1983_StatePlane_Texas_North_Central_FIPS_4202, NAD_1983_UTM_Zone_15N)

pytestmark = [mark.crs, mark.feature]


@mark.parametrize('srs_id_input, org_input, org_id_input, wkt', [
    (26915, 'EPSG', 26915, NAD_1983_UTM_Zone_15N),
    (32038, 'EPSG', 32038, NAD_1927_StatePlane_Texas_North_Central_FIPS_4202),
    (32138, 'EPSG', 32138, NAD_1983_StatePlane_Texas_North_Central_FIPS_4202),
    (300001, 'Custom', 0, NAD_1927_UTM_Zone_15N),
    (300001, 'Custom', 0, NAD_1927_UTM_Zone_15N),
    (54051, 'ThirdParty', 54051, CUSTOM_THIRD_PARTY_AUTHORITY),
    (60000, 'ThirdParty', 60000, CUSTOM_THIRD_PARTY_AUTHORITY_60000),
])
def test_from_crs_fresh(mem_gpkg, srs_id_input, org_input, org_id_input, wkt):
    """
    Test from_crs where custom does not exist in geopackage
    """
    srs = from_crs(CRS.from_wkt(wkt))
    if org_id_input:
        assert srs.srs_id == srs_id_input
        assert srs.organization == org_input
        assert srs.org_coord_sys_id == org_id_input
    else:
        srs = validate_srs(mem_gpkg, srs)
        _, srs_id, org, org_id, _, _ = srs.as_record()
        assert srs_id == srs_id_input
        assert org.upper() == org_input.upper()
        assert org_id == org_id_input
    fc = create_feature_class(mem_gpkg, name='asdf', srs=srs,
                              shape_type=GeometryType.point)
    key = 'AUTHORITY'
    if key in wkt:
        srs = fc.spatial_reference_system
        if wkt == CUSTOM_THIRD_PARTY_AUTHORITY:
            assert srs.srs_id == 300001
            assert srs.organization == CUSTOM_UPPER
        else:
            assert srs.srs_id == 60000
            assert srs.organization == org_input
        assert key in srs.definition
        assert org_input in srs.definition
# End test_from_crs_fresh function


if __name__ == '__main__':  # pragma: no cover
    pass
