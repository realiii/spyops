# -*- coding: utf-8 -*-
"""
Test Extraction
"""


from fudgeo import FeatureClass, Field, GeoPackage, Table
from fudgeo.enumeration import SQLFieldType
from pytest import mark, raises

from gisworks.analysis.extract import (
    clip, select, split, split_by_attributes, table_select)
from gisworks.shared.enumeration import Setting
from gisworks.shared.exception import OperationsError
from gisworks.shared.setting import Swap
from gisworks.shared.util import element_names, make_unique_name


pytestmark = [mark.extract]


class TestSelect:
    """
    Test Select and Tabl Select
    """
    @mark.parametrize('table_name, where_clause, count', [
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
    ])
    def test_table_select(self, world_tables, mem_gpkg, table_name, where_clause, count):
        """
        Test table_select
        """
        source = world_tables[table_name]
        target = Table(geopackage=mem_gpkg, name=table_name)
        result = table_select(source=source, target=target, where_clause=where_clause)
        assert len(result) == count
    # End test_table_select method

    def test_table_select_overwrite(self, world_tables, mem_gpkg):
        """
        Test table_select that exercises overwrite
        """
        source = world_tables['admin']
        where_clause = 'ISO_CC = "BR"'
        count = 62
        target = Table(geopackage=mem_gpkg, name=source.name)
        result = table_select(source=source, target=target, where_clause=where_clause)
        assert len(result) == count

        with raises(OperationsError):
            table_select(source=source, target=target, where_clause=where_clause)

        with Swap(Setting.OVERWRITE, True):
            result = table_select(source=source, target=target, where_clause=where_clause)
        assert len(result) == count
    # End test_table_select_overwrite method

    @mark.parametrize('table_name, where_clause', [
        ('admin', 'ISO = "BR"'),
        ('disputed_boundaries', 'Description = "Disputed Boundary'),
        ('cities', 'POP ISNULL()'),
        ('cities', 'POP <<>> 0'),
    ])
    def test_table_select_bad_sql(self, world_tables, mem_gpkg, table_name, where_clause):
        """
        Test table_select bad SQL
        """
        source = world_tables[table_name]
        target = Table(geopackage=mem_gpkg, name=table_name)
        with raises(OperationsError):
            table_select(source=source, target=target, where_clause=where_clause)
    # End test_table_select_bad_sql method

    @mark.parametrize('fc_name, where_clause, count', [
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
    def test_select(self, world_features, mem_gpkg, fc_name, where_clause, count):
        """
        Test select
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = select(source=source, target=target, where_clause=where_clause)
        assert len(result) == count
    # End test_select method

    def test_select_sans_attrs(self, inputs, world_features, mem_gpkg):
        """
        Test select sans attributes
        """
        where_clause = 'fid <= 10'
        fc_name = 'intersect_sans_attr_a'
        source = inputs[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = select(source=source, target=target, where_clause=where_clause)
        assert len(result) == 5
        fc_name = 'admin_sans_attr_a'
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = select(source=source, target=target, where_clause=where_clause)
        assert len(result) == 10
    # End test_select_sans_attrs method

    @mark.parametrize('fc_name, where_clause', [
        ('admin_a', 'ISO = "BR"'),
        ('disputed_boundaries_l', 'Description = "Disputed Boundary'),
        ('cities_p', 'POP ISNULL()'),
        ('cities_p', 'POP <<>> 0'),
    ])
    def test_select_bad_sql(self, world_features, mem_gpkg, fc_name, where_clause):
        """
        Test select bad SQL
        """
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with raises(OperationsError):
            select(source=source, target=target, where_clause=where_clause)
    # End test_select_bad_sql method
# End TestSelect class


class TestSplitByAttributes:
    """
    Test Split By Attributes
    """
    @mark.parametrize('fields, count', [
        (Field('ISO_CC', data_type='TEXT'), 3),
        ((Field('ISO_CC', data_type='TEXT'), Field('LAND_TYPE', data_type='TEXT')), 7),
        ('ISO_CC', 3),
        (('ISO_CC', 'LAND_TYPE'), 7),
    ])
    def test_split_by_attributes_features(self, world_features, mem_gpkg, fields, count):
        """
        Test split_by_attributes for feature classes
        """
        subset = 120
        source = world_features['admin_a']
        names = element_names(world_features)
        source = source.copy(
            make_unique_name(source.name, names=names),
            where_clause=f"""fid <= {subset}""", geopackage=mem_gpkg)
        results = split_by_attributes(source, group_fields=fields, geopackage=mem_gpkg)
        assert len(results) == count
        assert sum([len(r) for r in results]) == subset
    # End test_split_by_attributes_features method

    def test_split_by_attributes_features_sans_attributes(self, world_features, mem_gpkg):
        """
        Test split_by_attributes for feature classes sans attributes
        """
        count = 15
        source = world_features['admin_sans_attr_a']
        names = element_names(world_features)
        source = source.copy(
            make_unique_name(source.name, names=names),
            where_clause=f"""fid <= {count}""", geopackage=mem_gpkg)
        results = split_by_attributes(source, group_fields=['fid'], geopackage=mem_gpkg)
        assert len(results) == count
        assert sum([len(r) for r in results]) == count
    # End test_split_by_attributes_features_sans_attributes method

    @mark.parametrize('fields, count', [
        (Field('ISO_CC', data_type='TEXT'), 3),
        ((Field('ISO_CC', data_type='TEXT'), Field('LAND_TYPE', data_type='TEXT')), 7),
        ('ISO_CC', 3),
        (('ISO_CC', 'LAND_TYPE'), 7),
    ])
    def test_split_by_attributes_features_with_settings(self, world_features, mem_gpkg, fields, count):
        """
        Test split_by_attributes for feature classes with analysis settings
        """
        subset = 120
        source = world_features['admin_a']
        names = element_names(world_features)
        source = source.copy(
            make_unique_name(source.name, names=names),
            where_clause=f"""fid <= {subset}""", geopackage=mem_gpkg)
        with Swap(Setting.CURRENT_WORKSPACE, mem_gpkg):
            results = split_by_attributes(source.name, group_fields=fields, geopackage=None)
        assert len(results) == count
        assert sum([len(r) for r in results]) == subset
    # End test_split_by_attributes_features_with_settings method

    @mark.benchmark
    @mark.parametrize('fix_name, name, fields, count', [
        ('inputs', 'utmzone_continentish_a', ('ZONE', 'ROW_'), 708),
        ('inputs', 'utmzone_sparse_a', ('ZONE', 'ROW_'), 228),
        ('world_features', 'admin_a', ('COUNTRY', 'ISO_CC', 'ADMINTYPE'), 376),
    ])
    def test_split_by_attributes_larger_inputs(self, request, inputs, mem_gpkg, fix_name, name, fields, count):
        """
        Test split by attributes using larger inputs
        """
        source = request.getfixturevalue(fix_name)[name]
        results = split_by_attributes(
            source=source, group_fields=fields, geopackage=mem_gpkg)
        assert len(results) == count
    # End test_split_by_attributes_larger_inputs method
# End TestSplitByAttributes class


class TestClip:
    """
    Test Clip
    """
    @mark.parametrize('fc_name, xy_tolerance, count', [
        ('admin_a', None, 89),
        ('airports_p', None, 35),
        ('roads_l', None, 2189),
        ('admin_mp_a', None, 49),
        ('airports_mp_p', None, 4),
        ('roads_mp_l', None, 8),
        ('admin_a', 0.001, 88),
        ('airports_p', 0.001, 35),
        ('roads_l', 0.001, 2319),
        ('admin_mp_a', 0.001, 49),
        ('airports_mp_p', 0.001, 4),
        ('roads_mp_l', 0.001, 8),
        ('admin_a', 1, 17),
        ('airports_p', 1, 32),
        ('roads_l', 1, 300),
        ('admin_mp_a', 1, 17),
        ('airports_mp_p', 1, 4),
        ('roads_mp_l', 1, 8),
    ])
    def test_clip(self, inputs, world_features, mem_gpkg, fc_name, xy_tolerance, count):
        """
        Test clip
        """
        clipper = inputs['clipper_a']
        assert len(clipper) == 3
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        result = clip(source=source, operator=clipper, target=target, xy_tolerance=xy_tolerance)
        assert len(result) < len(source)
        assert len(result) == count
    # End test_clip method

    def test_clip_sans_attributes(self, inputs, world_features, mem_gpkg):
        """
        Test clip sans attributes
        """
        clipper = inputs['intersect_sans_attr_a']
        assert len(clipper) == 5
        source = world_features['admin_sans_attr_a']
        target = FeatureClass(geopackage=mem_gpkg, name='sans')
        result = clip(source=source, operator=clipper, target=target)
        assert len(result) == 107
    # End test_clip_sans_attributes method

    @mark.parametrize('xy_tolerance, count', [
        (None, 195),
        (0.001, 209),
    ])
    def test_clip_line_on_line(self, world_features, inputs, mem_gpkg, xy_tolerance, count):
        """
        Test clipping using a line feature class as the operator on a line feature class
        """
        clipper = inputs['rivers_portion_l']
        source = world_features['rivers_l']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = clip(source=source, operator=clipper, target=target, xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_clip_line_on_line method

    @mark.parametrize('xy_tolerance, count', [
        (None, 7398),
        (0, 7398),
        (0.0000000001, 3),
        (0.1, 0),
    ])
    def test_clip_line_on_point(self, inputs, mem_gpkg, xy_tolerance, count):
        """
        Test clipping using a line feature class as the operator on a point feature class
        """
        clipper = inputs['rivers_portion_l']
        source = inputs['river_p']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = clip(source=source, operator=clipper, target=target, xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_clip_line_on_point method

    @mark.parametrize('xy_tolerance, count', [
        (None, 100),
        (0, 100),
        (0.001, 100),
    ])
    def test_clip_point_on_point(self, inputs, mem_gpkg, xy_tolerance, count):
        """
        Test clipping using a point feature class as the operator on a point feature class
        """
        clipper = inputs['river_p'].copy(name='river_p_clipper', where_clause='fid <= 100', geopackage=mem_gpkg)
        assert len(clipper) == 100
        source = inputs['river_p']
        target = FeatureClass(geopackage=mem_gpkg, name='riv')
        result = clip(source=source, operator=clipper, target=target, xy_tolerance=xy_tolerance)
        assert len(result) == count
    # End test_clip_point_on_point method

    @mark.parametrize('fc_name, xy_tolerance, count', [
        ('admin_a', None, 89),
        ('airports_p', None, 35),
        ('roads_l', None, 2189),
        ('admin_mp_a', None, 49),
        ('airports_mp_p', None, 4),
        ('roads_mp_l', None, 8),
        ('admin_a', 0.001, 88),
        ('airports_p', 0.001, 35),
        ('roads_l', 0.001, 2319),
        ('admin_mp_a', 0.001, 49),
        ('airports_mp_p', 0.001, 4),
        ('roads_mp_l', 0.001, 8),
        ('admin_a', 1, 17),
        ('airports_p', 1, 32),
        ('roads_l', 1, 300),
        ('admin_mp_a', 1, 17),
        ('airports_mp_p', 1, 4),
        ('roads_mp_l', 1, 8),
    ])
    def test_clip_setting(self, inputs, world_features, mem_gpkg, fc_name, xy_tolerance, count):
        """
        Test clip using analysis settings
        """
        clipper = inputs['clipper_a']
        assert len(clipper) == 3
        source = world_features[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        with Swap(Setting.XY_TOLERANCE, xy_tolerance):
            result = clip(source=source, operator=clipper, target=target)
        assert len(result) < len(source)
        assert len(result) == count
    # End test_clip_setting method

    @mark.benchmark
    @mark.parametrize('name, count', [
        ('utmzone_continentish_a', 200_915),
        ('utmzone_sparse_a', 26_602),
    ])
    def test_clip_larger_inputs(self, inputs, world_features, mem_gpkg, name, count):
        """
        Test clip using larger inputs
        """
        operator = inputs[name]
        source = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name=name)
        result = clip(source=source, operator=operator, target=target)
        assert len(result) == count
    # End test_clip_larger_inputs method
# End TestClip class


class TestSplit:
    """
    Test Split
    """
    @mark.parametrize('fc_name, xy_tolerance, element_count, record_count', [
        ('admin_a', None, 4, 114),
        ('airports_p', None, 4, 40),
        ('roads_l', None, 4, 2514),
        ('admin_mp_a', None, 4, 68),
        ('airports_mp_p', None, 4, 8),
        ('roads_mp_l', None, 4, 14),
        ('admin_a', 0.001, 4, 112),
        ('airports_p', 0.001, 4, 40),
        ('roads_l', 0.001, 4, 2679),
        ('admin_mp_a', 0.001, 4, 68),
        ('airports_mp_p', 0.001, 4, 8),
        ('roads_mp_l', 0.001, 4, 14),
        ('admin_a', 1, 4, 22),
        ('airports_p', 1, 4, 35),
        ('roads_l', 1, 4, 344),
        ('admin_mp_a', 1, 4, 22),
        ('airports_mp_p', 1, 4, 8),
        ('roads_mp_l', 1, 4, 13),
    ])
    def test_split(self, inputs, world_features, mem_gpkg, fc_name, xy_tolerance, element_count, record_count):
        """
        Test split
        """
        splitter = inputs['splitter_a']
        assert len(splitter) == 5
        source = world_features[fc_name]
        field = Field('NAME', data_type=SQLFieldType.text)
        results = split(source=source, operator=splitter, field=field, geopackage=mem_gpkg, xy_tolerance=xy_tolerance)
        assert len(results) == element_count
        assert sum(len(r) for r in results) == record_count
    # End test_split method

    @mark.parametrize('fc_name, xy_tolerance, element_count, record_count', [
        ('admin_a', None, 4, 114),
        ('airports_p', None, 4, 40),
        ('roads_l', None, 4, 2514),
        ('admin_mp_a', None, 4, 68),
        ('airports_mp_p', None, 4, 8),
        ('roads_mp_l', None, 4, 14),
        ('admin_a', 0.001, 4, 112),
        ('airports_p', 0.001, 4, 40),
        ('roads_l', 0.001, 4, 2679),
        ('admin_mp_a', 0.001, 4, 68),
        ('airports_mp_p', 0.001, 4, 8),
        ('roads_mp_l', 0.001, 4, 14),
        ('admin_a', 1, 4, 22),
        ('airports_p', 1, 4, 35),
        ('roads_l', 1, 4, 344),
        ('admin_mp_a', 1, 4, 22),
        ('airports_mp_p', 1, 4, 8),
        ('roads_mp_l', 1, 4, 13),
    ])
    def test_split_setting(self, tmp_path, inputs, world_features, mem_gpkg, fc_name, xy_tolerance, element_count, record_count):
        """
        Test split using analysis settings
        """
        splitter = inputs['splitter_a']
        assert len(splitter) == 5
        source = world_features[fc_name]
        field = Field('NAME', data_type=SQLFieldType.text)
        gpkg = GeoPackage.create(tmp_path / 'test_scratch.gpkg')
        with (Swap(Setting.XY_TOLERANCE, xy_tolerance),
              Swap(Setting.CURRENT_WORKSPACE, mem_gpkg),
              Swap(Setting.SCRATCH_WORKSPACE, gpkg)):
            results = split(source=source, operator=splitter, field=field, geopackage=None)
        assert len(results) == element_count
        assert sum(len(r) for r in results) == record_count
    # End test_split_setting method

    @mark.benchmark
    @mark.parametrize('name, count', [
        ('utmzone_continentish_a', 708),
        ('utmzone_sparse_a', 228),
    ])
    def test_split_larger_inputs(self, inputs, world_features, mem_gpkg, name, count):
        """
        Test split using larger inputs
        """
        operator = inputs[name]
        source = world_features['admin_a']
        results = split(source=source, operator=operator, field='NAME', geopackage=mem_gpkg)
        assert len(results) == count
    # End test_split_larger_inputs method
# End TestSplit class


if __name__ == '__main__':  # pragma: no cover
    pass
