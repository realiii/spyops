# -*- coding: utf-8 -*-
"""
Extraction
"""


from typing import Callable

from fudgeo import FeatureClass, Field, Table
from fudgeo.constant import FETCH_SIZE
from shapely import box
from shapely.io import from_wkb

from geomio.analysis.sql import (
    build_analysis, build_sql_select_by_attributes)
from geomio.shared.constant import (
    FIELD, GROUP_FIELDS, OPERATOR, SOURCE, SQL_EMPTY, TARGET, UNDERSCORE)
from geomio.shared.element import copy_element
from geomio.shared.field import (
    GEOM_TYPE_POLYGONS, TEXTS, TEXT_AND_NUMBERS, make_field_names)
from geomio.shared.geometry import extent_from_feature_class, overlay_config
from geomio.shared.hint import ELEMENT, FIELDS, FIELD_NAMES, GPKG, XY_TOL
from geomio.shared.setting import ANALYSIS_SETTINGS
from geomio.shared.util import (
    element_names, extend_records, make_unique_name, make_valid_name)
from geomio.shared.validation import (
    validate_element, validate_feature_class, validate_field,
    validate_geopackage, validate_result, validate_same_crs, validate_table,
    validate_xy_tolerance)


__all__ = ['table_select', 'select', 'extract_rows', 'extract_features',
           'split_by_attributes', 'clip', 'split']


@validate_result()
@validate_table(TARGET, exists=False)
@validate_table(SOURCE)
def table_select(source: Table, target: Table, *,
                 where_clause: str = '') -> Table:
    """
    Table Select

    Select rows from a table using a where clause (optional) and write results
    to a target table.
    """
    return copy_element(source=source, target=target, where_clause=where_clause)
# End table_select function


@validate_result()
@validate_feature_class(TARGET, exists=False)
@validate_feature_class(SOURCE)
def select(source: FeatureClass, target: FeatureClass, *,
           where_clause: str = '') -> FeatureClass:
    """
    Select

    Select features from a feature class using a where clause (optional) and
    write results to a target feature class.
    """
    return copy_element(source=source, target=target, where_clause=where_clause)
# End select function


@validate_result()
@validate_geopackage()
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
            element = copy_element(
                source=source, where_clause=SQL_EMPTY,
                target=FeatureClass(geopackage=geopackage, name=name))
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
def clip(source: FeatureClass, operator: FeatureClass, target: FeatureClass, *,
         xy_tolerance: XY_TOL = None) -> FeatureClass:
    """
    Clip

    Extracts features using the features of a polygon feature class. Extracted
    features are cut along the edges of the clipping polygons.
    """
    components = build_analysis(
        source, target=target, operator=operator, use_empty=True)
    if not components.has_intersection:
        return components.target
    records = []
    config = overlay_config(source, operator=operator)
    polygon = config.geometry
    with target.geopackage.connection as conn:
        cursor = source.geopackage.connection.execute(components.sql_intersect)
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


@validate_result()
@validate_same_crs(SOURCE, OPERATOR)
@validate_xy_tolerance()
@validate_geopackage()
@validate_field(FIELD, data_types=TEXTS, single=True)
@validate_feature_class(OPERATOR, geometry_types=GEOM_TYPE_POLYGONS)
@validate_feature_class(SOURCE)
def split(source: FeatureClass, operator: FeatureClass, field: Field | str,
          geopackage: GPKG, *, xy_tolerance: XY_TOL = None) -> list[FeatureClass]:
    """
    Split

    Extracts features for each polygon in the splitting feature class and uses
    values from the specified field to name the output feature classes.
    """
    features = []
    split_extent = extent_from_feature_class(operator)
    source_extent = extent_from_feature_class(source)
    if not box(*split_extent).intersects(box(*source_extent)):
        return features
    splitters = split_by_attributes(
        operator, group_fields=[field],
        geopackage=ANALYSIS_SETTINGS.scratch_workspace)
    for s in splitters:
        cursor = s.select(fields=[field], limit=1, include_geometry=False)
        value, = cursor.fetchone()
        name = make_valid_name(
            f'{source.name}{UNDERSCORE}{value}', prefix='split')
        target = clip(
            source, operator=s, xy_tolerance=xy_tolerance,
            target=FeatureClass(geopackage=geopackage, name=name))
        features.append(target)
    return features
# End split function


# Aliases
extract_rows: Callable[[Table, Table, str, bool], Table] = table_select
extract_features: Callable[[FeatureClass, FeatureClass, str, bool], FeatureClass] = select


if __name__ == '__main__':  # pragma: no cover
    pass
