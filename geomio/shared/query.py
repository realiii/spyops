# -*- coding: utf-8 -*-
"""
SQL Utilities
"""


from abc import ABCMeta, abstractmethod
from functools import cache, cached_property

from fudgeo import FeatureClass
from fudgeo.constant import COMMA_SPACE
from shapely import box

from geomio.shared.base import OverlayConfig
from geomio.shared.constant import QUESTION, SQL_EMPTY, SQL_FULL
from geomio.shared.element import copy_feature_class
from geomio.shared.field import (
    get_geometry_column_name, make_field_names, validate_fields)
from geomio.shared.geometry import extent_from_feature_class, overlay_config
from geomio.shared.hint import ELEMENT, EXTENT, FIELDS


class AbstractQuery(metaclass=ABCMeta):
    """
    Base Query Support
    """
    def __init__(self, element: ELEMENT) -> None:
        """
        Initialize the AbstractQuery class
        """
        super().__init__()
        self._element: ELEMENT = element
    # End init built-in

    @staticmethod
    def _make_select(element: ELEMENT, field_names: str,
                     where_clause: str) -> str:
        """
        Make SQL statement for Select
        """
        return f"""
            SELECT {field_names}
            FROM {element.escaped_name} 
            WHERE {where_clause}
        """
    # End _make_select function

    @staticmethod
    def _make_insert(element_name: str, field_names: str, field_count: int) -> str:
        """
        Make SQL statement for Insert
        """
        return f"""
            INSERT INTO {element_name}({field_names}) 
            VALUES ({COMMA_SPACE.join(QUESTION * field_count)})
        """
    # End _make_insert function

    @cache
    def _field_names_and_count(self, element: ELEMENT) -> tuple[int, str, str]:
        """
        Field Names for Select and Insert + Derive Field Count
        """
        fields = validate_fields(element, fields=element.fields)
        select_field_names = insert_field_names = make_field_names(fields)
        field_count = len(fields)
        if isinstance(element, FeatureClass):
            geom = get_geometry_column_name(element)
            geom_type = get_geometry_column_name(
                element, include_geom_type=True)
            select_field_names = f'{geom_type}{COMMA_SPACE}{select_field_names}'
            insert_field_names = f'{geom}{COMMA_SPACE}{insert_field_names}'
            field_count += 1
        return field_count, insert_field_names, select_field_names
    # End _field_names_and_count property

    @property
    def source(self) -> ELEMENT:
        """
        Source
        """
        return self._element
    # End source property

    @property
    @abstractmethod
    def select(self) -> str:  # pragma: no cover
        """
        Selection Query
        """
        pass
    # End select property

    @property
    @abstractmethod
    def insert(self) -> str:  # pragma: no cover
        """
        Insert Query
        """
        pass
    # End insert property
# End AbstractQuery class


class AbstractSpatialQuery(AbstractQuery):
    """
    Abstract Spatial Query Support
    """
    def __init__(self, source: FeatureClass, target: FeatureClass,
                 operator: FeatureClass) -> None:
        """
        Initialize the QueryClip class
        """
        super().__init__(source)
        self._target: FeatureClass = target
        self._operator: FeatureClass = operator
    # End init built-in

    @cached_property
    def config(self) -> OverlayConfig:
        """
        Overlay Configuration
        """
        return overlay_config(
            self.source, target=self.target, operator=self._operator)
    # End config property

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        return self.select_intersect
    # End select property

    @cached_property
    def operator_extent(self) -> EXTENT:
        """
        Operator Extent
        """
        return extent_from_feature_class(self._operator)
    # End operator_extent property

    @cached_property
    def source_extent(self) -> EXTENT:
        """
        Source Extent
        """
        return extent_from_feature_class(self._element)
    # End source_extent property

    @cached_property
    def shared_extent(self) -> EXTENT:
        """
        Shared Extent between source and operator
        """
        shared = box(*self.operator_extent).intersection(
            box(*self.source_extent))
        return shared.bounds
    # End shared_extent property

    @cached_property
    def has_intersection(self) -> bool:
        """
        Has Intersection between source and operator
        """
        return box(*self.operator_extent).intersects(box(*self.source_extent))
    # End has_intersection property

    @staticmethod
    def _spatial_index_where(element: FeatureClass, extent: EXTENT) -> str:
        """
        Make a where clause stub that can be used to select features which
        intersect an extent. The query is based on a spatial index (if present).
        """
        primary = element.primary_key_field
        if not element.has_spatial_index or not primary:
            return ''
        min_x, min_y, max_x, max_y = extent
        return f"""{primary.escaped_name} {{}} (
            SELECT id  
            FROM {element.spatial_index_name} 
            WHERE minx <= {max_x} AND maxx >= {min_x} AND 
                  miny <= {max_y} AND maxy >= {min_y})
        """
    # End _spatial_index_wheres function

    @property
    def source(self) -> FeatureClass:
        """
        Source
        """
        return self._element
    # End source property

    @property
    def operator(self) -> FeatureClass:
        """
        Operator
        """
        return self._operator
    # End operator property

    @property
    def target(self) -> FeatureClass:
        """
        Alias for Target Empty
        """
        return self.target_empty
    # End target property

    @cached_property
    def target_empty(self) -> FeatureClass:
        """
        Only the Structure of the Source copied to the Target Feature Class
        """
        return copy_feature_class(
            self._element, target=self._target, where_clause=SQL_EMPTY)
    # End target_empty property

    @cached_property
    def target_full(self) -> FeatureClass:
        """
        Full Copy of the Source Feature Class
        """
        return copy_feature_class(
            self._element, target=self._target, where_clause=SQL_FULL)
    # End target_full property

    @property
    @abstractmethod
    def select_intersect(self) -> str:  # pragma: no cover
        """
        Selection query for intersection
        """
        pass
    # End select_intersect property

    @property
    @abstractmethod
    def select_disjoint(self) -> str:  # pragma: no cover
        """
        Selection query for disjoint
        """
        pass
    # End select_disjoint property
