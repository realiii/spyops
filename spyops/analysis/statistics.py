# -*- coding: utf-8 -*-
"""
Statistics
"""


from fudgeo import FeatureClass, MemoryGeoPackage, Table

from spyops.analysis.util import (
    _combine_inputs, _summarize_by_class, _summarize_by_feature)
from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.environment import OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.query.analysis.statistics import (
    QueryFrequency, QueryStatistics, QueryTabulateIntersection)
from spyops.shared.enumeration import AlgorithmOption, AttributeOption
from spyops.shared.hint import (
    ELEMENT, FIELDS, FIELD_NAMES, STATS_FIELDS, XY_TOL)
from spyops.shared.keywords import (
    ALGORITHM_OPTION, AREA_UNIT, CLASS_FIELDS, GROUP_FIELDS, LENGTH_UNIT,
    OPERATOR, SOURCE, STATS_FIELDS_ARG, TARGET)
from spyops.shared.records import bulk_records
from spyops.validation import (
    validate_field, validate_geometry_dimension,
    validate_operator_feature_class, validate_overwrite_input,
    validate_overwrite_source, validate_result, validate_source_element,
    validate_source_feature_class, validate_statistic_field,
    validate_str_enumeration, validate_supported_crs, validate_table,
    validate_target_feature_class, validate_target_table, validate_xy_tolerance)


__all__ = ['statistics', 'frequency', 'tabulate_intersection']


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


if __name__ == '__main__':  # pragma: no cover
    pass
