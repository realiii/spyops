# -*- coding: utf-8 -*-
"""
Proximity
"""


from typing import TYPE_CHECKING

from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany

from spyops.crs.enumeration import DistanceUnit
from spyops.query.analysis.proximity import (
    QueryBufferDissolveAll, QueryBufferDissolveList, QueryBufferDissolveNone,
    QueryMultipleBuffer)
from spyops.shared.enumeration import (
    BufferTypeOption, DissolveOption, EndOption, SideOption)
from spyops.shared.hint import DISTANCE, FIELDS, FIELD_NAMES, XY_TOL
from spyops.shared.keywords import (
    BUFFER_TYPE, DISSOLVE_OPTION, DISTANCES, DISTANCE_ARG, DISTANCE_UNIT,
    END_OPTION, GROUP_FIELDS, RESOLUTION, SIDE_OPTION, SOURCE)
from spyops.shared.records import extend_records
from spyops.validation import (
    validate_dissolve_option, validate_distance, validate_field,
    validate_overwrite_source, validate_range, validate_result,
    validate_side_option, validate_source_feature_class,
    validate_str_enumeration, validate_target_feature_class, validate_values,
    validate_xy_tolerance)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['buffer', 'multiple_buffer']


@validate_result()
@validate_source_feature_class()
@validate_target_feature_class()
@validate_distance(DISTANCE_ARG, element_name=SOURCE)
@validate_str_enumeration(BUFFER_TYPE, BufferTypeOption)
@validate_str_enumeration(DISSOLVE_OPTION, DissolveOption)
@validate_field(GROUP_FIELDS, element_name=SOURCE, is_optional=True)
@validate_dissolve_option(DISSOLVE_OPTION, GROUP_FIELDS)
@validate_side_option(SIDE_OPTION, SOURCE)
@validate_str_enumeration(END_OPTION, EndOption)
@validate_range(RESOLUTION, default=32, min_value=8, max_value=256, type_=int)
@validate_xy_tolerance()
@validate_overwrite_source()
def buffer(source: 'FeatureClass', target: 'FeatureClass', distance: DISTANCE,
           *, buffer_type: BufferTypeOption = BufferTypeOption.PLANAR,
           dissolve_option: DissolveOption = DissolveOption.NONE,
           group_fields: FIELDS | FIELD_NAMES = (),
           side_option: SideOption = SideOption.FULL,
           end_option: EndOption = EndOption.ROUND, resolution: int = 32,
           xy_tolerance: XY_TOL = None) -> 'FeatureClass':
    """
    Buffer

    Create polygons that are a specified distance around the input features.

    All geometry types are supported.  However, not all options apply to or
    are useful on all geometry types.

    The output will not have Z or M values unless the OUTPUT_Z_OPTION or
    OUTPUT_M_OPTION environment variables are set.
    """
    records = []
    kwargs = dict(source=source, target=target, distance=distance,
                  buffer_type=buffer_type, fields=group_fields,
                  side_option=side_option, end_option=end_option,
                  resolution=resolution, xy_tolerance=xy_tolerance)
    if dissolve_option == DissolveOption.NONE:
        query = QueryBufferDissolveNone(**kwargs)
    elif dissolve_option == DissolveOption.LIST:
        query = QueryBufferDissolveList(**kwargs)
    else:
        query = QueryBufferDissolveAll(**kwargs)
    insert_sql = query.insert
    config = query.geometry_config
    with (query.source.geopackage.connection as cin,
          query.target.geopackage.connection as cout,
          ExecuteMany(connection=cout, table=query.target) as executor):
        if dissolve_option in (DissolveOption.NONE, DissolveOption.LIST):
            cursor = cin.execute(query.select)
            while rows := cursor.fetchmany(FETCH_SIZE):
                geoms = next(query.dissolved_geometries(), {})
                results = [(geoms.pop(i, None), attrs) for i, *attrs in rows]
                extend_records(results, records=records, config=config)
                executor(sql=insert_sql, data=records)
                records.clear()
        else:
            geoms = next(query.dissolved_geometries(), {})
            results = [(g, ()) for g in geoms.values()]
            extend_records(results, records=records, config=config)
            executor(sql=insert_sql, data=records)
            records.clear()
    query.show_warning()
    return query.target
# End buffer function


@validate_result()
@validate_source_feature_class()
@validate_target_feature_class()
@validate_str_enumeration(DISTANCE_UNIT, DistanceUnit)
@validate_values(DISTANCES)
@validate_str_enumeration(BUFFER_TYPE, BufferTypeOption)
@validate_range(RESOLUTION, default=32, min_value=8, max_value=256, type_=int)
@validate_xy_tolerance()
@validate_overwrite_source()
def multiple_buffer(source: 'FeatureClass', target: 'FeatureClass',
                    distance_unit: DistanceUnit, distances: list[float], *,
                    buffer_type: BufferTypeOption = BufferTypeOption.PLANAR,
                    overlapping: bool = False, only_outside: bool = False,
                    field_name: str | None = DISTANCE_ARG, resolution: int = 32,
                    xy_tolerance: XY_TOL = None) -> 'FeatureClass':
    """
    Multiple Buffer

    Generate polygons around the input features using the input distances.  The
    polygons can be created as overlapping or non-overlapping.

    All geometry types are supported.  For polygon feature classes the input
    feature can be removed from the buffer by using the only outside option
    set to True.

    The output will not have Z or M values unless the OUTPUT_Z_OPTION or
    OUTPUT_M_OPTION environment variables are set.
    """
    records = []
    query = QueryMultipleBuffer(
        source=source, target=target, distance_unit=distance_unit,
        distances=distances, buffer_type=buffer_type, overlapping=overlapping,
        only_outside=only_outside, field_name=field_name, resolution=resolution,
        xy_tolerance=xy_tolerance)
    insert_sql = query.insert
    select_sql = query.select
    config = query.geometry_config
    with (query.source.geopackage.connection as cin,
          query.target.geopackage.connection as cout,
          ExecuteMany(connection=cout, table=query.target) as executor):
        if overlapping:
            for sub, update_sql in query:
                cursor = cin.execute(select_sql)
                while rows := cursor.fetchmany(FETCH_SIZE):
                    geoms = next(sub.dissolved_geometries(), {})
                    results = [(geoms.pop(i, None), attrs) for i, *attrs in rows]
                    extend_records(results, records=records, config=config)
                    executor(sql=insert_sql, data=records)
                    records.clear()
                    if update_sql:
                        cout.execute(update_sql)
        else:
            results = query.dissolved_geometries()
            extend_records(results, records=records, config=config)
            executor(sql=insert_sql, data=records)
            records.clear()
    return query.target
# End multiple_buffer function


if __name__ == '__main__':  # pragma: no cover
    pass
