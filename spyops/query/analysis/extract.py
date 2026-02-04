# -*- coding: utf-8 -*-
"""
Query Classes for analysis.extract module
"""


from functools import cached_property
from typing import TYPE_CHECKING, Union

from fudgeo import FeatureClass

from spyops.crs.util import crs_from_srs
from spyops.environment import ANALYSIS_SETTINGS
from spyops.geometry.multi import build_multi
from spyops.query.base import (
    AbstractQuery, AbstractSourceQuery, AbstractSpatialQuery)
from spyops.shared.constant import EMPTY, IN, SQL_FULL
from spyops.shared.field import make_field_names
from spyops.shared.hint import ELEMENT, EXTENT, FIELDS


if TYPE_CHECKING:  # pragma: no cover
    from shapely import MultiLineString, MultiPoint, MultiPolygon


class QuerySelect(AbstractSourceQuery):
    """
    Query for Select
    """
    def __init__(self, source: FeatureClass, target: FeatureClass,
                 where_clause: str = EMPTY) -> None:
        """
        Initialize the AbstractSourceQuery class
        """
        super().__init__(source, target=target, xy_tolerance=None)
        self._where_clause: str = where_clause
    # End init built-in

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        elm = self.source
        *_, select_field_names = self._field_names_and_count(elm)
        where_clause = (self._where_clause or EMPTY).strip() or SQL_FULL
        if ANALYSIS_SETTINGS.extent:
            return self._make_intersection_query(
                elm, field_names=select_field_names, where_clause=where_clause)
        return self._make_select(
            elm, field_names=select_field_names, where_clause=where_clause)
    # End select property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self.target
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property
# End QuerySelect class


class QuerySplitByAttributes(AbstractQuery):
    """
    Queries for Split by Attributes
    """
    def __init__(self, element: ELEMENT, fields: FIELDS) -> None:
        """
        Initialize the QuerySplitByAttributes class
        """
        super().__init__(element, xy_tolerance=None)
        self._group_names: str = make_field_names(fields)
    # End init built-in

    def _spatial_index_where(self, element: ELEMENT, extent: EXTENT) -> str:
        """
        Make a where clause stub that can be used to select features which
        intersect an extent. The query is based on a spatial index (if present).
        """
        if not isinstance(element, FeatureClass):
            return EMPTY
        if not (extent := ANALYSIS_SETTINGS.extent):
            return EMPTY
        polygon = self._get_extent_polygon(
            extent, crs=crs_from_srs(element.spatial_reference_system))
        if index_where := super()._spatial_index_where(
                element, extent=polygon.bounds):
            index_where = f'WHERE ({index_where.format(IN)})'
        return index_where
    # End _spatial_index_where function

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        elm = self.source
        *_, select_field_names = self._field_names_and_count(elm)
        index_where = self._spatial_index_where(elm, extent=(0, 0, 0, 0))
        primary = elm.primary_key_field.escaped_name
        where_clause = f"""
            {primary} IN (SELECT {primary}
            FROM (SELECT {primary}, 
                         dense_rank() OVER (ORDER BY {self._group_names}) AS __DRID__ 
                  FROM {elm.escaped_name} {index_where})
            WHERE __DRID__ = ?) 
        """
        return self._make_select(
            elm, field_names=select_field_names, where_clause=where_clause)
    # End select property

    @property
    def groups(self) -> str:
        """
        Groups
        """
        elm = self.source
        index_where = self._spatial_index_where(elm, extent=(0, 0, 0, 0))
        return f"""
            SELECT DISTINCT * 
            FROM (SELECT dense_rank() OVER (
                    ORDER BY {self._group_names}) AS __DRID__, {self._group_names} 
            FROM {elm.escaped_name} {index_where})
        """
    # End groups property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self.source
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert('{}', insert_field_names, field_count)
    # End insert property
# End QuerySplitByAttributes class


class QueryClip(AbstractSpatialQuery):
    """
    Queries for Clip
    """
    @cached_property
    def geometry(self) -> Union['MultiPolygon', 'MultiLineString', 'MultiPoint']:
        """
        Multi-Part Geometry of the Operator Feature Class
        """
        return build_multi(
            self.operator, select_sql=self.select_operator,
            transformer=self.operator_transformer)
    # End geometry property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self.target
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property
# End QueryClip class


class QuerySplit(AbstractSpatialQuery):
    """
    Queries for Split, really just here for the has_intersection
    """
    @property
    def insert(self) -> str:  # pragma: no cover
        """
        Insert Query, not used
        """
        return EMPTY
    # End insert property
# End QuerySplit class


if __name__ == '__main__':  # pragma: no cover
    pass
