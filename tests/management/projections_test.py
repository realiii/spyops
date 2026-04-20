# -*- coding: utf-8 -*-
"""
Test the project function from spyops.management.projections module.
"""


from fudgeo import FeatureClass
from pyproj import CRS
from pytest import mark

from spyops.crs.transform import get_transform_best_guess
from spyops.crs.util import crs_from_srs
from spyops.environment import (
    Extent, OutputMOption, OutputZOption, Setting,
    core)
from spyops.environment.context import Swap
from spyops.management import project

pytestmark = [mark.management, mark.projections]


class TestProject:
    """
    Test Project
    """
    @mark.parametrize('fc_name, expected', [
        ('hydro_lcc_a', 382),
        ('hydro_lcc_zm_a', 382),
        ('transmission_lcc_l', 66),
        ('transmission_lcc_zm_l', 66),
        ('structures_lcc_p', 3912),
        ('structures_lcc_zm_p', 3912),
    ])
    def test_settings(self, ntdb_zm_small, mem_gpkg, fc_name, expected):
        """
        Test project using settings but really testing that the settings
        are ignored
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        code = 102009
        with (Swap(Setting.EXTENT, Extent.from_bounds(-90, 48, -80, 54, crs=CRS(4326))),
              Swap(Setting.OUTPUT_M_OPTION, OutputMOption.ENABLED),
              Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.ENABLED),
              Swap(Setting.Z_VALUE, 123.456),
              Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS.from_authority('ESRI', code))):
            srs = source.spatial_reference_system
            result = project(source, target, coordinate_system=srs)
            assert result.spatial_reference_system.srs_id != code
            assert result.spatial_reference_system.srs_id == srs.srs_id
            assert result.has_m is source.has_m
            assert result.has_z is source.has_z
            assert len(result) == expected
    # End test_settings function

    @mark.parametrize('fc_name, expected', [
        ('hydro_lcc_a', 382),
        ('hydro_lcc_zm_a', 382),
        ('transmission_lcc_l', 66),
        ('transmission_lcc_zm_l', 66),
        ('structures_lcc_p', 3912),
        ('structures_lcc_zm_p', 3912),
    ])
    def test_project_transform_specified(self, ntdb_zm_small, mem_gpkg, fc_name, expected):
        """
        Test project by specifying the coordinate system and transform
        """
        code = 6654
        crs = CRS(code)
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        transform = get_transform_best_guess(crs_from_srs(source.spatial_reference_system), crs)
        result = project(source, target, coordinate_system=crs, transform=transform)
        assert result.spatial_reference_system.srs_id == code
        assert result.has_m is source.has_m
        assert result.has_z is source.has_z
        assert len(result) == expected
        assert result.extent != source.extent
    # End test_project_transform_specified function

    @mark.parametrize('fc_name, expected', [
        ('hydro_lcc_a', 382),
        ('hydro_lcc_zm_a', 382),
        ('transmission_lcc_l', 66),
        ('transmission_lcc_zm_l', 66),
        ('structures_lcc_p', 3912),
        ('structures_lcc_zm_p', 3912),
    ])
    def test_project_transform_guess(self, ntdb_zm_small, mem_gpkg, fc_name, expected):
        """
        Test project by specifying the coordinate system and transform
        """
        code = 6654
        crs = CRS(code)
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = project(source, target, coordinate_system=crs)
        assert result.spatial_reference_system.srs_id == code
        assert result.has_m is source.has_m
        assert result.has_z is source.has_z
        assert len(result) == expected
        assert result.extent != source.extent
    # End test_project_transform_guess function
# End TestProject class


if __name__ == '__main__':  # pragma: no cover
    pass
