# -*- coding: utf-8 -*-
"""
Extraction
"""

from typing import Callable

from fudgeo import FeatureClass, Table
from fudgeo.constant import FETCH_SIZE
from shapely.io import from_wkb

from geomio.analysis.sql import (
    build_query_components, build_sql_select_by_attributes)
from geomio.analysis.util import shared_select
from geomio.shared.constants import (
    GEOPACKAGE, GROUP_FIELDS, OPERATOR, SOURCE, SQL_EMPTY, TARGET)
from geomio.shared.field import (
    GEOM_TYPE_POLYGONS, TEXT_AND_NUMBERS, make_field_names)
from geomio.shared.geometry import overlay_config
from geomio.shared.hints import ELEMENT, FIELDS, FIELD_NAMES, FLOAT, GPKG
from geomio.shared.util import (
    add_spatial_index, element_names, extend_records, make_unique_name)
from geomio.shared.validation import (
    validate_element, validate_feature_class, validate_field,
    validate_geopackage, validate_result, validate_same_crs, validate_table,
    validate_xy_tolerance)


__all__ = ['table_select', 'select', 'extract_rows', 'extract_features',
           'split_by_attributes', 'clip']


@validate_result()
@validate_table(TARGET, exists=False)
@validate_table(SOURCE)
def table_select(source: Table, target: Table, where_clause: str = '',
                 overwrite: bool = False) -> Table:
    """
    Table Select

    Select rows from a table using a where clause (optional) and write results
    to a target table.  Optionally overwrite the target table if it exists.
    """
    return shared_select(source=source, target=target,
                         where_clause=where_clause, overwrite=overwrite)
# End table_select function


@validate_result()
@validate_feature_class(TARGET, exists=False)
@validate_feature_class(SOURCE)
def select(source: FeatureClass, target: FeatureClass, where_clause: str = '',
           overwrite: bool = False) -> FeatureClass:
    """
    Select

    Select features from a feature class using a where clause (optional) and
    write results to a target feature class.  Optionally overwrite the target
    feature class if it exists.
    """
    return shared_select(source=source, target=target,
                         where_clause=where_clause, overwrite=overwrite)
# End select function


@validate_result()
@validate_geopackage(GEOPACKAGE)
@validate_field(GROUP_FIELDS, data_types=TEXT_AND_NUMBERS,
                element_name=SOURCE, exclude_primary=False)
@validate_element(SOURCE)
def split_by_attributes(source: ELEMENT, group_fields: FIELDS | FIELD_NAMES,
                        geopackage: GPKG) -> list[ELEMENT]:
    """
    Split by Attributes

    Split an input table or feature class by groups of attributes.
    """
    group_names = make_field_names(group_fields)
    group_count_sql, insert_sql, select_sql = build_sql_select_by_attributes(
        source, group_names=group_names)
    elements = []
    target_names = element_names(geopackage)
    with geopackage.connection as conn:
        source_conn = source.geopackage.connection
        cursor = source_conn.execute(group_count_sql)
        group_count, = cursor.fetchone()
        for i in range(1, group_count + 1):
            cursor = source_conn.execute(select_sql, (i,))
            name = make_unique_name(name=source.name, names=target_names)
            element = add_spatial_index(source.copy(
                name=name, description=source.description,
                where_clause=SQL_EMPTY, geopackage=geopackage))
            elements.append(element)
            while records := cursor.fetchmany(FETCH_SIZE):
                conn.executemany(
                    insert_sql.format(element.escaped_name), records)
    return elements
# End split_by_attributes function


@validate_result()
@validate_same_crs(SOURCE, OPERATOR)
@validate_xy_tolerance()
@validate_feature_class(TARGET, exists=False)
@validate_feature_class(OPERATOR, geometry_types=GEOM_TYPE_POLYGONS)
@validate_feature_class(SOURCE)
def clip(source: FeatureClass, operator: FeatureClass, target: FeatureClass,
         overwrite: bool = False, xy_tolerance: FLOAT = None) -> FeatureClass:
    """
    Clip

    Extracts features using the features of a polygon feature class. Extracted
    features are cut along the edges of the clipping polygons.
    """
    components = build_query_components(
        source, target=target, operator=operator)
    target = shared_select(
        source=source, target=target, where_clause=SQL_EMPTY,
        overwrite=overwrite)
    if not components.has_intersection:
        return target
    records = []
    config = overlay_config(source, operator=operator)
    polygon = config.geometry
    with target.geopackage.connection as conn:
        cursor = source.geopackage.connection.execute(components.sql_touches)
        while features := cursor.fetchmany(FETCH_SIZE):
            geometries = [from_wkb(g.wkb) for g, *_ in features]
            intersects = polygon.intersects(geometries)
            if not intersects.any():
                continue
            keepers = [f for f, keep in zip(features, intersects) if keep]
            geometries = [g for g, keep in zip(geometries, intersects) if keep]
            results = [(g, polygon.intersection(geom, grid_size=xy_tolerance), attrs)
                       for geom, (g, *attrs) in zip(geometries, keepers)]
            extend_records(results, records=records, config=config)
            conn.executemany(components.sql_insert, records)
            records.clear()
    return target
# End clip function


# Aliases
extract_rows: Callable[[Table, Table, str, bool], Table] = table_select
extract_features: Callable[[FeatureClass, FeatureClass, str, bool], FeatureClass] = select


if __name__ == '__main__':  # pragma: no cover
    pass
