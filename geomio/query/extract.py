# -*- coding: utf-8 -*-
"""
Query Classes for analysis.extract module
"""


from geomio.query.base import AbstractQuery, AbstractSpatialQuery
from geomio.shared.constant import IN, NOT_IN, SQL_FULL
from geomio.shared.field import make_field_names
from geomio.shared.hint import ELEMENT, FIELDS


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
        elm = self._element
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            self._target.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property
# End QueryClip class


if __name__ == '__main__':  # pragma: no cover
    pass
