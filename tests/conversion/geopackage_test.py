# -*- coding: utf-8 -*-
"""
Tests for Geopackage Conversion
"""
from fudgeo import FeatureClass, Table
from pyproj import CRS
from pytest import mark, approx

from conftest import world_features
from spyops.conversion import (
    export_features, export_table, feature_class_to_geopackage,
    table_to_geopackage)
from spyops.environment import Extent, OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.shared.sort import Ascending, Descending

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


class TestExportTable:
    """
    Test Export Table
    """
    @mark.parametrize('where_clause, count', [
        ('', 5824),
        ("""ISO_CC = 'AF'""", 34),
    ])
    def test_sans_sort(self, world_tables, mem_gpkg, where_clause, count):
        """
        Test sans sorting
        """
        source = world_tables['admin']
        target = Table(geopackage=mem_gpkg, name=source.name)
        result = export_table(source, target, where_clause=where_clause)
        assert len(result) == count
        names = [n for n, in result.select('NAME', limit=10).fetchall()]
        assert names == ['Badakhshān', 'Bādghīs', 'Baghlān', 'Balkh', 'Bāmyān',
                         'Dāykundī', 'Farāh', 'Fāryāb', 'Ghaznī', 'Ghōr']
    # End test_sans_sort method

    def test_with_sort(self, world_tables, mem_gpkg):
        """
        Test with sorting
        """
        source = world_tables['admin']
        target = Table(geopackage=mem_gpkg, name=source.name)
        result = export_table(
            source, target, sort_fields=[Descending('ISO_CC'), Ascending('ADMINTYPE')])
        assert len(result) == 5824
        names = [n for n, in result.select('NAME', limit=10).fetchall()]
        assert names == [
            'Bulawayo', 'Harare', 'Manicaland', 'Mashonaland Central',
            'Mashonaland East', 'Mashonaland West', 'Masvingo',
            'Matebeleland North', 'Matebeleland South', 'Midlands']
    # End test_with_sort method
# End TestExportTable class


class TestExportFeatures:
    """
    Test Export Features
    """
    @mark.parametrize('where_clause, count, expected', [
        ('', 6893, ['American Samoa', 'American Samoa', 'American Samoa',
                    'American Samoa', 'American Samoa', 'American Samoa',
                    'American Samoa', 'American Samoa', 'American Samoa',
                    'American Samoa']),
        ("""ISO_CC = 'BR'""", 2231,
         ['Acre', 'Alagoas', 'Alagoas', 'Alagoas', 'Alagoas', 'Alagoas',
          'Alagoas', 'Alagoas', 'Alagoas', 'Alagoas']),
    ])
    def test_sans_sort(self, world_features, mem_gpkg, where_clause, count, expected):
        """
        Test sans sorting
        """
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name=source.name)
        with Swap(Setting.EXTENT, Extent.from_bounds(-180, -50, 0, 0, crs=CRS(4326))):
            result = export_features(source, target, where_clause=where_clause)
        assert len(result) == count
        names = [n for n, in result.select('NAME', include_geometry=False, limit=10).fetchall()]
        assert names == expected
    # End test_sans_sort method

    def test_with_sort(self, world_features, mem_gpkg):
        """
        Test with sorting
        """
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name=source.name)
        code = 3395
        with (Swap(Setting.EXTENT, Extent.from_bounds(-180, -50, 0, 0, crs=CRS(4326))),
              Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.ENABLED),
              Swap(Setting.Z_VALUE, 123.456),
              Swap(Setting.OUTPUT_M_OPTION, OutputMOption.ENABLED),
              Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(code))):
            result = export_features(
                source, target, where_clause="ISO_CC = 'BR'",
                sort_fields=[Descending('ISO_CC'), Ascending('ADMINTYPE')])
        assert len(result) == 2231
        names = [n for n, in result.select('NAME', include_geometry=False, limit=10).fetchall()]
        assert names == ['Distrito Federal', 'Acre', 'Alagoas', 'Alagoas',
                         'Alagoas', 'Alagoas', 'Alagoas', 'Alagoas', 'Alagoas',
                         'Alagoas']
        assert result.spatial_reference_system.srs_id == code
        assert result.has_z
        assert result.has_m
    # End test_with_sort method
# End TestExportFeatures class


if __name__ == '__main__':  # pragma: no cover
    pass
