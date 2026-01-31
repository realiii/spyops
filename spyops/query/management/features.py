# -*- coding: utf-8 -*-
"""
Query Classes for management.features module
"""


from functools import cached_property
from operator import attrgetter
from typing import Callable

from fudgeo.enumeration import ShapeType

from spyops.crs.transform import make_transformer_function
from spyops.query.base import AbstractSourceQuery
from spyops.shared.constant import (
    LINES_ATTR, POINTS_ATTR, POLYGONS_ATTR, SQL_FULL)
from spyops.shared.field import (
    ORIG_FID, get_geometry_column_name, make_field_names, make_unique_fields,
    validate_fields)
from spyops.shared.hint import FIELDS


class QueryMultiPartToSinglePart(AbstractSourceQuery):
    """
    Queries for MultiPart to SinglePart
    """
    @property
    def part_getter(self) -> attrgetter:
        """
        Part Getter
        """
        shape_type = self.source.shape_type
        if shape_type == ShapeType.multi_point:
            name = POINTS_ATTR
        elif shape_type == ShapeType.multi_linestring:
            name = LINES_ATTR
        else:
            name = POLYGONS_ATTR
        return attrgetter(name)
    # End part_getter property

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type reducing from multi to single
        """
        shape_type = self.source.shape_type
        if shape_type == ShapeType.multi_point:
            return ShapeType.point
        elif shape_type == ShapeType.multi_linestring:
            return ShapeType.linestring
        return ShapeType.polygon
    # End _get_target_shape_type method

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields and Rename Primary Key Columns if included
        """
        key = ORIG_FID.name.casefold()
        fields = validate_fields(self.source, fields=self.source.fields)
        names = [f.name.casefold() for f in fields]
        if key not in names:
            return ORIG_FID, *fields
        index = names.index(key)
        field, = make_unique_fields([ORIG_FID, *fields], others=[fields[index]])
        fields[index] = field
        return ORIG_FID, *fields
    # End _get_unique_fields method

    @property
    def select(self) -> str:
        """
        Select from Source including FID
        """
        fields = validate_fields(self.source, fields=self.source.fields)
        fields = [self.source.primary_key_field, *fields]
        select_names = make_field_names(fields)
        geom_type = get_geometry_column_name(
            self.source, include_geom_type=True)
        select_names = self._concatenate(geom_type, select_names)
        return self._make_select(
            self.source, field_names=select_names, where_clause=SQL_FULL)
    # End select property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        fields = self._get_unique_fields()
        insert_names = make_field_names(fields)
        geom = get_geometry_column_name(self.target)
        insert_names = self._concatenate(geom, insert_names)
        return self._make_insert(
            self.target.escaped_name, field_names=insert_names,
            field_count=len(fields) + 1)
    # End insert property

    @cached_property
    def source_transformer(self) -> Callable | None:
        """
        Transformer
        """
        elm = self.source
        transformer = self._get_transformer(elm)
        return make_transformer_function(
            self._get_target_shape_type(), has_z=elm.has_z, has_m=elm.has_m,
            transformer=transformer)
    # End source_transformer property
# End QueryMultiPartToSinglePart class


if __name__ == '__main__':  # pragma: no cover
    pass
