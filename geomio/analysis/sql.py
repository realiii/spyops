# -*- coding: utf-8 -*-
"""
SQL Utilities
"""


from functools import cached_property

from fudgeo import FeatureClass
from fudgeo.constant import COMMA_SPACE
from shapely import box

from geomio.shared.constant import QUESTION, SQL_EMPTY, SQL_FULL
from geomio.shared.element import copy_feature_class
from geomio.shared.field import (
    get_geometry_column_name, make_field_names, validate_fields)
from geomio.shared.geometry import extent_from_feature_class
from geomio.shared.hint import ELEMENT, FIELDS
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


class QuerySplitByAttributes:
    """
    Queries for Split by Attributes
    """
    def __init__(self, element: ELEMENT, fields: FIELDS) -> None:
        """
        Initialize the QuerySplitByAttributes class
        """
        super().__init__()
        self._element: ELEMENT = element
        self._fields: FIELDS = fields
        self._group_names: str = make_field_names(fields)
    # End init built-in

    @cached_property
    def _field_names_and_count(self) -> tuple[int, str, str]:
        """
        Field Names for Select and Insert + Derive Field Count
        """
        fields = validate_fields(self._element, fields=self._element.fields)
        select_field_names = insert_field_names = make_field_names(fields)
        field_count = len(fields)
        if isinstance(self._element, FeatureClass):
            geom = get_geometry_column_name(self._element)
            geom_type = get_geometry_column_name(
                self._element, include_geom_type=True)
            select_field_names = f'{geom_type}{COMMA_SPACE}{select_field_names}'
            insert_field_names = f'{geom}{COMMA_SPACE}{insert_field_names}'
            field_count += 1
        return field_count, insert_field_names, select_field_names
    # End _field_names_and_count property

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        *_, select_field_names = self._field_names_and_count
        primary = self._element.primary_key_field.escaped_name
        sub = f"""
            SELECT {primary}
            FROM (SELECT {primary}, 
                         dense_rank() OVER (ORDER BY {self._group_names}) AS __DRID__ 
                         FROM {self._element.escaped_name})
            WHERE __DRID__ = ?
        """
        return f"""
            SELECT {select_field_names}
            FROM {self._element.escaped_name}
            WHERE {primary} IN ({sub}) 
        """
    # End select property

    @property
    def group_count(self) -> str:
        """
        Group Count Query
        """
        return f"""
            SELECT COUNT(C) AS C 
            FROM (SELECT COUNT(1) AS C 
                  FROM {self._element.escaped_name} 
                  GROUP BY {self._group_names}
            )
        """
    # End group_count property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        field_count, insert_field_names, _ = self._field_names_and_count
        return build_sql_insert(
            '{}', field_names=insert_field_names, field_count=field_count)
    # End insert property
# End QuerySplitByAttributes class


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
