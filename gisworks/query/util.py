# -*- coding: utf-8 -*-
"""
Utilities for Query
"""


from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany
from shapely import from_wkb, set_precision

from gisworks.shared.base import QueryConfig
from gisworks.shared.hint import XY_TOL
from gisworks.shared.util import extend_records


def process_disjoint(query: QueryConfig, xy_tolerance: XY_TOL) -> None:
    """
    Process Disjoint Features
    """
    if not query.disjoint:
        return
    records = []
    insert_sql = query.insert
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.disjoint)
        while features := cursor.fetchmany(FETCH_SIZE):
            if xy_tolerance is None:
                executor(sql=insert_sql, data=features)
            else:
                geometries = [from_wkb(g.wkb) for g, *_ in features]
                geometries = set_precision(geometries, grid_size=xy_tolerance)
                results = [(geom, attrs) for geom, (_, *attrs) in
                           zip(geometries, features)]
                extend_records(results, records=records, config=query.config)
                executor(sql=insert_sql, data=records)
                records.clear()
# End process_disjoint function


if __name__ == '__main__':  # pragma: no cover
    pass
