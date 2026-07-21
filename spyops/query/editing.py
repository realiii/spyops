# -*- coding: utf-8 -*-
"""
Query Classes for editing
"""


from functools import cached_property
from typing import TYPE_CHECKING

from fudgeo import Field

from spyops.geometry.config import geometry_config
from spyops.query.base import AbstractSourceUpdateQuery
from spyops.shared.field import ORIG_FID
from spyops.shared.hint import FIELDS, NAMES


if TYPE_CHECKING:  # pragma: no cover
    from spyops.geometry.config import GeometryConfig


class QueryGeneralize(AbstractSourceUpdateQuery):
    """
    Query for Generalize
    """
    @cached_property
    def geometry_config(self) -> 'GeometryConfig':
        """
        Geometry Configuration
        """
        return geometry_config(self.source, cast_geom=False)
    # End geometry_config property

    @property
    def _short_name(self) -> str:
        """
        Short Name
        """
        return 'editing_generalize'
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

    @property
    def update(self) -> str:
        """
        Update Query
        """
        field_names = self._get_field_names()
        key_name, *from_field_names = [
            f.escaped_name for f in self._intermediate_fields]
        # noinspection PyUnresolvedReferences
        target_key_name = self.target.primary_key_field.escaped_name
        return self._make_update_from(
            element_name=self.target.escaped_name, key_name=target_key_name,
            field_names=field_names, from_name=self._intermediate_table,
            from_key_name=key_name, from_field_names=from_field_names)
    # End update property
# End QueryGeneralize class


if __name__ == '__main__':  # pragma: no cover
    pass
