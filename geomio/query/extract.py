# -*- coding: utf-8 -*-
"""
Query Classes for analysis.extract module
"""


from geomio.query.base import AbstractQuery, AbstractSpatialQuery
from geomio.shared.constant import EMPTY
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
        elm = self.source
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
    def groups(self) -> str:
        """
        Groups
        """
        elm = self.source
        return f"""
            SELECT DISTINCT * 
            FROM (SELECT dense_rank() OVER (
                    ORDER BY {self._group_names}) AS __DRID__, {self._group_names} 
            FROM {elm.escaped_name})
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
    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self.source
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            self.target.escaped_name, field_names=insert_field_names,
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
