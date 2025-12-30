# -*- coding: utf-8 -*-
"""
Extraction
"""


from typing import Callable

from fudgeo import FeatureClass, Table, Field
from fudgeo.constant import FETCH_SIZE
from shapely.io import from_wkb

from geomio.query.extract import QueryClip, QuerySplit, QuerySplitByAttributes
from geomio.shared.constant import (
    FIELD, GROUP_FIELDS, OPERATOR, SOURCE, SQL_EMPTY, TARGET, UNDERSCORE)
from geomio.shared.element import copy_element
from geomio.shared.field import GEOM_TYPE_POLYGONS, TEXTS, TEXT_AND_NUMBERS
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
    elements = []
    target_names = element_names(geopackage)
    query = QuerySplitByAttributes(element=source, fields=group_fields)
    with (geopackage.connection as cout,
          query.source.geopackage.connection as cin):
        cursor = cin.execute(query.group_count)
        group_count, = cursor.fetchone()
        for i in range(1, group_count + 1):
            cursor = cin.execute(query.select, (i,))
            name = make_unique_name(name=query.source.name, names=target_names)
            element = copy_element(
                source=source, where_clause=SQL_EMPTY,
                target=FeatureClass(geopackage=geopackage, name=name))
            elements.append(element)
            while records := cursor.fetchmany(FETCH_SIZE):
                cout.executemany(
                    query.insert.format(element.escaped_name), records)
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
    features are cut along the edges of the operator polygons.
    """
    query = QueryClip(source=source, target=target, operator=operator)
    if not query.has_intersection:
        return query.target_empty
    records = []
    polygon = query.config.geometry
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            geometries = [from_wkb(g.wkb) for g, *_ in features]
            intersects = polygon.intersects(geometries)
            if not intersects.any():
                continue
            keepers = [f for f, keep in zip(features, intersects) if keep]
            geoms = polygon.intersection(
                [g for g, keep in zip(geometries, intersects) if keep],
                grid_size=xy_tolerance)
            results = [(geom, attrs) for geom, (_, *attrs) in zip(geoms, keepers)]
            extend_records(results, records=records, config=query.config)
            cout.executemany(query.insert, records)
            records.clear()
    return query.target
# End clip function


@validate_result()
@validate_same_crs(SOURCE, OPERATOR)
@validate_xy_tolerance()
@validate_geopackage()
@validate_field(FIELD, data_types=TEXTS, single=True, element_name=OPERATOR)
@validate_feature_class(OPERATOR, geometry_types=GEOM_TYPE_POLYGONS)
@validate_feature_class(SOURCE)
def split(source: FeatureClass, operator: FeatureClass, field: Field | str,
          geopackage: GPKG, *, xy_tolerance: XY_TOL = None) -> list[FeatureClass]:
    """
    Split

    Extracts features for each polygon in the operator feature class and uses
    values from the specified field to name the output feature classes.
    """
    features = []
    query = QuerySplit(source, target=None, operator=operator)
    if not query.has_intersection:
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
