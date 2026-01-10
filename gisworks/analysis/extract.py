# -*- coding: utf-8 -*-
"""
Extraction
"""


from typing import Callable

from fudgeo import FeatureClass, Table, Field
from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany

from gisworks.geometry.util import filter_features, to_shapely
from gisworks.query.extract import QueryClip, QuerySplit, QuerySplitByAttributes
from gisworks.shared.constant import (
    FIELD, GROUP_FIELDS, OPERATOR, SOURCE, SQL_EMPTY, TARGET, UNDERSCORE)
from gisworks.shared.element import copy_element
from gisworks.shared.field import GEOM_TYPE_POLYGONS, TEXTS, TEXT_AND_NUMBERS
from gisworks.shared.hint import ELEMENT, FIELDS, FIELD_NAMES, GPKG, XY_TOL
from gisworks.environment import ANALYSIS_SETTINGS
from gisworks.shared.util import (
    element_names, extend_records, make_unique_name, make_valid_name)
from gisworks.shared.validation import (
    validate_element, validate_feature_class, validate_field,
    validate_geometry_dimension, validate_geopackage, validate_result,
    validate_same_crs, validate_table, validate_xy_tolerance)


__all__ = ['table_select', 'select', 'extract_rows', 'extract_features',
           'split_by_attributes', 'clip', 'split']


@validate_result()
@validate_table(SOURCE)
@validate_table(TARGET, exists=False)
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
@validate_feature_class(SOURCE)
@validate_feature_class(TARGET, exists=False)
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
@validate_element(SOURCE)
@validate_field(GROUP_FIELDS, data_types=TEXT_AND_NUMBERS,
                element_name=SOURCE, exclude_primary=False)
@validate_geopackage()
def split_by_attributes(source: ELEMENT, group_fields: FIELDS | FIELD_NAMES,
                        geopackage: GPKG) -> list[ELEMENT]:
    """
    Split by Attributes

    Split an input table or feature class by groups of attributes.
    """
    results = _split_by_attributes(
        source=source, group_fields=group_fields, geopackage=geopackage)
    return list(results.values())
# End split_by_attributes function


@validate_result()
@validate_feature_class(SOURCE)
@validate_feature_class(OPERATOR)
@validate_feature_class(TARGET, exists=False)
@validate_xy_tolerance()
@validate_geometry_dimension(SOURCE, OPERATOR)
@validate_same_crs(SOURCE, OPERATOR)
def clip(source: FeatureClass, operator: FeatureClass, target: FeatureClass, *,
         xy_tolerance: XY_TOL = None) -> FeatureClass:
    """
    Clip

    Extracts features using the features of a polygon feature class. Extracted
    features are cut along the edges of the operator polygons.
    """
    return _clip(source=source, operator=operator, target=target,
                 xy_tolerance=xy_tolerance)
# End clip function


@validate_result()
@validate_feature_class(SOURCE)
@validate_feature_class(OPERATOR, geometry_types=GEOM_TYPE_POLYGONS)
@validate_field(FIELD, data_types=TEXTS, single=True, element_name=OPERATOR)
@validate_geopackage()
@validate_xy_tolerance()
@validate_same_crs(SOURCE, OPERATOR)
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
    splitters = _split_by_attributes(
        source=operator, group_fields=[field],
        geopackage=ANALYSIS_SETTINGS.scratch_workspace)
    for (value,), s in splitters.items():
        name = make_valid_name(
            f'{source.name}{UNDERSCORE}{value}', prefix='split')
        target = _clip(
            source=source, operator=s, xy_tolerance=xy_tolerance,
            target=FeatureClass(geopackage=geopackage, name=name))
        features.append(target)
    return features
# End split function


# Aliases
extract_rows: Callable[[Table, Table, str, bool], Table] = table_select
extract_features: Callable[[FeatureClass, FeatureClass, str, bool], FeatureClass] = select


def _clip(*, source: FeatureClass, operator: FeatureClass,
          target: FeatureClass, xy_tolerance: XY_TOL) -> FeatureClass:
    """
    Internal Clip
    """
    query = QueryClip(source=source, target=target, operator=operator)
    if not query.has_intersection:
        return query.target_empty
    records = []
    insert_sql = query.insert
    geometry = query.geometry
    config = query.geometry_config
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            geometries = to_shapely(features)
            intersects = geometry.intersects(geometries)
            if not intersects.any():
                continue
            keepers = [f for f, keep in zip(features, intersects) if keep]
            geoms = geometry.intersection(
                [g for g, keep in zip(geometries, intersects) if keep],
                grid_size=xy_tolerance)
            results = [(g, attrs) for g, (_, *attrs) in zip(geoms, keepers)]
            extend_records(results, records=records, config=config)
            executor(sql=insert_sql, data=records)
            records.clear()
    return query.target
# End _clip function


def _split_by_attributes(*, source: ELEMENT, group_fields: FIELDS | FIELD_NAMES,
                         geopackage: GPKG) -> dict[tuple, ELEMENT]:
    """
    Internal Split by Attributes
    """
    elements = {}
    target_names = element_names(geopackage)
    query = QuerySplitByAttributes(element=source, fields=group_fields)
    query_select = query.select
    query_insert = query.insert
    source_name = query.source.name
    with (geopackage.connection as cout,
          query.source.geopackage.connection as cin,):
        cursor = cin.execute(query.groups)
        groups = cursor.fetchall()
        for i, *group in groups:
            name = UNDERSCORE.join([str(g).strip() for g in group])
            name = make_valid_name(name, prefix=source_name)
            name = make_unique_name(name, names=target_names)
            element = copy_element(
                source=source, where_clause=SQL_EMPTY,
                target=FeatureClass(geopackage=geopackage, name=name))
            elements[tuple(group)] = element
            cursor = cin.execute(query_select, (i,))
            with ExecuteMany(connection=cout, table=element) as executor:
                insert_sql = query_insert.format(element.escaped_name)
                while records := cursor.fetchmany(FETCH_SIZE):
                    executor(sql=insert_sql, data=records)
    return elements
# End _split_by_attributes function


if __name__ == '__main__':  # pragma: no cover
    pass
