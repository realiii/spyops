# -*- coding: utf-8 -*-
"""
Generalization
"""


from typing import TYPE_CHECKING

from fudgeo.enumeration import ShapeType

from spyops.cartography.util import _simplify, _smooth
from spyops.query.cartography.generalization import (
    QuerySimplifyLine, QuerySimplifyPolygon, QuerySmoothLine,
    QuerySmoothPolygon)
from spyops.shared.enumeration import (
    SimplifyAlgorithmOption, SmoothAlgorithmOption)
from spyops.shared.hint import UNIT_TOLERANCE, XY_TOL
from spyops.shared.keywords import ALGORITHM_OPTION, SOURCE, TOLERANCE
from spyops.validation import (
    validate_feature_class, validate_linear_unit, validate_overwrite_source,
    validate_result, validate_str_enumeration, validate_target_feature_class,
    validate_xy_tolerance)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['simplify_line', 'simplify_polygon', 'smooth_line', 'smooth_polygon']


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
    query = QuerySimplifyLine(
        source, target=target, where_clause=where_clause,
        xy_tolerance=xy_tolerance, algorithm_option=algorithm_option)
    return _simplify(
        query, tolerance=tolerance, preserve_topology=preserve_topology)
# End simplify_line function


@validate_result()
@validate_feature_class(SOURCE, geometry_types=(
        ShapeType.polygon, ShapeType.multi_polygon))
@validate_target_feature_class()
@validate_linear_unit(TOLERANCE, feature_class_name=SOURCE,
                      as_number=True, use_source_crs=False)
@validate_str_enumeration(ALGORITHM_OPTION, SimplifyAlgorithmOption)
@validate_xy_tolerance()
@validate_overwrite_source()
def simplify_polygon(source: 'FeatureClass', target: 'FeatureClass',
                     tolerance: UNIT_TOLERANCE, *,
                     preserve_topology: bool = True,
                     algorithm_option: SimplifyAlgorithmOption = (
                             SimplifyAlgorithmOption.POINT_REMOVE),
                     xy_tolerance: XY_TOL = None,
                     where_clause: str = '') -> 'FeatureClass':
    """
    Simplify Polygon

    Removes vertices from polygon features while retaining overall polygon
    shape based on the specified tolerance.
    """
    query = QuerySimplifyPolygon(
        source, target=target, where_clause=where_clause,
        xy_tolerance=xy_tolerance, algorithm_option=algorithm_option)
    return _simplify(
        query, tolerance=tolerance, preserve_topology=preserve_topology)
# End simplify_polygon function


@validate_result()
@validate_feature_class(SOURCE, geometry_types=(
        ShapeType.linestring, ShapeType.multi_linestring))
@validate_target_feature_class()
@validate_linear_unit(TOLERANCE, feature_class_name=SOURCE,
                      as_number=True, use_source_crs=False)
@validate_str_enumeration(ALGORITHM_OPTION, SmoothAlgorithmOption)
@validate_xy_tolerance()
@validate_overwrite_source()
def smooth_line(source: 'FeatureClass', target: 'FeatureClass',
                tolerance: UNIT_TOLERANCE = 0, *,
                algorithm_option: SmoothAlgorithmOption = (
                          SmoothAlgorithmOption.PAEK),
                xy_tolerance: XY_TOL = None,
                where_clause: str = '') -> 'FeatureClass':
    """
    Smooth Line

    Smooth line features to give a more aesthetically pleasing shape while
    retaining overall line shape.  Algorithm options include Polynomial
    Approximation with Exponential Kernel (PAEK) and Cubic Bezier
    Curves (BEZIER).  The tolerance specified applies to PAEK only.
    """
    query = QuerySmoothLine(
        source, target=target, where_clause=where_clause,
        xy_tolerance=xy_tolerance, algorithm_option=algorithm_option)
    return _smooth(query, tolerance=tolerance)
# End simplify_line function


@validate_result()
@validate_feature_class(SOURCE, geometry_types=(
        ShapeType.polygon, ShapeType.multi_polygon))
@validate_target_feature_class()
@validate_linear_unit(TOLERANCE, feature_class_name=SOURCE,
                      as_number=True, use_source_crs=False)
@validate_str_enumeration(ALGORITHM_OPTION, SmoothAlgorithmOption)
@validate_xy_tolerance()
@validate_overwrite_source()
def smooth_polygon(source: 'FeatureClass', target: 'FeatureClass',
                   tolerance: UNIT_TOLERANCE = 0, *,
                   algorithm_option: SmoothAlgorithmOption = (
                           SmoothAlgorithmOption.PAEK),
                   xy_tolerance: XY_TOL = None,
                   where_clause: str = '') -> 'FeatureClass':
    """
    Smooth Polygon

    Smooth polygon features to give a more aesthetically pleasing shape while
    retaining overall polygon shape.  Algorithm options include Polynomial
    Approximation with Exponential Kernel (PAEK) and Cubic Bezier
    Curves (BEZIER).  The tolerance specified applies to PAEK only.
    """
    query = QuerySmoothPolygon(
        source, target=target, where_clause=where_clause,
        xy_tolerance=xy_tolerance, algorithm_option=algorithm_option)
    return _smooth(query, tolerance=tolerance)
# End smooth_polygon function


if __name__ == '__main__':  # pragma: no cover
    pass
