# -*- coding: utf-8 -*-
"""
Tests for Feature Class Capabilities
"""


from fudgeo import FeatureClass
from fudgeo.enumeration import ShapeType
from pyproj import CRS
from pytest import mark

from conftest import world_features
from spyops.crs.util import srs_from_crs, validate_srs
from spyops.environment.context import Swap
from spyops.environment.core import zm_config
from spyops.environment.enumeration import (
    OutputMOption, OutputZOption,
    Setting)
from spyops.geometry.constant import FUDGEO_GEOMETRY_LOOKUP
from spyops.shared.constant import CUSTOM_UPPER
from spyops.shared.element import (
    copy_element, copy_feature_class,
    create_feature_class)
from tests.constants import (
    CUSTOM_THIRD_PARTY_AUTHORITY, CUSTOM_THIRD_PARTY_AUTHORITY_60000,
    NAD_1927_StatePlane_Texas_North_Central_FIPS_4202, NAD_1927_UTM_Zone_15N,
    NAD_1983_StatePlane_Texas_North_Central_FIPS_4202, NAD_1983_UTM_Zone_15N)

pytestmark = [mark.crs, mark.element]


@mark.parametrize('srs_id_input, org_input, org_id_input, wkt', [
    (26915, 'EPSG', 26915, NAD_1983_UTM_Zone_15N),
    (32038, 'EPSG', 32038, NAD_1927_StatePlane_Texas_North_Central_FIPS_4202),
    (32138, 'EPSG', 32138, NAD_1983_StatePlane_Texas_North_Central_FIPS_4202),
    (300001, 'Custom', 0, NAD_1927_UTM_Zone_15N),
    (300001, 'Custom', 0, NAD_1927_UTM_Zone_15N),
    (54051, 'ThirdParty', 54051, CUSTOM_THIRD_PARTY_AUTHORITY),
    (60000, 'ThirdParty', 60000, CUSTOM_THIRD_PARTY_AUTHORITY_60000),
])
def test_srs_from_crs_fresh(mem_gpkg, srs_id_input, org_input, org_id_input, wkt):
    """
    Test srs_from_crs where custom does not exist in geopackage
    """
    srs = srs_from_crs(CRS.from_wkt(wkt))
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
                              shape_type=ShapeType.point)
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
# End test_srs_from_crs_fresh function


@mark.parametrize('name, where_clause, count', [
    ('admin', None, 5824),
    ('admin', '', 5824),
    ('admin', 'ISO_CC = "BR"', 62),
    ('disputed_boundaries', None, 561),
    ('disputed_boundaries', '', 561),
    ('disputed_boundaries', 'Description = "Disputed Boundary"', 364),
    ('cities', None, 2540),
    ('cities', '', 2540),
    ('cities', 'POP IS NULL', 1377),
    ('cities', 'POP < 0', 0),
    ('lakes_a', None, 39),
    ('lakes_a', '', 39),
    ('lakes_a', 'SQKM > 5000', 28),
    ('disputed_boundaries_l', None, 561),
    ('disputed_boundaries_l', '', 561),
    ('disputed_boundaries_l', 'Description = "Disputed Boundary"', 364),
    ('cities_p', None, 2540),
    ('cities_p', '', 2540),
    ('cities_p', 'POP IS NULL', 1377),
    ('cities_p', 'POP < 0', 0),
])
def test_copy_element(world_tables, world_features, mem_gpkg, name, where_clause, count):
    """
    Test copy_element
    """
    source = world_tables[name] or world_features[name]
    target = source.__class__(geopackage=mem_gpkg, name=name)
    result = copy_element(source=source, target=target, where_clause=where_clause)
    assert len(result) == count
# End test_copy_element function


@mark.parametrize('name, where_clause, output_z_option, output_m_option, count', [
    ('lakes_a', None, OutputZOption.SAME, OutputMOption.SAME, 39),
    ('lakes_a', 'SQKM > 5000', OutputZOption.SAME, OutputMOption.SAME, 28),
    ('disputed_boundaries_l', None, OutputZOption.SAME, OutputMOption.SAME, 561),
    ('disputed_boundaries_l', 'Description = "Disputed Boundary"', OutputZOption.SAME, OutputMOption.SAME, 364),
    ('cities_p', None, OutputZOption.SAME, OutputMOption.SAME, 2540),
    ('cities_p', 'POP IS NULL', OutputZOption.SAME, OutputMOption.SAME, 1377),
    ('lakes_a', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 39),
    ('lakes_a', 'SQKM > 5000', OutputZOption.ENABLED, OutputMOption.ENABLED, 28),
    ('disputed_boundaries_l', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 561),
    ('disputed_boundaries_l', 'Description = "Disputed Boundary"', OutputZOption.ENABLED, OutputMOption.ENABLED, 364),
    ('cities_p', None, OutputZOption.ENABLED, OutputMOption.ENABLED, 2540),
    ('cities_p', 'POP IS NULL', OutputZOption.ENABLED, OutputMOption.ENABLED, 1377),
    ('lakes_a', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 39),
    ('lakes_a', 'SQKM > 5000', OutputZOption.DISABLED, OutputMOption.DISABLED, 28),
    ('disputed_boundaries_l', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 561),
    ('disputed_boundaries_l', 'Description = "Disputed Boundary"', OutputZOption.DISABLED, OutputMOption.DISABLED, 364),
    ('cities_p', None, OutputZOption.DISABLED, OutputMOption.DISABLED, 2540),
    ('cities_p', 'POP IS NULL', OutputZOption.DISABLED, OutputMOption.DISABLED, 1377),
])
def test_copy_feature_class_zm(world_features, mem_gpkg, name, where_clause, output_z_option, output_m_option, count):
    """
    Test Copy Feature Class, change up ZM settings
    """
    source = world_features[name]
    target = FeatureClass(geopackage=mem_gpkg, name=name)
    with Swap(Setting.OUTPUT_Z_OPTION, output_z_option), Swap(Setting.OUTPUT_M_OPTION, output_m_option):
        config = zm_config(source)
        target = copy_feature_class(
            source, target=target, where_clause=where_clause, config=config)
    assert len(target) == count
    assert target.has_z == config.z_enabled
    assert target.has_m == config.m_enabled
    cls = FUDGEO_GEOMETRY_LOOKUP[target.shape_type][config.z_enabled, config.m_enabled]
    cursor = target.select()
    assert all(isinstance(g, cls) for g, in cursor.fetchall())
    assert all(not g.is_empty for g, in cursor.fetchall())
# End test_copy_feature_class_zm function


if __name__ == '__main__':  # pragma: no cover
    pass
