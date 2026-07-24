# -*- coding: utf-8 -*-
"""
Generalization
"""


from typing import TYPE_CHECKING

from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany
from fudgeo.enumeration import ShapeType

from spyops.geometry.util import filter_features, to_shapely
from spyops.geometry.wa import set_precision
from spyops.query.cartography.generalization import QuerySimplifyLine
from spyops.shared.enumeration import SimplifyAlgorithmOption
from spyops.shared.hint import UNIT_TOLERANCE, XY_TOL
from spyops.shared.keywords import ALGORITHM_OPTION, SOURCE, TOLERANCE
from spyops.shared.records import extend_records
from spyops.validation import (
    validate_feature_class, validate_linear_unit, validate_overwrite_source,
    validate_result, validate_str_enumeration, validate_target_feature_class,
    validate_xy_tolerance)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['simplify_line']


@validate_result()
@validate_feature_class(SOURCE, geometry_types=(
        ShapeType.linestring, ShapeType.multi_linestring))
@validate_target_feature_class()
@validate_linear_unit(TOLERANCE, feature_class_name=SOURCE,
                      as_number=True, use_source_crs=False)
@validate_str_enumeration(ALGORITHM_OPTION, SimplifyAlgorithmOption)
@validate_xy_tolerance()
@validate_overwrite_source()
def simplify_line(source: 'FeatureClass', target: 'FeatureClass',
                  tolerance: UNIT_TOLERANCE, *,
                  preserve_topology: bool = True,
                  algorithm_option: SimplifyAlgorithmOption = (
                          SimplifyAlgorithmOption.POINT_REMOVE),
                  xy_tolerance: XY_TOL = None,
                  where_clause: str = '') -> 'FeatureClass':
    """
    Simplify Line

    Removes vertices from line features while retaining overall line shape
    based on the specified tolerance.
    """
    records = []
    tolerance: float
    query = QuerySimplifyLine(
        source, target=target, tolerance=tolerance, where_clause=where_clause,
        xy_tolerance=xy_tolerance, algorithm_option=algorithm_option)
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
# End simplify_line function


if __name__ == '__main__':  # pragma: no cover
    pass
