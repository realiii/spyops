# -*- coding: utf-8 -*-
"""
Generalization Data Management
"""


from typing import TYPE_CHECKING

from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany

from spyops.query.management.generalization import QueryDissolve
from spyops.shared.hint import FIELDS, FIELD_NAMES, STATS_FIELDS, XY_TOL
from spyops.shared.keywords import GROUP_FIELDS, SOURCE, STATISTICS
from spyops.shared.records import extend_records
from spyops.validation import (
    validate_field, validate_overwrite_source, validate_result,
    validate_source_feature_class, validate_statistic_field,
    validate_target_feature_class, validate_xy_tolerance)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


@validate_result()
@validate_source_feature_class()
@validate_target_feature_class()
@validate_field(GROUP_FIELDS, element_name=SOURCE, exclude_primary=False)
@validate_statistic_field(STATISTICS, element_name=SOURCE)
@validate_xy_tolerance()
@validate_overwrite_source()
def dissolve(source: 'FeatureClass', target: 'FeatureClass',
             group_fields: FIELDS | FIELD_NAMES, *,
             statistics: STATS_FIELDS | None = None, as_multi_part: bool = True,
             xy_tolerance: XY_TOL = None) -> 'FeatureClass':
    """
    Dissolve

    Aggregate features based on one or more group fields and optionally
    generate statistics for attributes.  The as_multi_part option controls
    whether the output is a single-part or multipart feature class.
    """
    records = []
    with QueryDissolve(source, target=target, fields=group_fields,
                       statistics=statistics, as_multi_part=as_multi_part,
                       xy_tolerance=xy_tolerance) as query:
        insert_sql = query.insert
        config = query.geometry_config
        with (query.source.geopackage.connection as cin,
              query.target.geopackage.connection as cout,
              ExecuteMany(connection=cout, table=query.target) as executor):
            cursor = cin.execute(query.select)
            for geoms in query.dissolved_geometries():
                rows = cursor.fetchmany(FETCH_SIZE)
                results = [(geoms.pop(i, None), attrs) for i, *attrs in rows]
                extend_records(results, records=records, config=config)
                executor(sql=insert_sql, data=records)
                records.clear()
    return query.target
# End dissolve function


if __name__ == '__main__':  # pragma: no cover
    pass
