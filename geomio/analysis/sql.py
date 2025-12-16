# -*- coding: utf-8 -*-
"""
SQL Utilities
"""


from fudgeo import FeatureClass
from fudgeo.constant import COMMA_SPACE
from shapely import box

from geomio.shared.constant import QUESTION, SQL_FULL
from geomio.shared.geometry import extent_from_feature_class
from geomio.shared.field import (
    get_geometry_column_name, make_field_names, validate_fields)
from geomio.shared.hint import ELEMENT
from geomio.shared.base import QueryComponents
from geomio.shared.util import make_spatial_index_where


def build_sql_insert(element_name: str, field_names: str,
                     field_count: int) -> str:
    """
    Build SQL statement for Insert
    """
    return f"""
        INSERT INTO {element_name}({field_names}) 
        VALUES ({COMMA_SPACE.join(QUESTION * field_count)})
    """
# End build_sql_insert function


def build_sql_select_by_attributes(source: ELEMENT,
                                   group_names: str) -> tuple[str, str, str]:
    """
    Build SQL statements for Select by Attributes
    """
    (field_count, insert_field_names,
     select_field_names) = _build_field_names_and_count(source)
    group_count_sql = f"""
        SELECT COUNT(C) AS C 
        FROM (SELECT COUNT(1) AS C 
              FROM {source.escaped_name} 
              GROUP BY {group_names}
        )
    """
    ids_sql = f"""
        SELECT {source.primary_key_field.escaped_name}
        FROM (SELECT {source.primary_key_field.escaped_name}, 
                     dense_rank() OVER (ORDER BY {group_names}) AS __DRID__ 
                     FROM {source.escaped_name})
        WHERE __DRID__ = ?
    """
    select_sql = f"""
        SELECT {select_field_names}
        FROM {source.escaped_name}
        WHERE {source.primary_key_field.escaped_name} IN ({ids_sql}) 
    """
    insert_sql = build_sql_insert(
        '{}', field_names=insert_field_names, field_count=field_count)
    return group_count_sql, insert_sql, select_sql
# End build_sql_select_by_attributes function


def _build_field_names_and_count(source: ELEMENT) -> tuple[int, str, str]:
    """
    Build Field Names and Derive Field Count
    """
    source_fields = validate_fields(source, fields=source.fields)
    select_field_names = insert_field_names = make_field_names(source_fields)
    field_count = len(source_fields)
    if isinstance(source, FeatureClass):
        geom = get_geometry_column_name(source)
        geom_type = get_geometry_column_name(source, include_geom_type=True)
        select_field_names = f'{geom_type}{COMMA_SPACE}{select_field_names}'
        insert_field_names = f'{geom}{COMMA_SPACE}{insert_field_names}'
        field_count += 1
    return field_count, insert_field_names, select_field_names
# End _build_field_names_and_count function


def build_query_components(source: FeatureClass, target: FeatureClass,
                           operator: FeatureClass) -> QueryComponents:
    """
    Build Query Components
    """
    (field_count, insert_field_names,
     select_field_names) = _build_field_names_and_count(source)
    operator_extent = extent_from_feature_class(operator)
    source_extent = extent_from_feature_class(source)
    has_intersection = box(*operator_extent).intersects(box(*source_extent))
    wheres = where_touches, where_outside = make_spatial_index_where(
        source=source, extent=operator_extent)
    if use_index := all(wheres):
        sql_touches = _build_sql_select(
            source, field_names=select_field_names, where_clause=where_touches)
        sql_outside = _build_sql_select(
            source, field_names=select_field_names, where_clause=where_outside)
    else:
        sql_touches = _build_sql_select(
            source, field_names=select_field_names, where_clause=SQL_FULL)
        sql_outside = ''
    sql_insert = build_sql_insert(
        target.escaped_name, field_names=insert_field_names,
        field_count=field_count)
    return QueryComponents(
        use_index=use_index, has_intersection=has_intersection,
        sql_touches=sql_touches, sql_outside=sql_outside, sql_insert=sql_insert)
# End build_query_components function


def _build_sql_select(element: ELEMENT, field_names: str,
                      where_clause: str) -> str:
    """
    Build SQL statement for Select
    """
    return f"""
        SELECT {field_names}
        FROM {element.escaped_name} 
        WHERE {where_clause}
    """
# End _build_sql_select function


if __name__ == '__main__':  # pragma: no cover
    pass