# End AbstractSpatialQuery class


class QuerySplitByAttributes(AbstractQuery):
    """
    Queries for Split by Attributes
    """
    def __init__(self, element: ELEMENT, fields: FIELDS) -> None:
        """
        Initialize the QuerySplitByAttributes class
        """
        super().__init__(element)
        self._group_names: str = make_field_names(fields)
    # End init built-in

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        elm = self._element
        *_, select_field_names = self._field_names_and_count(elm)
        primary = elm.primary_key_field.escaped_name
        sub = f"""
            SELECT {primary}
            FROM (SELECT {primary}, 
                         dense_rank() OVER (ORDER BY {self._group_names}) AS __DRID__ 
                         FROM {elm.escaped_name})
            WHERE __DRID__ = ?
        """
        return self._make_select(
            elm, field_names=select_field_names,
            where_clause=f'{primary} IN ({sub})')
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
        elm = self._element
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert('{}', insert_field_names, field_count)
    # End insert property
# End QuerySplitByAttributes class


class QueryClip(AbstractSpatialQuery):
    """
    Queries for Clip
    """
    @property
    def select_intersect(self) -> str:
        """
        Selection query for intersection
        """
        elm = self._element
        if where := self._spatial_index_where(
                elm, extent=self.shared_extent):
            where = where.format('IN')
        else:
            where = SQL_FULL
        *_, select_field_names = self._field_names_and_count(elm)
        return self._make_select(
            elm, field_names=select_field_names, where_clause=where)
    # End select_intersect property

    @property
    def select_disjoint(self) -> str:
        """
        Selection query for disjoint
        """
        elm = self._element
        if not (where := self._spatial_index_where(
                elm, extent=self.shared_extent)):
            return ''
        *_, select_field_names = self._field_names_and_count(elm)
        return self._make_select(
            elm, field_names=select_field_names,
            where_clause=where.format('NOT IN'))
    # End select_disjoint property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self._element
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            self._target.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property
# End QueryClip class


class QueryErase(QueryClip):
    """
    Queries for Erase
    """
# End QueryErase class


class QueryIntersect(AbstractSpatialQuery):
    """
    Queries for Intersect
    """
    @property
    def select(self) -> str:
        """
        Selection Query
        """
        return self.select_intersect
    # End select property

    @property
    def select_operator(self) -> str:
        """
        Selection Query for Operator
        """
        elm = self._operator
        if where := self._spatial_index_where(elm, extent=self.shared_extent):
            where = where.format('IN')
        else:
            where = SQL_FULL
        *_, select_field_names = self._field_names_and_count(elm)
        return self._make_select(elm, select_field_names, where_clause=where)
    # End select_operator property

    @property
    def select_intersect(self) -> str:
        """
        Selection query for intersection
        """
        elm = self._element
        if where := self._spatial_index_where(elm, extent=self.shared_extent):
            where = where.format('IN')
        else:
            where = SQL_FULL
        *_, select_field_names = self._field_names_and_count(elm)
        return self._make_select(
            elm, field_names=select_field_names, where_clause=where)
    # End select_intersect property

    @property
    def select_disjoint(self) -> str:
        """
        Selection query for disjoint
        """
        elm = self._element
        if not (where := self._spatial_index_where(
                elm, extent=self.shared_extent)):
            return ''
        *_, select_field_names = self._field_names_and_count(elm)
        return self._make_select(
            elm, field_names=select_field_names,
            where_clause=where.format('NOT IN'))
    # End select_disjoint property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self._element
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            self._target.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property
# End QueryIntersect class


if __name__ == '__main__':  # pragma: no cover
    pass
