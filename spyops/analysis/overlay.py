# -*- coding: utf-8 -*-
"""
Overlay
"""


from typing import TYPE_CHECKING

from spyops.analysis.util import (
    _difference, _get_converted_operator,
    _intersect, _symmetrical_difference)
from spyops.geometry.convert import get_geometry_converters
from spyops.geometry.validate import get_validated_geometries
from spyops.query.analysis.overlay import (
    QueryErase, QueryIntersectClassic, QueryIntersectPairwise,
    QuerySymmetricalDifferenceClassic, QuerySymmetricalDifferencePairwise,
    QueryUnionClassic, QueryUnionPairwise)
from spyops.shared.constant import (
    ALGORITHM_OPTION, ATTRIBUTE_OPTION, OPERATOR, OUTPUT_TYPE_OPTION, SOURCE,
    TARGET)
from spyops.shared.enumeration import (
    AlgorithmOption, AttributeOption, OutputTypeOption)
from spyops.shared.field import GEOM_TYPE_POLYGONS
from spyops.shared.hint import XY_TOL
from spyops.validation import (
    validate_enumeration, validate_feature_class, validate_geometry_dimension,
    validate_output_type, validate_overwrite_input, validate_result,
    validate_crs, validate_xy_tolerance)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['erase', 'intersect', 'symmetrical_difference', 'union']


@validate_result()
@validate_feature_class(SOURCE)
@validate_feature_class(OPERATOR)
@validate_feature_class(TARGET, exists=False)
@validate_xy_tolerance()
@validate_geometry_dimension(SOURCE, OPERATOR)
@validate_crs(SOURCE, OPERATOR)
@validate_overwrite_input(TARGET, SOURCE, OPERATOR)
def erase(source: 'FeatureClass', operator: 'FeatureClass',
          target: 'FeatureClass', *,
          xy_tolerance: XY_TOL = None) -> 'FeatureClass':
    """
    Erase

    Removes the portion of the input feature class that overlaps with the
    operator feature class.
    """
    query = QueryErase(source, target=target, operator=operator,
                       xy_tolerance=xy_tolerance)
    if not query.has_intersection:
        return query.target_full
    query.process_disjoint()
    geoms = get_validated_geometries(
        query.operator, select_sql=query.select_operator,
        transformer=query.operator_transformer)
    _difference(
        source=query.source, source_transformer=query.source_transformer,
        select_sql=query.select_source, insert_sql=query.insert,
        overlay_geoms=geoms, overlay_transformer=query.operator_transformer,
        target=query.target, config=query.geometry_config,
        grid_size=query.grid_size)
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
@validate_crs(SOURCE, OPERATOR)
@validate_output_type(OUTPUT_TYPE_OPTION, SOURCE)
@validate_overwrite_input(TARGET, SOURCE, OPERATOR)
def intersect(source: 'FeatureClass', operator: 'FeatureClass',
              target: 'FeatureClass', *,
              attribute_option: AttributeOption = AttributeOption.ALL,
              output_type_option: OutputTypeOption = OutputTypeOption.SAME,
              algorithm_option: AlgorithmOption = AlgorithmOption.PAIRWISE,
              xy_tolerance: XY_TOL = None) -> 'FeatureClass':
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
    src_convert, op_convert = get_geometry_converters(
        source, operator=operator, output_type_option=output_type_option)
    op_features, op_geoms = _get_converted_operator(
        query=query, converter=op_convert,
        transformer=query.operator_transformer)
    return _intersect(query=query, op_features=op_features, op_geoms=op_geoms,
                      src_convert=src_convert)
# End intersect function


@validate_result()
@validate_feature_class(SOURCE)
@validate_feature_class(OPERATOR)
@validate_feature_class(TARGET, exists=False)
@validate_enumeration(ATTRIBUTE_OPTION, AttributeOption)
@validate_enumeration(ALGORITHM_OPTION, AlgorithmOption)
@validate_xy_tolerance()
@validate_geometry_dimension(SOURCE, OPERATOR, same=True)
@validate_crs(SOURCE, OPERATOR)
@validate_overwrite_input(TARGET, SOURCE, OPERATOR)
def symmetrical_difference(source: 'FeatureClass', operator: 'FeatureClass',
                           target: 'FeatureClass', *,
                           attribute_option: AttributeOption = AttributeOption.ALL,
                           algorithm_option: AlgorithmOption = AlgorithmOption.PAIRWISE,
                           xy_tolerance: XY_TOL = None) -> 'FeatureClass':
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
    _symmetrical_difference(query)
    return query.target
# End symmetrical_difference function


@validate_result()
@validate_feature_class(SOURCE, geometry_types=GEOM_TYPE_POLYGONS)
@validate_feature_class(OPERATOR, geometry_types=GEOM_TYPE_POLYGONS)
@validate_feature_class(TARGET, exists=False)
@validate_enumeration(ATTRIBUTE_OPTION, AttributeOption)
@validate_enumeration(ALGORITHM_OPTION, AlgorithmOption)
@validate_xy_tolerance()
@validate_crs(SOURCE, OPERATOR)
@validate_overwrite_input(TARGET, SOURCE, OPERATOR)
def union(source: 'FeatureClass', operator: 'FeatureClass',
          target: 'FeatureClass', *,
          attribute_option: AttributeOption = AttributeOption.ALL,
          algorithm_option: AlgorithmOption = AlgorithmOption.PAIRWISE,
          xy_tolerance: XY_TOL = None) -> 'FeatureClass':
    """
    Union

    Combines the geometries from the source and operator feature classes into
    a single output feature class. The output contains all features from both
    inputs, with overlapping areas split into separate features. Optionally,
    extends the output feature class with attributes from the operator feature
    class. Only polygon geometry types are supported.
    """
    if algorithm_option == AlgorithmOption.CLASSIC:
        cls = QuerySymmetricalDifferenceClassic
    else:
        cls = QuerySymmetricalDifferencePairwise
    query = cls(source=source, target=target, operator=operator,
                attribute_option=attribute_option, xy_tolerance=xy_tolerance)
    _symmetrical_difference(query)
    if algorithm_option == AlgorithmOption.CLASSIC:
        cls = QueryUnionClassic
    else:
        cls = QueryUnionPairwise
    query = cls(source=query.source, source_fid=query.input_fid_source,
                operator=query.operator, operator_fid=query.input_fid_operator,
                target=query.target, attribute_option=attribute_option,
                xy_tolerance=xy_tolerance)
    if not query.has_intersection:
        return query.target
    src_convert, op_convert = get_geometry_converters(
        source, operator=operator, output_type_option=OutputTypeOption.SAME)
    op_features, op_geoms = _get_converted_operator(
        query=query, converter=op_convert,
        transformer=query.operator_transformer)
    return _intersect(query=query, op_features=op_features, op_geoms=op_geoms,
                      src_convert=src_convert)
# End union function


if __name__ == '__main__':  # pragma: no cover
    pass
