# -*- coding: utf-8 -*-
"""
Query Classes for management.general module
"""


from functools import cached_property
from typing import TYPE_CHECKING

from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.core import HasZM
from spyops.query.base import (
    AbstractElementGroupQuery, AbstractFeatureClassGroupQuery)
from spyops.shared.constant import DRID, EMPTY
from spyops.shared.field import (
    ORIG_FID, REPEAT_FID, get_geometry_column_name, make_field_names)
from spyops.shared.hint import FIELDS, GRID_SIZE, M_TOL, XY_TOL, Z_TOL


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, Table


class FindIdenticalMixin:
    """
    Find Identical Mixin
    """
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        return ORIG_FID, REPEAT_FID
    # End _get_unique_fields method

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        fields = self._get_unique_fields()
        insert_names = make_field_names(fields)
        return self._make_insert(
            self.target.escaped_name, field_names=insert_names,
            field_count=len(fields))
    # End insert property

    # noinspection PyUnresolvedReferences
    @property
    def repeats(self) -> str:
        """
        SQL for Groups with Repeats
        """
        elm = self.source
        index_where = self._spatial_index_where(elm)
        key = elm.primary_key_field.name
        return f"""
        SELECT {key}, {DRID}
        FROM (SELECT {key}, dense_rank() OVER (
                ORDER BY {self._group_names}) AS {DRID}
              FROM {elm.escaped_name} {index_where})
        WHERE {DRID} IN (
            SELECT {DRID} 
            FROM (SELECT {key}, dense_rank() OVER (
                ORDER BY {self._group_names}) AS {DRID}
            FROM {elm.escaped_name} {index_where}) 
            GROUP BY {DRID}
            HAVING COUNT({key}) > 1)
        """
    # End repeats property

    @property
    def target(self) -> 'Table':
        """
        Target
        """
        return self.target_empty
    # End target property

    @cached_property
    def target_empty(self) -> 'Table':
        """
        Target Empty
        """
        # noinspection PyUnresolvedReferences
        return self._target.geopackage.create_table(
            self._target.name, fields=self._get_unique_fields(),
            description='Results from Find Identical',
            overwrite=ANALYSIS_SETTINGS.overwrite)
    # End target_empty property
# End FindIdenticalMixin class


class QueryFindIdenticalTable(FindIdenticalMixin, AbstractElementGroupQuery):
    """
    Query Find Identical for Table
    """
    def __init__(self, element: 'Table', target: 'Table', fields: FIELDS,
                 **kwargs) -> None:
        """
        Initialize the QueryFindIdenticalTable class
        """
        super().__init__(element, fields=fields)
        self._target: 'Table' = target
    # End init built-in

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        return EMPTY
    # End select property

    @property
    def has_zm(self) -> HasZM:
        """
        Has ZM
        """
        return HasZM(has_z=False, has_m=False)
    # End has_zm property
# End QueryFindIdenticalTable class


class QueryFindIdenticalFeatureClass(FindIdenticalMixin,
                                     AbstractFeatureClassGroupQuery):
    """
    Query Find Identical for Feature Class
    """
    def __init__(self, element: 'FeatureClass', target: 'Table', fields: FIELDS,
                 *, include_geometry: bool, xy_tolerance: XY_TOL,
                 z_tolerance: Z_TOL, m_tolerance: M_TOL) -> None:
        """
        Initialize the QueryFindIdenticalFeatureClass class
        """
        super().__init__(element, fields=fields, xy_tolerance=xy_tolerance)
        self._target: 'Table' = target
        self._include_geometry: bool = include_geometry
        self._z_tolerance: Z_TOL = z_tolerance
        self._m_tolerance: M_TOL = m_tolerance
    # End init built-in

    @cached_property
    def grid_size(self) -> GRID_SIZE:
        """
        Grid Size Overload, use xy tolerance as-is
        """
        return self._xy_tolerance
    # End grid_size property

    @property
    def has_zm(self) -> HasZM:
        """
        Has ZM
        """
        return HasZM(has_z=self.source.has_z, has_m=self.source.has_m)
    # End has_zm property

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        if not self._include_geometry:
            return EMPTY
        elm = self.source
        geom_type = get_geometry_column_name(elm, include_geom_type=True)
        # noinspection PyUnresolvedReferences
        select_names = self._concatenate(geom_type, elm.primary_key_field.name)
        where_clause = self._build_spatial_rank(elm)
        return self._make_select(
            elm, field_names=select_names, where_clause=where_clause)
    # End select property
# End QueryFindIdenticalFeatureClass class


if __name__ == '__main__':  # pragma: no cover
    pass
