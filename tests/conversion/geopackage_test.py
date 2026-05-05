# -*- coding: utf-8 -*-
"""
Tests for Geopackage Conversion
"""


from pytest import mark

from spyops.conversion import table_to_geopackage
from spyops.environment import Setting
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


if __name__ == '__main__':  # pragma: no cover
    pass
