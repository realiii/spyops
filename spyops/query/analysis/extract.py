# -*- coding: utf-8 -*-
"""
Query Classes for analysis.extract module
"""


from functools import cached_property
from typing import Optional, TYPE_CHECKING, Union

from spyops.geometry.multi import build_multi
from spyops.query.base import (
    AbstractElementGroupQuery, AbstractFeatureClassGroupQuery,
    AbstractSpatialQuery, BaseQuerySelect)
from spyops.shared.constant import DRID, EMPTY
from spyops.shared.hint import FIELDS


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from shapely import MultiLineString, MultiPoint, MultiPolygon


class QuerySelect(BaseQuerySelect):
    """
    Query for Select
    """
# End QuerySelect class


# noinspection PyUnresolvedReferences
class SplitByAttributesMixin:
    """
    Split By Attributes Mixin
    """
    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self.source
        # noinspection PyArgumentList
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert('{}', insert_field_names, field_count)
    # End insert property

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        elm = self.source
        # noinspection PyArgumentList
        *_, select_field_names = self._field_names_and_count(elm)
        where_clause = self._build_spatial_rank(elm)
        return self._make_select(
            elm, field_names=select_field_names, where_clause=where_clause)
    # End select property

    @property
    def groups(self) -> str:
        """
        Groups
        """
        elm = self.source
        # NOTE this extent not used, simply filling a required argument
        index_where = self._spatial_index_where(elm, extent=(0, 0, 0, 0))
        return f"""
            SELECT DISTINCT * 
            FROM (SELECT dense_rank() OVER (
                    ORDER BY {self._group_names}) AS {DRID}, {self._group_names} 
            FROM {elm.escaped_name} {index_where})
        """
    # End groups property
# End SplitByAttributesMixin class


class QuerySplitByAttributesTable(SplitByAttributesMixin,
                                  AbstractElementGroupQuery):
    """
    Queries for Split by Attributes for Tables
    """
# End QuerySplitByAttributesTable class


class QuerySplitByAttributesFeatureClass(SplitByAttributesMixin,
                                         AbstractFeatureClassGroupQuery):
    """
    Queries for Split by Attributes for FeatureClasses
    """
    def __init__(self, element: 'FeatureClass', fields: FIELDS) -> None:
        """
        Initialize the QuerySplitByAttributesFeatureClass class
        """
        super().__init__(element, fields=fields, xy_tolerance=None)
    # End init built-in
# End QuerySplitByAttributesFeatureClass class


class QueryClip(AbstractSpatialQuery):
    """
    Queries for Clip
    """
    @cached_property
    def geometry(self) -> Optional[Union[
            'MultiPolygon', 'MultiLineString', 'MultiPoint']]:
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
