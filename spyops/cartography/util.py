# -*- coding: utf-8 -*-
"""
Utilities for Cartography
"""

from typing import TYPE_CHECKING

from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany

from spyops.geometry.util import filter_features, to_shapely
from spyops.geometry.wa import set_precision
from spyops.shared.records import extend_records

if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from spyops.query.cartography.generalization import BaseQuerySimplify


def _simplify(query: 'BaseQuerySimplify', tolerance: float,
              preserve_topology: bool) -> 'FeatureClass':
    """
    Simplify Line or Polygon Features
    """
    records = []
    insert_sql = query.insert
    grid_size = query.grid_size
    simplifier = query.simplifier
    config = query.geometry_config
    transformer = query.source_transformer
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            features, geometries = to_shapely(features, transformer=transformer)
            if grid_size is not None:
                geometries = set_precision(geometries, grid_size=grid_size)
            geometries = simplifier(
                geometries, tolerance=tolerance,
                preserve_topology=preserve_topology)
            results = [(g, attrs) for g, (_, *attrs) in
                       zip(geometries, features)]
            extend_records(results, records=records, config=config)
            executor(sql=insert_sql, data=records)
            records.clear()
    return query.target
# End _simplify function


if __name__ == '__main__':  # pragma: no cover
    pass
