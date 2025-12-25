# -*- coding: utf-8 -*-
"""
Query Classes for analysis.overlay module
"""

from geomio.query.base import AbstractSpatialAttribute
from geomio.query.extract import QueryClip

from geomio.shared.constant import IN, NOT_IN, SQL_FULL


class QueryErase(QueryClip):
    """
    Queries for Erase
    """
# End QueryErase class


class QueryIntersect(AbstractSpatialAttribute):
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
            where = where.format(IN)
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
            where = where.format(IN)
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
            where_clause=where.format(NOT_IN))
    # End select_disjoint property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        # TODO fix this
        elm = self._element
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            self._target.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property
# End QueryIntersect class


if __name__ == '__main__':  # pragma: no cover
    pass
