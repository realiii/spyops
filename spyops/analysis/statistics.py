# -*- coding: utf-8 -*-
"""
Statistics
"""


from typing import TYPE_CHECKING

from spyops.query.analysis.statistics import QueryFrequency, QueryStatistics
from spyops.shared.hint import ELEMENT, FIELDS, FIELD_NAMES, STATS_FIELDS
from spyops.shared.keywords import GROUP_FIELDS, SOURCE, STATS_FIELDS_ARG
from spyops.shared.records import bulk_records
from spyops.validation import (
    validate_field, validate_overwrite_source, validate_result,
    validate_source_element, validate_statistic_field, validate_target_table)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Table


__all__ = ['statistics', 'frequency']


@validate_result()
@validate_source_element()
@validate_target_table()
@validate_statistic_field(STATS_FIELDS_ARG, element_name=SOURCE,
                          is_optional=False)
@validate_field(GROUP_FIELDS, element_name=SOURCE, is_optional=True)
@validate_overwrite_source()
def statistics(source: ELEMENT, target: 'Table', *,
               stats_fields: STATS_FIELDS,
               group_fields: FIELDS | FIELD_NAMES = (),
               where_clause: str = '') -> 'Table':
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
def frequency(source: ELEMENT, target: 'Table', *,
              group_fields: FIELDS | FIELD_NAMES,
              stats_fields: STATS_FIELDS | None = None,
              where_clause: str = '') -> 'Table':
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


if __name__ == '__main__':  # pragma: no cover
    pass
