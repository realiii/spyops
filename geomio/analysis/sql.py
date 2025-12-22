# -*- coding: utf-8 -*-
"""
SQL Utilities
"""


from fudgeo import FeatureClass
from fudgeo.constant import COMMA_SPACE
from shapely import box

from geomio.shared.constant import QUESTION, SQL_EMPTY, SQL_FULL
from geomio.shared.element import copy_feature_class
from geomio.shared.field import (
    get_geometry_column_name, make_field_names, validate_fields)
from geomio.shared.geometry import extent_from_feature_class
from geomio.shared.hint import ELEMENT
from geomio.shared.base import AnalysisComponents
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


def build_analysis(source: FeatureClass, target: FeatureClass,
                   operator: FeatureClass, use_empty: bool) -> AnalysisComponents:
    """
    Build the components needed for an Analysis
    """
    (field_count, insert_field_names,
     select_field_names) = _build_field_names_and_count(source)
    operator_extent = extent_from_feature_class(operator)
    source_extent = extent_from_feature_class(source)
    has_intersection = box(*operator_extent).intersects(box(*source_extent))
    wheres = where_intersect, where_disjoint = make_spatial_index_where(
        source=source, extent=operator_extent)
    if use_index := all(wheres):
        sql_intersect = _build_sql_select(
            source, field_names=select_field_names,
            where_clause=where_intersect)
        sql_disjoint = _build_sql_select(
            source, field_names=select_field_names,
            where_clause=where_disjoint)
    else:
        sql_intersect = _build_sql_select(
            source, field_names=select_field_names, where_clause=SQL_FULL)
        sql_disjoint = ''
    sql_insert = build_sql_insert(
        target.escaped_name, field_names=insert_field_names,
        field_count=field_count)
    if use_empty:
        sql = SQL_EMPTY
    else:
        sql = SQL_FULL
    target = copy_feature_class(source=source, target=target, where_clause=sql)
    return AnalysisComponents(
        use_index=use_index, has_intersection=has_intersection,
        sql_intersect=sql_intersect, sql_disjoint=sql_disjoint,
        sql_insert=sql_insert, target=target)
# End build_analysis function


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
