# -*- coding: utf-8 -*-
"""
Overlay
"""


from collections import defaultdict

from fudgeo import FeatureClass
from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany
from shapely.strtree import STRtree

from spyops.analysis.util import _difference
from spyops.geometry.convert import get_geometry_converters
from spyops.geometry.util import filter_features, to_shapely
from spyops.geometry.validate import get_validated_geometries
from spyops.query.overlay import (
    QueryErase, QueryIntersectClassic, QueryIntersectPairwise,
    QuerySymmetricalDifferenceClassic, QuerySymmetricalDifferencePairwise)
from spyops.shared.constant import (
    ALGORITHM_OPTION, ATTRIBUTE_OPTION, OPERATOR, OUTPUT_TYPE_OPTION, SOURCE,
    TARGET)
from spyops.shared.enumeration import (
    AlgorithmOption, AttributeOption, OutputTypeOption)
from spyops.shared.hint import XY_TOL
from spyops.shared.records import extend_records
from spyops.validation import (
    validate_enumeration, validate_feature_class, validate_geometry_dimension,
    validate_output_type, validate_overwrite_input, validate_result,
    validate_same_crs, validate_xy_tolerance)


__all__ = ['erase', 'intersect', 'symmetrical_difference']


@validate_result()
@validate_feature_class(SOURCE)
@validate_feature_class(OPERATOR)
@validate_feature_class(TARGET, exists=False)
@validate_xy_tolerance()
@validate_geometry_dimension(SOURCE, OPERATOR)
@validate_same_crs(SOURCE, OPERATOR)
@validate_overwrite_input(TARGET, SOURCE, OPERATOR)
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
    query.process_disjoint(xy_tolerance)
    geoms = get_validated_geometries(operator)
    _difference(source=query.source, select_sql=query.select_source,
                insert_sql=query.insert, overlay_geoms=geoms,
                target=query.target, config=query.geometry_config,
                xy_tolerance=xy_tolerance)
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
@validate_geometry_dimension(SOURCE, OPERATOR)
@validate_same_crs(SOURCE, OPERATOR)
@validate_output_type(OUTPUT_TYPE_OPTION, SOURCE)
@validate_overwrite_input(TARGET, SOURCE, OPERATOR)
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
    src_convert, op_convert = get_geometry_converters(
        source, operator=operator, output_type_option=output_type_option)
    with query.operator.geopackage.connection as cin:
        cursor = cin.execute(query.select_operator)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            op_features.extend(features)
            op_geoms.extend(to_shapely(features))
    op_geoms = op_convert(op_geoms)
    records = []
    tree = STRtree(op_geoms)
    insert_sql = query.insert
    config = query.geometry_config
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            geometries = src_convert(to_shapely(features))
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
                intersections = op_geom.intersection(
                    [geometries[idx] for idx in indexes],
                    grid_size=xy_tolerance)
                results.extend([
                    (g, (*src_attr, *op_attr))
                    for g, src_attr in zip(intersections, src_attrs)])
            extend_records(results, records=records, config=config)
            executor(sql=insert_sql, data=records)
            records.clear()
    return query.target
# End intersect function


@validate_result()
@validate_feature_class(SOURCE)
@validate_feature_class(OPERATOR)
@validate_feature_class(TARGET, exists=False)
@validate_enumeration(ATTRIBUTE_OPTION, AttributeOption)
@validate_enumeration(ALGORITHM_OPTION, AlgorithmOption)
@validate_xy_tolerance()
@validate_geometry_dimension(SOURCE, OPERATOR, same=True)
@validate_same_crs(SOURCE, OPERATOR)
@validate_overwrite_input(TARGET, SOURCE, OPERATOR)
def symmetrical_difference(source: FeatureClass, operator: FeatureClass,
                           target: FeatureClass, *,
                           attribute_option: AttributeOption = AttributeOption.ALL,
                           algorithm_option: AlgorithmOption = AlgorithmOption.PAIRWISE,
                           xy_tolerance: XY_TOL = None) -> FeatureClass:
    """
    Symmetrical Difference

    Extracts the portion of the input feature class and operator feature class
    that do not intersect.  Optionally, extends the output feature class
    with attributes from the operator feature class.
    """
    if algorithm_option == AlgorithmOption.CLASSIC:
        cls = QuerySymmetricalDifferenceClassic
    else:
        cls = QuerySymmetricalDifferencePairwise
    query = cls(source=source, target=target, operator=operator,
                attribute_option=attribute_option, xy_tolerance=xy_tolerance)
    geoms = get_validated_geometries(operator)
    _difference(source=query.source, select_sql=query.select_source,
                insert_sql=query.source_config.insert, overlay_geoms=geoms,
                target=query.target, config=query.geometry_config,
                xy_tolerance=xy_tolerance)
    geoms = get_validated_geometries(source)
    _difference(source=query.operator, select_sql=query.select_operator,
                insert_sql=query.operator_config.insert,
                overlay_geoms=geoms, target=query.target,
                config=query.geometry_config, xy_tolerance=xy_tolerance)
    return query.target
# End symmetrical_difference function


if __name__ == '__main__':  # pragma: no cover
    pass
