# -*- coding: utf-8 -*-
"""
Statistics
"""


from fudgeo import FeatureClass, MemoryGeoPackage, Table
from fudgeo.context import ExecuteMany

from spyops.analysis.util import (
    _combine_inputs, _summarize_by_class, _summarize_by_feature)
from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.query.analysis.statistics import (
    QueryFrequency, QueryStatistics, QuerySummarizeWithinFeatureClass,
    QuerySummarizeWithinTable, QueryTabulateIntersection)
from spyops.shared.enumeration import AlgorithmOption, AttributeOption
from spyops.shared.field import GEOM_TYPE_POLYGONS
from spyops.shared.hint import (
    ELEMENT, FIELDS, FIELD_NAMES, OPT_FIELD, OPT_FIELD_STR, STATS_FIELDS,
    XY_TOL)
from spyops.shared.keywords import (
    ALGORITHM_OPTION, AREA_UNIT, CLASS_FIELDS, FIELD, GROUP_FIELDS,
    LENGTH_UNIT, OPERATOR, SOURCE, STATS_FIELDS_ARG, TARGET, TARGET_TABLE)
from spyops.shared.records import bulk_records, insert_many_features
from spyops.shared.stats import Least, Most
from spyops.validation import (
    validate_field, validate_geometry_dimension,
    validate_operator_feature_class, validate_overwrite_input,
    validate_overwrite_source, validate_result, validate_source_element,
    validate_source_feature_class, validate_statistic_field,
    validate_str_enumeration, validate_supported_crs, validate_table,
    validate_target_feature_class, validate_target_table, validate_xy_tolerance)


__all__ = ['statistics', 'frequency', 'tabulate_intersection',
           'summarize_within']


@validate_result()
@validate_source_element()
@validate_target_table()
@validate_statistic_field(STATS_FIELDS_ARG, element_name=SOURCE,
                          is_optional=False)
@validate_field(GROUP_FIELDS, element_name=SOURCE, is_optional=True)
@validate_overwrite_source()
def statistics(source: ELEMENT, target: Table, *,
               stats_fields: STATS_FIELDS,
               group_fields: FIELDS | FIELD_NAMES = (),
               where_clause: str = '') -> Table:
    """
    Statistics

    Calculate summary statistics for selected fields in a table or feature
    class.  Optionally, perform summary statistics on groups of records using
    one or more fields.
    """
    group_fields: FIELDS
    with QueryStatistics(
            source, target=target, statistics=stats_fields,
            fields=group_fields, where_clause=where_clause) as query:
        table = bulk_records(query)
    return table
# End statistics function


@validate_result()
@validate_source_element()
@validate_target_table()
@validate_field(GROUP_FIELDS, element_name=SOURCE)
@validate_statistic_field(STATS_FIELDS_ARG, element_name=SOURCE)
@validate_overwrite_source()
def frequency(source: ELEMENT, target: Table, *,
              group_fields: FIELDS | FIELD_NAMES,
              stats_fields: STATS_FIELDS | None = None,
              where_clause: str = '') -> Table:
    """
    Frequency

    Calculate the frequency of unique field values from a table or
    feature class.  Optionally, add summary statistics.
    """
    group_fields: FIELDS
    stats_fields: STATS_FIELDS
    with QueryFrequency(
            source, target=target, statistics=stats_fields,
            fields=group_fields, where_clause=where_clause) as query:
        table = bulk_records(query)
    return table
# End frequency function


@validate_result()
@validate_source_feature_class()
@validate_operator_feature_class()
@validate_target_table()
@validate_field(GROUP_FIELDS, element_name=SOURCE)
@validate_field(CLASS_FIELDS, element_name=OPERATOR)
@validate_statistic_field(STATS_FIELDS_ARG, element_name=OPERATOR)
@validate_str_enumeration(LENGTH_UNIT, LengthUnit)
@validate_str_enumeration(AREA_UNIT, AreaUnit)
@validate_str_enumeration(ALGORITHM_OPTION, AlgorithmOption)
@validate_xy_tolerance()
@validate_geometry_dimension(OPERATOR, SOURCE)
@validate_supported_crs(SOURCE, OPERATOR)
@validate_overwrite_input(TARGET, SOURCE, OPERATOR)
def tabulate_intersection(source: FeatureClass, operator: FeatureClass,
                          target: Table, *,
                          group_fields: FIELDS | FIELD_NAMES,
                          class_fields: FIELDS | FIELD_NAMES,
                          stats_fields: STATS_FIELDS | None = None,
                          length_unit: LengthUnit = LengthUnit.METERS,
                          area_unit: AreaUnit = AreaUnit.SQUARE_METERS,
                          algorithm_option: AlgorithmOption = (
                                  AlgorithmOption.PAIRWISE),
                          xy_tolerance: XY_TOL = None) -> Table:
    """
    Tabulate Intersection

    Perform an intersection of the source and operator feature classes,
    grouping the source by group fields and the operator by class fields.
    Generate a table of the intersection results that includes geometry
    attributes, counts, and statistics from the operator feature class.
    """
    group_fields: FIELDS
    class_fields: FIELDS
    stats_fields: STATS_FIELDS
    with MemoryGeoPackage.create() as scratch:
        (intermediate, count_field, length_field,
         area_field) = _combine_inputs(
            scratch=scratch, attribute_option=AttributeOption.SANS_FID,
            source=source, operator=operator, target=target,
            algorithm_option=algorithm_option, length_unit=length_unit,
            area_unit=area_unit, xy_tolerance=xy_tolerance)
        with QueryTabulateIntersection(
                source, operator=operator, intermediate=intermediate,
                target=target, group_fields=group_fields,
                class_fields=class_fields, statistics=stats_fields,
                count_field=count_field, length_field=length_field,
                area_field=area_field) as query:
            table = bulk_records(query)
    return table
