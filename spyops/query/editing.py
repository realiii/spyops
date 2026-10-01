# -*- coding: utf-8 -*-
"""
Query Classes for editing
"""


from abc import ABCMeta, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING

from fudgeo import Field

from spyops.geometry.config import geometry_config
from spyops.query.base import AbstractSourceUpdateQuery
from spyops.query.mixin import DropEmptyMixin, OperatorMixin
from spyops.shared.field import ORIG_FID
from spyops.shared.hint import FIELDS, NAMES


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
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


class QueryErasePoint(OperatorMixin, AbstractSourceUpdateQuery, DropEmptyMixin):
    """
    Query for Erase Point
    """
    def __init__(self, source: 'FeatureClass', operator: 'FeatureClass',
                 where_clause: str) -> None:
        """
        Initialize the QueryErasePoint class
        """
        super().__init__(source, target=source, where_clause=where_clause)
        self._operator: 'FeatureClass' = operator
    # End init built-in

    @property
    def _short_name(self) -> str:
        """
        Short Name
        """
        return 'editing_erase_point'
    # End _short_name property
# End QueryErasePoint class


if __name__ == '__main__':  # pragma: no cover
    pass
