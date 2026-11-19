# -*- coding: utf-8 -*-
"""
Test for Statistics Query classes
"""


from fudgeo import FeatureClass, Field, Table
from fudgeo.enumeration import FieldType
from fudgeo.geometry.polygon import Polygon
from pytest import mark

from spyops.analysis import intersect
from spyops.analysis.util import (
    _add_geometry_attribute_fields, _combine_inputs, _summarize_by_feature)
from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.query.analysis.statistics import (
    QueryFrequency, QueryStatistics, QuerySummarizeWithin,
    QueryTabulateIntersection)
from spyops.shared.enumeration import AlgorithmOption, AttributeOption
from spyops.shared.field import validate_fields
from spyops.shared.stats import Count, First, Least, Max, Most, Sum

pytestmark = [mark.statistics, mark.query, mark.analysis]


class TestQueryStatistics:
    """
    Test Query Statistics
    """
    def test_field_names_and_count_sans_group(self, world_features, mem_gpkg):
        """
        Test field names and count no grouping
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='stats_a')
        stats = First(Field('NAME', data_type='TEXT'))
        query = QueryStatistics(
            source, target=target, statistics=[stats], fields=[],
            where_clause='')
        count, insert_names, _ = query._field_names_and_count(source)
        assert count == 1
        assert insert_names == 'FIRST_NAME'
        sql = query.select
        assert 'SELECT spyops_first(NAME)' in sql
        assert 'GROUP BY' not in sql
    # End test_field_names_and_count_sans_group method

    def test_field_names_and_count_with_group(self, world_features, mem_gpkg):
        """
        Test field names and count with grouping
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='stats_a')
        stats = First(Field('LAND_TYPE', data_type='TEXT')), Max(Field('LAND_RANK', data_type='REAL'))
        query = QueryStatistics(
            source, target=target, statistics=stats,
            fields=[Field('COUNTRY', data_type='TEXT')],
            where_clause='')
        count, insert_names, _ = query._field_names_and_count(source)
        assert count == 3
        assert insert_names == 'COUNTRY, FIRST_LAND_TYPE, MAX_LAND_RANK'
        sql = query.select
        assert 'SELECT COUNTRY, spyops_first(LAND_TYPE), MAX(LAND_RANK)' in sql
        assert 'GROUP BY COUNTRY' in sql
    # End test_field_names_and_count_with_group method
# End TestQueryStatistics class


