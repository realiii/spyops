# -*- coding: utf-8 -*-
"""
Tests for Geopackage Conversion
"""


from pyproj import CRS
from pytest import mark, approx

from spyops.conversion import feature_class_to_geopackage, table_to_geopackage
from spyops.environment import OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap

pytestmark = [mark.conversion, mark.geopackage]


class TestTableToGeoPackage:
    """
    Test Table to GeoPackage
    """
    def test_single(self, ntdb_zm_small, mem_gpkg):
        """
        Test single element
        """
        source = ntdb_zm_small['hydro_a']
        results = table_to_geopackage(source, mem_gpkg)
        assert len(results) == 1
    # End test_single method

    def test_with_overwrite(self, ntdb_zm_small, mem_gpkg):
        """
        Test with overwrite
        """
        source = ntdb_zm_small['hydro_a'], ntdb_zm_small['hydro_zm_a']
        with Swap(Setting.OVERWRITE, True):
            for _ in range(2):
                table_to_geopackage(source, mem_gpkg)
        assert len(mem_gpkg.feature_classes) == 2
    # End test_with_overwrite method

    def test_sans_overwrite(self, ntdb_zm_small, mem_gpkg):
        """
        Test without overwrite
        """
        source = ntdb_zm_small['hydro_a'], ntdb_zm_small['hydro_zm_a']
        with Swap(Setting.OVERWRITE, False):
            for _ in range(2):
                table_to_geopackage(source, mem_gpkg)
        assert len(mem_gpkg.feature_classes) == 4
    # End test_sans_overwrite method
# End TestTableToGeoPackage class


class TestFeatureClassToGeoPackage:
    """
    Test Feature Class to GeoPackage
    """
    def test_single(self, ntdb_zm_small, mem_gpkg):
        """
        Test single element
        """
        source = ntdb_zm_small['hydro_a']
        results = feature_class_to_geopackage(source, mem_gpkg)
        assert len(results) == 1
    # End test_single method

    def test_with_overwrite(self, ntdb_zm_small, mem_gpkg):
        """
        Test with overwrite
        """
        source = ntdb_zm_small['hydro_a'], ntdb_zm_small['hydro_zm_a']
        with Swap(Setting.OVERWRITE, True):
            for _ in range(2):
                feature_class_to_geopackage(source, mem_gpkg)
        assert len(mem_gpkg.feature_classes) == 2
    # End test_with_overwrite method

    def test_sans_overwrite(self, ntdb_zm_small, mem_gpkg):
        """
        Test without overwrite
        """
        source = ntdb_zm_small['hydro_a'], ntdb_zm_small['hydro_zm_a']
        with Swap(Setting.OVERWRITE, False):
            for _ in range(2):
                feature_class_to_geopackage(source, mem_gpkg)
        assert len(mem_gpkg.feature_classes) == 4
    # End test_sans_overwrite method

    def test_settings(self, ntdb_zm_small, mem_gpkg):
        """
        Test settings
        """
        source = ntdb_zm_small['hydro_a'], ntdb_zm_small['hydro_zm_a']
        code = 6654
        with (Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.ENABLED),
              Swap(Setting.OUTPUT_M_OPTION, OutputMOption.ENABLED),
              Swap(Setting.Z_VALUE, 123.456),
              Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(code))):
            feature_class_to_geopackage(source, mem_gpkg)
        fcs = mem_gpkg.feature_classes.values()
        assert len(fcs) == 2
        assert all(fc.has_z for fc in fcs)
        assert all(fc.has_m for fc in fcs)
        assert all(fc.spatial_reference_system.srs_id == code for fc in fcs)
        fc1, fc2 = fcs
        extent = (674655.0625, 5653054.0, 710481.625, 5681614.0)
        assert approx(fc1.extent, abs=0.1) == extent
        assert approx(fc2.extent, abs=0.1) == extent
    # End test_settings method
# End TestFeatureClassToGeoPackage class


if __name__ == '__main__':  # pragma: no cover
    pass
