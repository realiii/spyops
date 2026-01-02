# -*- coding: utf-8 -*-
"""
Overlay
"""


from collections import defaultdict

from fudgeo import FeatureClass
from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany
from shapely import STRtree, set_precision
from shapely.io import from_wkb

from geomio.query.overlay import (
    QueryErase, QueryIntersectClassic, QueryIntersectPairwise)
from geomio.shared.constant import (
    ALGORITHM_OPTION, ATTRIBUTE_OPTION, OPERATOR, OUTPUT_TYPE_OPTION, SOURCE,
    TARGET)
from geomio.shared.enumeration import (
    AlgorithmOption, AttributeOption, OutputTypeOption)
from geomio.shared.hint import XY_TOL
from geomio.shared.util import extend_records
from geomio.shared.validation import (
    validate_enumeration, validate_feature_class, validate_output_type,
    validate_result, validate_same_crs, validate_xy_tolerance)


@validate_result()
@validate_feature_class(SOURCE)
@validate_feature_class(OPERATOR)
@validate_feature_class(TARGET, exists=False)
@validate_xy_tolerance()
@validate_same_crs(SOURCE, OPERATOR)
def erase(source: FeatureClass, operator: FeatureClass, target: FeatureClass, *,
          xy_tolerance: XY_TOL = None) -> FeatureClass:
    """
    Erase

    Removes the portion of the input feature class that overlaps with the
    operator feature class.
    """
    query = QueryErase(source, target=target, operator=operator)
    if not query.has_intersection:
        return query.target_full
    records = []
    geometry = query.geometry
    insert_sql = query.insert
    _process_disjoint(query, xy_tolerance=xy_tolerance)
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            geometries = [from_wkb(g.wkb) for g, *_ in features]
            intersects = geometry.intersects(geometries)
            keepers = [f for f, i in zip(features, intersects) if not i]
            geoms = [g for g, i in zip(geometries, intersects) if not i]
            if xy_tolerance is not None:
                geoms = set_precision(geoms, grid_size=xy_tolerance)
            results = [(geom, attrs) for geom, (_, *attrs) in
                       zip(geoms, keepers)]
            extend_records(results, records=records, config=query.config)
            changers = [f for f, i in zip(features, intersects) if i]
            geoms = [g for g, i in zip(geometries, intersects) if i]
            results = [(geom.difference(geometry, grid_size=xy_tolerance), attrs)
                       for geom, (_, *attrs) in zip(geoms, changers)]
            extend_records(results, records=records, config=query.config)
            executor(sql=insert_sql, data=records)
            records.clear()
    return query.target
# End erase function


@validate_result()
@validate_feature_class(SOURCE)
@validate_feature_class(OPERATOR)
@validate_feature_class(TARGET, exists=False)
@validate_enumeration(ATTRIBUTE_OPTION, AttributeOption)
@validate_enumeration(OUTPUT_TYPE_OPTION, OutputTypeOption)
@validate_enumeration(ALGORITHM_OPTION, AlgorithmOption)
@validate_xy_tolerance()
@validate_same_crs(SOURCE, OPERATOR)
@validate_output_type(OUTPUT_TYPE_OPTION, SOURCE)
def intersect(source: FeatureClass, operator: FeatureClass,
              target: FeatureClass, *,
              attribute_option: AttributeOption = AttributeOption.ALL,
              output_type_option: OutputTypeOption = OutputTypeOption.SAME,
              algorithm_option: AlgorithmOption = AlgorithmOption.PAIRWISE,
              xy_tolerance: XY_TOL = None) -> FeatureClass:
    """
    Intersect

    Extracts the portion of the input feature class that overlaps with the
    operator feature class.  Optionally, extends the output feature class
    with attributes from the operator feature class.
    """
    if algorithm_option == AlgorithmOption.CLASSIC:
        cls = QueryIntersectClassic
    else:
        cls = QueryIntersectPairwise
    query = cls(source=source, target=target, operator=operator,
                attribute_option=attribute_option,
                output_type_option=output_type_option,
                xy_tolerance=xy_tolerance)
    if not query.has_intersection:
        return query.target_empty
    op_geoms = []
    op_features = []
    with query.operator.geopackage.connection as cin:
        cursor = cin.execute(query.select_operator)
        while features := cursor.fetchmany(FETCH_SIZE):
            op_features.extend(features)
            op_geoms.extend([from_wkb(g.wkb) for g, *_ in op_features])
    records = []
    insert_sql = query.insert
    tree = STRtree(op_geoms)
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            geometries = [from_wkb(g.wkb) for g, *_ in features]
            intersects = tree.query(geometries, predicate='intersects')
            if not len(intersects):
                continue
            grouper = defaultdict(list)
            for src_idx, op_idx in intersects.T.tolist():
                grouper[op_idx].append(src_idx)
            results = []
            for op_idx, indexes in grouper.items():
                op_attr = op_features[op_idx][1:]
                op_geom = op_geoms[op_idx]
                src_attrs = [features[idx][1:] for idx in indexes]
                if xy_tolerance is not None:
                    intersections = op_geom.intersection(
                        [geometries[idx] for idx in indexes],
                        grid_size=xy_tolerance)
                else:
                    intersections = op_geom.intersection(
                        [geometries[idx] for idx in indexes])
                results.extend([
                    (g, (*src_attr, *op_attr))
                    for g, src_attr in zip(intersections, src_attrs)])
            extend_records(results, records=records, config=query.config)
            executor(sql=insert_sql, data=records)
            records.clear()
    return query.target
# End intersect function


def _process_disjoint(query: QueryErase, xy_tolerance: XY_TOL) -> None:
    """
    Process Disjoint Features
    """
    if not query.select_disjoint:
        return
    records = []
    insert_sql = query.insert
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select_disjoint)
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
# End _process_disjoint function


if __name__ == '__main__':  # pragma: no cover
    pass
