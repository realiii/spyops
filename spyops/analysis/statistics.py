# -*- coding: utf-8 -*-
"""
Statistics
"""


from typing import TYPE_CHECKING

from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany

from spyops.query.analysis.statistics import QueryStatistics
from spyops.shared.hint import ELEMENT, FIELDS, FIELD_NAMES, STATS_FIELDS
from spyops.shared.keywords import GROUP_FIELDS, SOURCE, STATS_FIELDS_ARG
from spyops.validation import (
    validate_field, validate_overwrite_source, validate_result,
    validate_source_element, validate_statistic_field, validate_target_table)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Table


@validate_result()
@validate_source_element()
@validate_target_table()
@validate_statistic_field(STATS_FIELDS_ARG, element_name=SOURCE,
                          is_optional=False)
@validate_field(GROUP_FIELDS, element_name=SOURCE, is_optional=True)
@validate_overwrite_source()
def statistics(source: ELEMENT, target: 'Table', *, stats_fields: STATS_FIELDS,
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
        insert_sql = query.insert
        with (query.source.geopackage.connection as cin,
              query.target.geopackage.connection as cout,
              ExecuteMany(connection=cout, table=query.target) as executor):
            cursor = cin.execute(query.select)
            while rows := cursor.fetchmany(FETCH_SIZE):
                executor(sql=insert_sql, data=rows)
    return query.target
# End statistics function


if __name__ == '__main__':  # pragma: no cover
    pass
