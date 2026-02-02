# -*- coding: utf-8 -*-
"""
Test for Utility Functions
"""


from pyproj import CRS
from pytest import approx, mark

from spyops.crs.transform import get_transform_best_guess
from spyops.crs.unit import get_unit_name
from spyops.crs.util import get_crs_from_source, srs_from_crs
from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.context import Swap
from spyops.environment.enumeration import Setting
from spyops.environment.util import (
    as_title, _scale_factor, get_geographic_transformation, get_grid_size)


pytestmark = [mark.environment]


@mark.parametrize('value, expected', [
    (Setting.XY_TOLERANCE, 'XY Tolerance'),
    (Setting.OVERWRITE, 'Overwrite'),
    (Setting.CURRENT_WORKSPACE, 'Current Workspace'),
    (Setting.OUTPUT_Z_OPTION, 'Output Z Option'),
    (Setting.Z_VALUE, 'Z Value'),
    (Setting.OUTPUT_M_OPTION, 'Output M Option'),
    ('asdf', 'Asdf'),
    (None, ''),
])
def test_as_title(value, expected):
    """
    Test as_title
    """
    assert as_title(value) == expected
# End test_as_title function


@mark.parametrize('fc_name, expected', [
    ('hydro_4617_a', 8.988709950585871e-06),
    ('hydro_6654_a', 8.988710035851e-06),
    ('hydro_lcc_a', 8.988709851109888e-06),
    ('hydro_utm11_a', 8.988709851109888e-06),
    ('toponymy_10tm_p', 8.988674167653699e-06),
])
def test_scale_factor(ntdb_zm_small, fc_name, expected):
    """
    Test _scale_factor
    """
    fc = ntdb_zm_small[fc_name]
    assert approx(_scale_factor(fc), abs=10 ** -9) == expected
# End test_scale_factor function


@mark.parametrize('fc_name, epsg_code, from_name, to_name, expected', [
    ('structures_10tm_a', 4326, 'metre', 'degree', 8.988679418564516e-05),
    ('structures_4617_a', 4326, 'degree', 'degree', 10),
    ('structures_6654_a', 4326, 'metre', 'degree', 8.988711179824804e-05),
    ('structures_lcc_p', 4326, 'metre', 'degree', 8.98871027743553e-05),
    ('structures_utm11_p', 4326, 'metre', 'degree', 8.98870804633134e-05),
    ('structures_10tm_a', 6654, 'metre', 'metre', 10.),
    ('structures_4617_a', 6654, 'degree', 'metre', 1112505.9844928253),
    ('structures_6654_a', 6654, 'metre', 'metre', 10.),
    ('structures_lcc_p', 6654, 'metre', 'metre', 10.),
    ('structures_utm11_p', 6654, 'metre', 'metre', 10.),
    ('structures_10tm_a', 2274, 'metre', 'US survey foot', 32.80833333333335),
    ('structures_4617_a', 2274, 'degree', 'US survey foot', 3649946.71745688),
    ('structures_6654_a', 2274, 'metre', 'US survey foot', 32.80833333333335),
    ('structures_lcc_p', 2274, 'metre', 'US survey foot', 32.80833333333335),
    ('structures_utm11_p', 2274, 'metre', 'US survey foot', 32.80833333333335),
])
def test_get_grid_size(ntdb_zm_small, fc_name, epsg_code, from_name, to_name, expected):
    """
    Test get grid size
    """
    xy_tolerance = 10.
    fc = ntdb_zm_small[fc_name]
    source_crs = get_crs_from_source(fc)
    assert get_unit_name(source_crs) == from_name
    target_crs = CRS(epsg_code)
    assert get_unit_name(target_crs) == to_name
    target_srs = srs_from_crs(target_crs)
    size = get_grid_size(fc, xy_tolerance=xy_tolerance, target_srs=target_srs)
    assert approx(size, abs=10 ** -9) == expected
# End test_get_grid_size function


def test_get_geographic_transformation():
    """
    Test get_geographic_transformation
    """
    source_crs = CRS(4326)
    target_crs = CRS(3857)
    transformer = get_transform_best_guess(source_crs, target_crs)
    assert get_geographic_transformation(source_crs, source_crs, [transformer]) is None
    assert get_geographic_transformation(source_crs, target_crs, []) is None
    assert get_geographic_transformation(
        source_crs, target_crs, ANALYSIS_SETTINGS.geographic_transformations) is None
    with Swap(Setting.GEOGRAPHIC_TRANSFORMATIONS, [transformer]):
        assert get_geographic_transformation(
            source_crs, target_crs, ANALYSIS_SETTINGS.geographic_transformations) is transformer
# End test_get_geographic_transformation function


if __name__ == '__main__':  # pragma: no cover
    pass
