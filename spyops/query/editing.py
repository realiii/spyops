# -*- coding: utf-8 -*-
"""
Query Classes for editing
"""


from abc import ABCMeta, abstractmethod
from functools import cached_property
from typing import Callable, Optional, TYPE_CHECKING

from fudgeo import Field
from numpy import array
from shapely.predicates import is_empty
from shapely.set_operations import difference

from spyops.geometry.config import geometry_config
from spyops.geometry.multi import build_multi
from spyops.query.base import AbstractSourceUpdateQuery
from spyops.query.mixin import DropEmptyMixin, OperatorMixin
from spyops.shared.field import ORIG_FID
from spyops.shared.hint import FIELDS, NAMES


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from numpy import ndarray
    from shapely import MultiPolygon
    from spyops.geometry.config import GeometryConfig


class AbstractQueryEditing(AbstractSourceUpdateQuery, metaclass=ABCMeta):
    """
    Abstract Query for Editing
    """
    @cached_property
    def geometry_config(self) -> 'GeometryConfig':
        """
        Geometry Configuration
        """
        return geometry_config(self.source, cast_geom=False)
    # End geometry_config property

    @property
    @abstractmethod
    def _short_name(self) -> str:
        """
        Short Name
        """
        pass
    # End _short_name property

    def _prepare_source(self) -> None:
        """
        Source Preparation Steps
        """
        pass
    # End _prepare_source method

    @property
    def _intermediate_fields(self) -> FIELDS:
        """
        Intermediate Fields
        """
        geom = Field(self.source.geometry_column_name,
                     data_type=self.source.shape_type)
        return ORIG_FID, geom
    # End _intermediate_fields property

    def _get_field_names(self) -> NAMES:
        """
        Get Field Names
        """
        _, geom = self._intermediate_fields
        return [geom.escaped_name]
    # End _get_field_names method
# End AbstractQueryEditing class


class QueryGeneralize(AbstractQueryEditing):
    """
    Query for Generalize
    """
    @property
    def _short_name(self) -> str:
        """
        Short Name
        """
        return 'editing_generalize'
    # End _short_name property
# End QueryGeneralize class


class QueryDensify(AbstractQueryEditing):
    """
    Query for Densify
    """
    @property
    def _short_name(self) -> str:
        """
        Short Name
        """
        return 'editing_densify'
    # End _short_name property
# End QueryDensify class


class QueryFlip(AbstractQueryEditing):
    """
    Query for Flip
    """
    @property
    def _short_name(self) -> str:
        """
        Short Name
        """
        return 'editing_flip'
    # End _short_name property
# End QueryFlip class


class QueryErasePoint(OperatorMixin, AbstractQueryEditing, DropEmptyMixin):
    """
    Query for Erase Point
    """
    def __init__(self, source: 'FeatureClass', operator: 'FeatureClass',
                 remove_inside: bool, where_clause: str) -> None:
        """
        Initialize the QueryErasePoint class
        """
        super().__init__(source, where_clause=where_clause)
        self._operator: 'FeatureClass' = operator
        self._remove_inside: bool = remove_inside
    # End init built-in

    @property
    def _short_name(self) -> str:
        """
        Short Name
        """
        return 'editing_erase_point'
    # End _short_name property

    @cached_property
    def _operator_geometry(self) -> Optional['MultiPolygon']:
        """
        Multi-Part Geometry of the Operator Feature Class
        """
        # noinspection bad-return
        return build_multi(
            self.operator, select_sql=self.select_operator,
            transformer=self.operator_transformer)
    # End _operator_geometry property

    @property
    def eraser(self) -> Callable[['ndarray', list[int]], tuple[list, list]]:
        """
        Eraser Function
        """
        if self._remove_inside:
            return self._erase
        return self._clip
    # End eraser property

    def _clip(self, geometries: 'ndarray', ids: list[int]) -> tuple[list, list]:
        """
        Internal Clip
        """
        updates = []
        geometry = self._operator_geometry
        if not self.has_intersection or geometry is None:
            return updates, ids
        intersects = geometry.intersects(geometries)
        if not intersects.any():
            return updates, ids
        geoms = geometry.intersection(geometries[intersects])
        ids = array(ids, dtype=int)
        updates = [(g, (id_,)) for g, id_ in zip(geoms, ids[intersects])]
        return updates, ids[~intersects].tolist()
    # End _clip method

    def _erase(self, geometries: 'ndarray', ids: list[int]) -> tuple[list, list]:
        """
        Internal Difference
        """
        updates = []
        geometry = self._operator_geometry
        if not self.has_intersection or geometry is None:
            return updates, []
        intersects = geometry.intersects(geometries)
        if not intersects.any():
            return updates, []
        geoms = difference(geometries[intersects], geometry)
        empties = is_empty(geoms)
        ids = array(ids, dtype=int)[intersects]
        updates = [(g, (id_,)) for g, id_ in
                   zip(geoms[~empties], ids[~empties])]
        return updates, ids[empties].tolist()
    # End _erase method
# End QueryErasePoint class


if __name__ == '__main__':  # pragma: no cover
    pass