# End tabulate_intersection function


@validate_result()
@validate_source_feature_class(geometry_types=GEOM_TYPE_POLYGONS)
@validate_operator_feature_class()
@validate_target_feature_class()
@validate_statistic_field(STATS_FIELDS_ARG, element_name=OPERATOR)
@validate_field(FIELD, element_name=OPERATOR, single=True, is_optional=True)
@validate_table(TARGET_TABLE, exists=False, is_output=True, is_optional=True)
@validate_str_enumeration(LENGTH_UNIT, LengthUnit)
@validate_str_enumeration(AREA_UNIT, AreaUnit)
@validate_str_enumeration(ALGORITHM_OPTION, AlgorithmOption)
@validate_xy_tolerance()
@validate_geometry_dimension(OPERATOR, SOURCE)
@validate_supported_crs(SOURCE, OPERATOR)
@validate_overwrite_input(TARGET, SOURCE, OPERATOR)
@validate_overwrite_input(TARGET_TABLE, SOURCE, OPERATOR)
def summarize_within(source: FeatureClass, operator: FeatureClass,
                     target: FeatureClass, *,
                     keep_all: bool = True,
                     stats_fields: STATS_FIELDS | None = None,
                     field: OPT_FIELD_STR = None,
                     target_table: Table | None = None,
                     length_unit: LengthUnit = LengthUnit.METERS,
                     area_unit: AreaUnit = AreaUnit.SQUARE_METERS,
                     algorithm_option: AlgorithmOption = (
                             AlgorithmOption.PAIRWISE),
                     xy_tolerance: XY_TOL = None) \
        -> tuple[FeatureClass, Table | None]:
    """
    Summarize Within

    Overlay a polygon feature class with an operator feature class to generate
    a summary of the feature count (all geometry types), point count (points),
    length (lines and polygons), and area (polygons) within each source polygon.

    Optionally, include attribute field statistics in the output feature class
    based on specified statistics fields.

    Optionally, create a table which summarizes the stats field based on
    source polygons and a field specified from the operator feature class.
    Field statistics, if provided, will be calculated per polygon and field
    value combination.  Feature counts and geometry attributes will also
    be included in the table.
    """
    field: OPT_FIELD
    stats_fields: STATS_FIELDS
    if field is None:
        target_table = None
    if field:
        class_fields = [field]
        least_most = [Least(field), Most(field)]
    else:
        class_fields = []
        least_most = []
    with MemoryGeoPackage.create() as scratch:
        intermediate, *geom_fields = _combine_inputs(
            scratch=scratch, attribute_option=AttributeOption.ALL,
            source=source, operator=operator, target=target,
            algorithm_option=algorithm_option, length_unit=length_unit,
            area_unit=area_unit, xy_tolerance=xy_tolerance)
        summary, group_field = _summarize_by_feature(
            scratch=scratch, source=source, operator=operator,
            intermediate=intermediate, geom_fields=geom_fields,
            least_most=least_most, stats_fields=stats_fields)
        query = QuerySummarizeWithinFeatureClass(
            source, target=target, summary=summary, keep_all=keep_all)
        records = []
        target = query.target
        query_insert = query.insert
        config = query.geometry_config
        transformer = query.source_transformer
        with (target.geopackage.connection as cout,
              ExecuteMany(connection=cout, table=target) as executor):
            for features in query.build_features():
                insert_many_features(
                    config, executor=executor, transformer=transformer,
                    insert_sql=query_insert, features=features, records=records)
        if target_table is None:
            return target, target_table
        summary = _summarize_by_class(
            scratch=scratch, source=source, operator=operator,
            intermediate=intermediate, group_field=group_field,
            class_fields=class_fields, geom_fields=geom_fields,
            stats_fields=stats_fields)
        query = QuerySummarizeWithinTable(summary, target=target_table)
        target_table = bulk_records(query)
    return target, target_table
# End summarize_within function


if __name__ == '__main__':  # pragma: no cover
    pass