class TestQueryFrequency:
    """
    Test Query Frequency
    """
    def test_field_names_and_count_sans_stats(self, world_features, mem_gpkg):
        """
        Test field names and count no statistics
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='stats_a')
        field = Field('NAME', data_type='TEXT')
        query = QueryFrequency(
            source, target=target, statistics=[], fields=[field],
            where_clause='')
        count, insert_names, select_names = query._field_names_and_count(source)
        assert count == 2
        assert select_names == 'NAME, COUNT(ROWID)'
        assert insert_names == 'NAME, FREQUENCY'
        sql = query.select
        assert 'SELECT NAME, COUNT(ROWID)' in sql
        assert 'GROUP BY' in sql
    # End test_field_names_and_count_sans_group method

    def test_field_names_and_count_with_stats(self, world_features, mem_gpkg):
        """
        Test field names and count with statistics
        """
        source = world_features['admin_a']
        target = Table(geopackage=mem_gpkg, name='stats_a')
        fields = Field('COUNTRY', data_type='TEXT'), Field('LAND_TYPE', data_type='TEXT'), Field('LAND_RANK', data_type='REAL')
        stats = First(Field('LAND_TYPE', data_type='TEXT')), Max(Field('LAND_RANK', data_type='REAL'))
        query = QueryFrequency(
            source, target=target, statistics=stats, fields=fields, where_clause='')
        count, insert_names, select_names = query._field_names_and_count(source)
        assert count == 6
        assert insert_names == 'COUNTRY, LAND_TYPE, LAND_RANK, FREQUENCY, FIRST_LAND_TYPE, MAX_LAND_RANK'
        assert select_names == 'COUNTRY, LAND_TYPE, LAND_RANK, COUNT(ROWID), spyops_first(LAND_TYPE), MAX(LAND_RANK)'
        sql = query.select
        assert 'SELECT COUNTRY, LAND_TYPE, LAND_RANK, COUNT(ROWID)' in sql
        assert 'GROUP BY COUNTRY' in sql
    # End test_field_names_and_count_with_group method
# End TestQueryFrequency class


class TestQueryTabulateIntersection:
    """
    Test QueryTabulateIntersection
    """
    @mark.parametrize('src_name, op_name, group_names, class_names, expected_target, expected_intermediate', [
        ('grid_a', 'structures_p', [], ['DATANAME'], ['DATANAME'], ['DATANAME']),
        ('grid_a', 'structures_p', ['DATANAME'], ['DATANAME'], ['DATANAME_1', 'DATANAME'], ['DATANAME_1','DATANAME']),
        ('grid_a', 'structures_p', ['DATANAME', 'row_index'], ['DATANAME', 'CODE'], ['DATANAME_1', 'row_index', 'DATANAME', 'CODE'], ['DATANAME_1', 'row_index', 'DATANAME', 'CODE']),
        ('grid_a', 'structures_p', ['DATANAME', 'CODE'], ['DATANAME', 'CODE'], ['DATANAME_1', 'CODE_1', 'DATANAME', 'CODE'], ['DATANAME_1', 'CODE_1', 'DATANAME', 'CODE']),
        ('grid_a', 'structures_p', ['DATANAME', 'CODE'], ['ENTITY'], ['DATANAME', 'CODE', 'ENTITY'], ['DATANAME_1', 'CODE_1', 'ENTITY']),
    ])
    def test_rebuild_fields(self, ntdb_zm_small, grid_index, mem_gpkg, src_name, op_name,
                            group_names, class_names, expected_target, expected_intermediate):
        """
        Test rebuild fields
        """
        source = grid_index[src_name].copy(name=src_name, geopackage=mem_gpkg)
        source.add_fields([Field('CODE', data_type=FieldType.text)])
        operator = ntdb_zm_small[op_name]
        intermediate = FeatureClass(name='intermediate', geopackage=mem_gpkg)
        intermediate = intersect(
            operator, operator=source, target=intermediate,
            attribute_option=AttributeOption.SANS_FID)
        group_fields = validate_fields(source, fields=group_names)
        class_fields = validate_fields(operator, fields=class_names)
        dataname, = validate_fields(operator, fields=['DATANAME'])
        query = QueryTabulateIntersection(
            source, operator=operator, intermediate=intermediate,
            target=None, group_fields=group_fields, class_fields=class_fields,
            statistics=[Count(dataname)],
            count_field=None, length_field=None, area_field=None)
        results = query._rebuild_fields(
            source, operator=operator, intermediate=intermediate,
            group_fields=group_fields, class_fields=class_fields)
        intermediate_fields, target_fields = results
        target_names = [f.name for f in target_fields]
        intermediate_names = [f.name for f in intermediate_fields]
        assert target_names == expected_target
        assert intermediate_names == expected_intermediate
    # End test_rebuild_fields method

    @mark.parametrize('add_fields, src_name, op_name, group_names, class_names, expected_field_names, expected_stat_names', [
        (True, 'grid_a', 'structures_a', ['DATANAME'], ['ENTITY'], ['LENGTH', 'AREA'], ['SUM_LENGTH_1', 'SUM_AREA_1']),
        (True, 'grid_a', 'structures_p', ['DATANAME'], ['ENTITY'], ['POINT_COUNT'], ['SUM_POINT_COUNT_1']),
        (True, 'grid_a', 'structures_a', ['DATANAME', 'AREA'], ['ENTITY'], ['LENGTH', 'AREA_1'], ['SUM_LENGTH_1', 'SUM_AREA_1']),
        (True, 'grid_a', 'structures_p', ['DATANAME', 'POINT_COUNT'], ['ENTITY'], ['POINT_COUNT_1'], ['SUM_POINT_COUNT_1']),
        (False, 'grid_a', 'structures_a', ['DATANAME'], ['ENTITY'], ['LENGTH', 'AREA'], ['SUM_LENGTH', 'SUM_AREA']),
        (False, 'grid_a', 'structures_p', ['DATANAME'], ['ENTITY'], ['POINT_COUNT'], ['SUM_POINT_COUNT']),
    ])
    def test_rebuild_geom_stats(self, ntdb_zm_small, grid_index, mem_gpkg, add_fields,
                                src_name, op_name, group_names, class_names,
                                expected_field_names, expected_stat_names):
        """
        Test rebuild geom stats where the default geometry columns are present
        in source (added in the test)
        """
        source = grid_index[src_name].copy(name=src_name, geopackage=mem_gpkg)
        if add_fields:
            for name in ('POINT_COUNT', 'AREA', 'LENGTH'):
                source.add_fields([Field(name, data_type=FieldType.real)])
        operator = ntdb_zm_small[op_name]
        intermediate = FeatureClass(name='intermediate', geopackage=mem_gpkg)
        intermediate = intersect(
            operator, operator=source, target=intermediate,
            attribute_option=AttributeOption.SANS_FID)
        count_field, length_field, area_field = _add_geometry_attribute_fields(
            intermediate, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        group_fields = validate_fields(source, fields=group_names)
        class_fields = validate_fields(operator, fields=class_names)
        dataname, = validate_fields(operator, fields=['DATANAME'])
        query = QueryTabulateIntersection(
            source, operator=operator, intermediate=intermediate,
            target=None, group_fields=group_fields, class_fields=class_fields,
            statistics=[Count(dataname)], count_field=count_field,
            length_field=length_field, area_field=area_field)
        results = query._rebuild_fields(
            source, operator=operator, intermediate=intermediate,
            group_fields=group_fields, class_fields=class_fields)
        _, target_fields = results
        geom_fields, geom_stats = QueryTabulateIntersection._rebuild_geom_stats(
            target_fields, count_field=count_field, length_field=length_field,
            area_field=area_field)
        geom_names = [field.name for field in geom_fields]
        stat_names = [stat.output_name for stat in geom_stats]
        assert geom_names == expected_field_names
        assert stat_names == expected_stat_names
    # End test_rebuild_geom_stats method

    @mark.parametrize('add_fields, src_name, op_name, group_names, class_names, expected_field_names', [
        (True, 'grid_a', 'structures_a', ['DATANAME'], ['ENTITY'], ['DATANAME', 'ENTITY', 'COUNT_DATANAME', 'LENGTH', 'AREA']),
        (True, 'grid_a', 'structures_p', ['DATANAME'], ['ENTITY'], ['DATANAME', 'ENTITY', 'COUNT_DATANAME', 'POINT_COUNT']),
        (True, 'grid_a', 'structures_a', ['DATANAME', 'AREA'], ['ENTITY'], ['DATANAME', 'AREA', 'ENTITY', 'COUNT_DATANAME', 'LENGTH', 'AREA_1']),
        (True, 'grid_a', 'structures_p', ['DATANAME', 'POINT_COUNT'], ['ENTITY'], ['DATANAME', 'POINT_COUNT', 'ENTITY', 'COUNT_DATANAME', 'POINT_COUNT_1']),
        (False, 'grid_a', 'structures_a', ['DATANAME'], ['ENTITY'], ['DATANAME', 'ENTITY', 'COUNT_DATANAME', 'LENGTH', 'AREA']),
        (False, 'grid_a', 'structures_p', ['DATANAME'], ['ENTITY'], ['DATANAME', 'ENTITY', 'COUNT_DATANAME', 'POINT_COUNT'] ),
    ])
    def test_get_unique_fields(self, ntdb_zm_small, grid_index, mem_gpkg, add_fields,
                               src_name, op_name, group_names, class_names,
                               expected_field_names):
        """
        Test get unique fields
        """
        source = grid_index[src_name].copy(name=src_name, geopackage=mem_gpkg)
        if add_fields:
            for name in ('POINT_COUNT', 'AREA', 'LENGTH'):
                source.add_fields([Field(name, data_type=FieldType.real)])
        operator = ntdb_zm_small[op_name]
        group_fields = validate_fields(source, fields=group_names)
        class_fields = validate_fields(operator, fields=class_names)
        dataname, = validate_fields(operator, fields=['DATANAME'])
        intermediate = FeatureClass(name='intermediate', geopackage=mem_gpkg)
        intermediate = intersect(
            operator, operator=source, target=intermediate,
            attribute_option=AttributeOption.SANS_FID)
        count_field, length_field, area_field = _add_geometry_attribute_fields(
            intermediate, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        query = QueryTabulateIntersection(
            source, operator=operator, intermediate=intermediate,
            target=None, group_fields=group_fields, class_fields=class_fields,
            statistics=[Count(dataname)],
            count_field=count_field, length_field=length_field,
            area_field=area_field)
        names = [field.name for field in query._get_unique_fields()]
        assert names == expected_field_names
    # End test_get_unique_fields method

    @mark.parametrize('add_fields, src_name, op_name, group_names, class_names, expected_count, expected_insert, expected_select', [
        (True, 'grid_a', 'structures_a', ['DATANAME'], ['ENTITY'], 5, 'DATANAME, ENTITY, COUNT_DATANAME, LENGTH, AREA', 'DATANAME_1, ENTITY, COUNT(DATANAME), SUM(LENGTH_1), SUM(AREA_1)'),
        (True, 'grid_a', 'structures_p', ['DATANAME'], ['ENTITY'], 4, 'DATANAME, ENTITY, COUNT_DATANAME, POINT_COUNT', 'DATANAME_1, ENTITY, COUNT(DATANAME), SUM(POINT_COUNT_1)'),
        (True, 'grid_a', 'structures_a', ['DATANAME', 'AREA'], ['ENTITY'], 6, 'DATANAME, AREA, ENTITY, COUNT_DATANAME, LENGTH, AREA_1', 'DATANAME_1, AREA, ENTITY, COUNT(DATANAME), SUM(LENGTH_1), SUM(AREA_1)'),
        (True, 'grid_a', 'structures_p', ['DATANAME', 'POINT_COUNT'], ['ENTITY'], 5, 'DATANAME, POINT_COUNT, ENTITY, COUNT_DATANAME, POINT_COUNT_1', 'DATANAME_1, POINT_COUNT, ENTITY, COUNT(DATANAME), SUM(POINT_COUNT_1)'),
        (False, 'grid_a', 'structures_a', ['DATANAME'], ['ENTITY'], 5, 'DATANAME, ENTITY, COUNT_DATANAME, LENGTH, AREA', 'DATANAME_1, ENTITY, COUNT(DATANAME), SUM(LENGTH), SUM(AREA)'),
        (False, 'grid_a', 'structures_p', ['DATANAME'], ['ENTITY'], 4, 'DATANAME, ENTITY, COUNT_DATANAME, POINT_COUNT', 'DATANAME_1, ENTITY, COUNT(DATANAME), SUM(POINT_COUNT)'),
    ])
    def test_field_names_and_count(self, ntdb_zm_small, grid_index, mem_gpkg, add_fields,
                                   src_name, op_name, group_names, class_names,
                                   expected_count, expected_insert, expected_select):
        """
        Test field names and count
        """
        source = grid_index[src_name].copy(name=src_name, geopackage=mem_gpkg)
        if add_fields:
            for name in ('POINT_COUNT', 'AREA', 'LENGTH'):
                source.add_fields([Field(name, data_type=FieldType.real)])
        operator = ntdb_zm_small[op_name]
        group_fields = validate_fields(source, fields=group_names)
        class_fields = validate_fields(operator, fields=class_names)
        dataname, = validate_fields(operator, fields=['DATANAME'])
        intermediate = FeatureClass(name='intermediate', geopackage=mem_gpkg)
        intermediate = intersect(
            operator, operator=source, target=intermediate,
            attribute_option=AttributeOption.SANS_FID)
        count_field, length_field, area_field = _add_geometry_attribute_fields(
            intermediate, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        query = QueryTabulateIntersection(
            source, operator=operator, intermediate=intermediate,
            target=None, group_fields=group_fields, class_fields=class_fields,
            statistics=[Count(dataname)],
            count_field=count_field, length_field=length_field,
            area_field=area_field)
        count, insert, select = query._field_names_and_count(source)
        assert insert == expected_insert
        assert select == expected_select
        assert count == expected_count
    # End test_field_names_and_count method
# End TestQueryTabulateIntersection class


class TestQuerySummarizeWithin:
    """
    Test Query Summarize Within -- Feature Class output
    """
    @mark.parametrize('src_name, op_name, stats_field_names, count, expected', [
        ('grid_a', 'hydro_a', ['CODE', 'ACCURACY'], 8,
         ['fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
          'MOST_COMMON_CODE', 'SUM_CODE', 'SUM_ACCURACY', 'LENGTH', 'AREA']),
        ('grid_a', 'hydro_a', [], 8,
         ['fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
          'MOST_COMMON_CODE', 'LENGTH', 'AREA']),
        ('grid_a', 'structures_p', ['CODE', 'ACCURACY'], 8,
         ['fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
          'MOST_COMMON_CODE', 'SUM_CODE', 'SUM_ACCURACY', 'POINT_COUNT']),
        ('grid_a', 'structures_p', [], 8,
         ['fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
          'MOST_COMMON_CODE', 'POINT_COUNT']),
        ('grid_a', 'transmission_l', ['CODE', 'ACCURACY'], 8,
         ['fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
          'MOST_COMMON_CODE', 'SUM_CODE', 'SUM_ACCURACY', 'LENGTH']),
        ('grid_a', 'transmission_l', [], 8,
         ['fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
          'MOST_COMMON_CODE', 'LENGTH']),
    ])
    @mark.parametrize('keep_all', [
        True,
        False
    ])
    def test_with_class_field(self, grid_index, ntdb_zm_small, mem_gpkg,
                              src_name, op_name, stats_field_names, count,
                              expected, keep_all):
        """
        Test with class field
        """
        source = grid_index[src_name]
        operator = ntdb_zm_small[op_name]
        class_field, = validate_fields(operator, fields=['CODE'])
        stats_fields = [Sum(f) for f in validate_fields(operator, fields=stats_field_names)]
        least_most = Least(class_field), Most(class_field)
        target = FeatureClass(name='summary', geopackage=mem_gpkg)
        intermediate, *geom_fields = _combine_inputs(
            scratch=mem_gpkg, attribute_option=AttributeOption.ALL,
            source=source, operator=operator, target=target,
            algorithm_option=AlgorithmOption.PAIRWISE,
            length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS, xy_tolerance=None)
        summary, _ = _summarize_by_feature(
            scratch=mem_gpkg, source=source, operator=operator,
            intermediate=intermediate, geom_fields=geom_fields,
            least_most=least_most, stats_fields=stats_fields)
        assert len(summary) == count
        assert summary.field_names == expected
        target = FeatureClass(name='target', geopackage=mem_gpkg)
        query = QuerySummarizeWithin(
            source, target=target, summary=summary, keep_all=keep_all)
        features = next(query.build_features())
        assert len(features) == count
        (geom, *attrs), *_ = features
        assert isinstance(geom, Polygon)
        assert len(attrs) == len(expected) - 1
        fields = query._get_unique_fields()
        assert len(fields) == len(expected) - 1
    # End test_with_class_field method

    def test_least_most_overlap(self, grid_index, ntdb_zm_small, mem_gpkg):
        """
        Test least most overlap with class field least most
        """
        source = grid_index['grid_a']
        operator = ntdb_zm_small['hydro_a']
        class_field, = validate_fields(operator, fields=['CODE'])
        stats_fields = least_most = Least(class_field), Most(class_field)
        target = FeatureClass(name='summary', geopackage=mem_gpkg)
        intermediate, *geom_fields = _combine_inputs(
            scratch=mem_gpkg, attribute_option=AttributeOption.ALL,
            source=source, operator=operator, target=target,
            algorithm_option=AlgorithmOption.PAIRWISE,
            length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS, xy_tolerance=None)
        summary, _ = _summarize_by_feature(
            scratch=mem_gpkg, source=source, operator=operator,
            intermediate=intermediate, geom_fields=geom_fields,
            least_most=least_most, stats_fields=stats_fields)
        assert len(summary) == 8
        expected = [
            'fid', 'fid_grid_a', 'COUNT_fid_grid_a', 'LEAST_COMMON_CODE',
            'MOST_COMMON_CODE', 'LENGTH', 'AREA']
        assert summary.field_names == expected
        target = FeatureClass(name='target', geopackage=mem_gpkg)
        query = QuerySummarizeWithin(
            source, target=target, summary=summary, keep_all=True)
        features = next(query.build_features())
        assert len(features) == len(source)
        (geom, *attrs), *_ = features
        assert isinstance(geom, Polygon)
        assert len(attrs) == len(expected) - 1
        fields = query._get_unique_fields()
        assert len(fields) == len(expected) - 1
        assert 'INTO target(SHAPE, ORIG_FID, FEAT_COUNT, LEAST_COMMON_CODE, MOST_COMMON_CODE, LENGTH, AREA)' in query.insert
    # End test_with_class_field method
# End TestQuerySummarizeWithin class


if __name__ == '__main__':  # pragma: no cover
    pass
