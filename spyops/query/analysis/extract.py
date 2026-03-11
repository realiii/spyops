# -*- coding: utf-8 -*-
"""
Query Classes for analysis.extract module
"""


from functools import cached_property
from typing import TYPE_CHECKING, Union

from spyops.geometry.multi import build_multi
from spyops.query.base import (
    AbstractGroupQuery, AbstractSpatialQuery, BaseQuerySelect)
from spyops.shared.constant import EMPTY
from spyops.shared.hint import ELEMENT, FIELDS


if TYPE_CHECKING:  # pragma: no cover
    from shapely import MultiLineString, MultiPoint, MultiPolygon


class QuerySelect(BaseQuerySelect):
    """
    Query for Select
    """
# End QuerySelect class


class QuerySplitByAttributes(AbstractGroupQuery):
    """
    Queries for Split by Attributes
    """
    def __init__(self, element: ELEMENT, fields: FIELDS) -> None:
        """
        Initialize the QuerySplitByAttributes class
        """
        super().__init__(element, fields=fields, xy_tolerance=None)
    # End init built-in

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
