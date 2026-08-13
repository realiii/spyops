# -*- coding: utf-8 -*-
"""
Data Management for Sampling
"""


from typing import TYPE_CHECKING

from spyops.management.util import _generate_along_lines
from spyops.query.management.sampling import (
    QueryGeneratePointsAlongLinesDistance, QueryGeneratePointsAlongLinesField,
    QueryGeneratePointsAlongLinesPercentage)
from spyops.shared.enumeration import DistanceTypeOption, PlacementOption
from spyops.shared.field import GEOM_TYPE_LINES, GEOM_TYPE_POLYGONS
from spyops.shared.hint import DISTANCE, TRANSECT_LENGTH
from spyops.shared.keywords import (
    DISTANCE_TYPE, LENGTH, PLACEMENT, PLACEMENT_OPTION, SOURCE)
from spyops.validation import (
    validate_linear_unit, validate_overwrite_source, validate_placement,
    validate_result, validate_source_feature_class, validate_str_enumeration,
    validate_target_feature_class)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['generate_points_along_lines', 'generate_transects_along_lines']


@validate_result()
@validate_source_feature_class(geometry_types=(
        *GEOM_TYPE_LINES, *GEOM_TYPE_POLYGONS))
@validate_target_feature_class()
@validate_str_enumeration(PLACEMENT_OPTION, PlacementOption)
@validate_str_enumeration(DISTANCE_TYPE, DistanceTypeOption)
@validate_placement(PLACEMENT, element_name=SOURCE, enum_name=PLACEMENT_OPTION)
@validate_overwrite_source()
def generate_points_along_lines(
        source: 'FeatureClass', target: 'FeatureClass', placement: DISTANCE, *,
        placement_option: PlacementOption = PlacementOption.DISTANCE,
        include_ends: bool = False,
        distance_type: DistanceTypeOption = DistanceTypeOption.PLANAR,
        where_clause: str = '') -> 'FeatureClass':
    """
    Generate Points Along Lines

    Create points along lines (linear rings) at the specified intervals based
    on the specified placement option.

    Placement option DISTANCE creates points at the specified distance
    interval, e.g. 100 metres will be placed at 200, 300, 400 meters, etc.

    Placement option PERCENTAGE creates points at the specified percentage
    interval e.g. 15 percent will be placed at 15, 30, 45, 60, 75, and
    90 percent of the line length.

    Placement option FIELD creates points differently based on the field
    data type and field value.

    * Numeric fields are treated as being distances defined in the same units
      as the source feature class spatial reference. For example, a value of
      200 will be handled as 200 meters if the source feature class spatial
      reference is in meters.
    * Text fields are treated as linear units and can contain one or more
      values separated by semicolons. If there is only one value in the text
      field, then it will be handled as an interval, for example, the string
      value '50 feet' will be used to repeat points along the linear feature
      at 50 ft intervals (e.g. 50, 100, ... 200, 250 ft, etc.)  If there are
      multiple values in the text field, then they will be treated as a list of
      specific distances, for example, the string value '50 feet;175 feet' will
      be used to place two points, one at 50 ft and the other at 175 ft.
    * Units for text values can be mixed across features and within the same
      field. For example, the string value '50 feet;175 meters' will be used to
      place two points, one at 50 ft and the other at 175 meters.  If a unit
      value is missing, then it will be assumed to be in the same units as the
      source feature class spatial reference.

    """
    if placement_option == PlacementOption.PERCENTAGE:
        cls = QueryGeneratePointsAlongLinesPercentage
    elif placement_option == PlacementOption.FIELD:
        cls = QueryGeneratePointsAlongLinesField
    else:
        cls = QueryGeneratePointsAlongLinesDistance
    # noinspection bad-argument-type
    query = cls(source=source, target=target, placement=placement,
                include_ends=include_ends, distance_type=distance_type,
                where_clause=where_clause)
    return _generate_along_lines(query)
# End generate_points_along_lines function


@validate_result()
@validate_source_feature_class(geometry_types=(
        *GEOM_TYPE_LINES, *GEOM_TYPE_POLYGONS))
@validate_target_feature_class()
@validate_linear_unit(LENGTH, feature_class_name=SOURCE)
@validate_str_enumeration(PLACEMENT_OPTION, PlacementOption)
@validate_str_enumeration(DISTANCE_TYPE, DistanceTypeOption)
@validate_placement(PLACEMENT, element_name=SOURCE, enum_name=PLACEMENT_OPTION)
@validate_overwrite_source()
def generate_transects_along_lines(
        source: 'FeatureClass', target: 'FeatureClass',
        placement: DISTANCE, *, length: TRANSECT_LENGTH,
        placement_option: PlacementOption = PlacementOption.DISTANCE,
        include_ends: bool = False,
        distance_type: DistanceTypeOption = DistanceTypeOption.PLANAR,
        where_clause: str = '') -> 'FeatureClass':
    """
    Generate Transects Along Lines

    Create transects along lines (linear rings) at the specified intervals based
    on the specified placement option.

    Length can be specified as a Linear Unit, Decimal Degrees, a number,
    or a string.  For example, Meters(100), DecimalDegrees(0.001), 100, or
    '100 meters'.  The length represents the total length of the transect.

    Placement option DISTANCE creates points at the specified distance
    interval, e.g. 100 metres will be placed at 200, 300, 400 meters, etc.

    Placement option PERCENTAGE creates points at the specified percentage
    interval e.g. 15 percent will be placed at 15, 30, 45, 60, 75, and
    90 percent of the line length.

    Placement option FIELD creates points differently based on the field
    data type and field value.

    * Numeric fields are treated as being distances defined in the same units
      as the source feature class spatial reference. For example, a value of
      200 will be handled as 200 meters if the source feature class spatial
      reference is in meters.
    * Text fields are treated as linear units and can contain one or more
      values separated by semicolons. If there is only one value in the text
      field, then it will be handled as an interval, for example, the string
      value '50 feet' will be used to repeat points along the linear feature
      at 50 ft intervals (e.g. 50, 100, ... 200, 250 ft, etc.)  If there are
      multiple values in the text field, then they will be treated as a list of
      specific distances, for example, the string value '50 feet;175 feet' will
      be used to place two points, one at 50 ft and the other at 175 ft.
    * Units for text values can be mixed across features and within the same
      field. For example, the string value '50 feet;175 meters' will be used to
      place two points, one at 50 ft and the other at 175 meters.  If a unit
      value is missing, then it will be assumed to be in the same units as the
      source feature class spatial reference.

    """
    pass
# End generate_transects_along_lines function


if __name__ == '__main__':  # pragma: no cover
    pass
