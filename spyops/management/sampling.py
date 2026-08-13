# -*- coding: utf-8 -*-
"""
Data Management for Sampling
"""


from typing import TYPE_CHECKING

from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany

from spyops.geometry.util import filter_features
from spyops.query.management.sampling import (
    QueryGeneratePointsAlongLinesDistance, QueryGeneratePointsAlongLinesField,
    QueryGeneratePointsAlongLinesPercentage)
from spyops.shared.enumeration import DistanceTypeOption, PlacementOption
from spyops.shared.field import GEOM_TYPE_LINES, GEOM_TYPE_POLYGONS
from spyops.shared.hint import DISTANCE
from spyops.shared.keywords import (
    DISTANCE_TYPE, PLACEMENT, PLACEMENT_OPTION, SOURCE)
from spyops.shared.records import extend_records
from spyops.validation import (
    validate_overwrite_source, validate_placement, validate_result,
    validate_source_feature_class, validate_str_enumeration,
    validate_target_feature_class)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['generate_points_along_lines']


@validate_result()
@validate_source_feature_class(geometry_types=(
        *GEOM_TYPE_LINES, *GEOM_TYPE_POLYGONS))
@validate_target_feature_class()
@validate_str_enumeration(PLACEMENT_OPTION, PlacementOption)
@validate_str_enumeration(DISTANCE_TYPE, DistanceTypeOption)
@validate_placement(PLACEMENT, element_name=SOURCE, enum_name=PLACEMENT_OPTION)
@validate_overwrite_source()
def generate_points_along_lines(source: 'FeatureClass', target: 'FeatureClass',
                                placement: DISTANCE, *,
                                placement_option: PlacementOption = (
                                        PlacementOption.DISTANCE),
                                include_end_points: bool = False,
                                distance_type: DistanceTypeOption = (
                                        DistanceTypeOption.PLANAR),
                                where_clause: str = '') \
        -> 'FeatureClass':
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
    records = []
    kwargs = dict(source=source, target=target, placement=placement,
                  include_end_points=include_end_points,
                  distance_type=distance_type, where_clause=where_clause)
    if placement_option == PlacementOption.PERCENTAGE:
        query = QueryGeneratePointsAlongLinesPercentage(**kwargs)
    elif placement_option == PlacementOption.FIELD:
        query = QueryGeneratePointsAlongLinesField(**kwargs)
    else:
        query = QueryGeneratePointsAlongLinesDistance(**kwargs)
    insert_sql = query.insert
    config = query.geometry_config
    with (query.source.geopackage.connection as cin,
          query.target.geopackage.connection as cout,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            results = query.generate_points(features)
            extend_records(results, records=records, config=config)
            executor(sql=insert_sql, data=records)
            records.clear()
    query.show_warning()
    return query.target
# End generate_points_along_lines function


if __name__ == '__main__':  # pragma: no cover
    pass
