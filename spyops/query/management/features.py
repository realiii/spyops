# -*- coding: utf-8 -*-
"""
Query Classes for management.features module
"""


from datetime import datetime
from functools import cached_property, partial
from operator import attrgetter
from typing import Callable, Self, TYPE_CHECKING

from fudgeo.constant import COMMA_SPACE
from fudgeo.enumeration import ShapeType
from fudgeo.util import escape_name

from spyops.crs.transform import make_transformer_function
from spyops.environment import ANALYSIS_SETTINGS
from spyops.geometry.centroid import GEOMETRY_CENTROID
from spyops.query.base import AbstractSourceQuery, BaseQuerySelect
from spyops.shared.constant import (
    DOT, LINES_ATTR, POINTS_ATTR, POLYGONS_ATTR, SQL_FULL, TEMP_SCHEMA)
from spyops.shared.enumeration import WeightOption
from spyops.shared.field import (
    ORIG_FID, POINT_M, POINT_X, POINT_Y, POINT_Z, get_geometry_column_name,
    make_field_names, make_unique_fields, validate_fields)
from spyops.shared.hint import FIELDS, NAMES


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


class QueryMultiPartToSinglePart(AbstractSourceQuery):
    """
    Queries for MultiPart to SinglePart
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass') -> None:
        """
        Initialize the QueryMultiPartToSinglePart class
        """
        super().__init__(source, target=target, xy_tolerance=None)
    # End init built-in

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
        if ANALYSIS_SETTINGS.extent:
            return self._make_intersection_query(
                self.source, field_names=select_names)
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
# End QueryMultiPartToSinglePart class


class QueryCopyFeatures(BaseQuerySelect):
    """
    Query for Copy Features
    """
# End QueryCopyFeatures class


class QueryAddXYCoordinates(AbstractSourceQuery):
    """
    Queries for Add XY Coordinates
    """
    def __init__(self, source: 'FeatureClass', weight_option: WeightOption) -> None:
        """
        Initialize the QueryAddXYCoordinates class
        """
        super().__init__(source, target=source, xy_tolerance=None)
        self._option: WeightOption = weight_option
    # End init built-in

    def __enter__(self) -> Self:
        """
        Context Manager Enter
        """
        self._prepare_source()
        self._delete_intermediate()
        _ = self._intermediate_table
        return self
    # End enter built-in

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Context Manager Exit
        """
        self._delete_intermediate()
        return False
    # End exit built-in

    def _delete_intermediate(self) -> None:
        """
        Delete Intermediate
        """
        name = self._intermediate_name
        with self.source.geopackage.connection as cin:
            cin.execute(f"""DROP TABLE IF EXISTS {TEMP_SCHEMA}{DOT}{name}""")
    # End _delete_intermediate method

    def _prepare_source(self) -> None:
        """
        Prepare Source by removing any of the controlled fields and then
        re-add just the controlled fields needed.
        """
        self.source.drop_fields((POINT_X, POINT_Y, POINT_Z, POINT_M))
        _, *fields = self._intermediate_fields
        self.source.add_fields(fields)
    # End _prepare_source method

    @cached_property
    def _intermediate_table(self) -> str:
        """
        Intermediate Table
        """
        name = self._intermediate_name
        defs = COMMA_SPACE.join(repr(f) for f in self._intermediate_fields)
        with self.source.geopackage.connection as cin:
            cin.execute(f"""CREATE TEMPORARY TABLE {name} ({defs})""")
        return f'{TEMP_SCHEMA}{DOT}{name}'
    # End _intermediate_table property

    @cached_property
    def _intermediate_name(self) -> str:
        """
        Intermediate Name
        """
        now = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return escape_name(f'tmp_{self.source.name}_add_xy_coords_{now}')
    # End _intermediate_name property

    @property
    def _intermediate_fields(self) -> FIELDS:
        """
        Intermediate Fields
        """
        fields = ORIG_FID, POINT_X, POINT_Y
        if self.source.has_z:
            fields = *fields, POINT_Z
        if self.source.has_m:
            fields = *fields, POINT_M
        return fields
    # End _intermediate_fields property

    @staticmethod
    def _make_update_from(element_name: str, key_name: str,
                          from_name: str, from_key_name: str,
                          field_names: NAMES) -> str:
        """
        Make SQL statement for Update
        """
        sets = [f'{name} = {from_name}{DOT}{name}' for name in field_names]
        return f"""
            UPDATE {element_name} 
            SET {COMMA_SPACE.join(sets)} 
            FROM {from_name}
            WHERE {element_name}{DOT}{key_name} = {from_name}{DOT}{from_key_name}
        """
    # End _make_update_from method

    @property
    def centroid_getter(self) -> Callable:
        """
        Centroid Getter
        """
        getter = GEOMETRY_CENTROID[self.source.shape_type]
        return partial(getter, has_z=self.source.has_z, has_m=self.source.has_m,
                       use_xy_length=self._option == WeightOption.TWO_D)
    # End centroid_getter property

    @property
    def target(self) -> 'FeatureClass':
        """
        Target
        """
        return self.source
    # End target property

    @property
    def select(self) -> str:
        """
        Select Geometry and FID
        """
        geom_type = get_geometry_column_name(
            self.source, include_geom_type=True)
        select_names = self._concatenate(
            geom_type, self.source.primary_key_field.escaped_name)
        if ANALYSIS_SETTINGS.extent:
            return self._make_intersection_query(
                self.source, field_names=select_names)
        return self._make_select(
            self.source, field_names=select_names, where_clause=SQL_FULL)
    # End select property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        return self._make_insert(
            self._intermediate_table,
            field_names=make_field_names(self._intermediate_fields),
            field_count=len(self._intermediate_fields))
    # End insert property

    @property
    def update(self) -> str:
        """
        Update Query
        """
        key_name, *field_names = [
            f.escaped_name for f in self._intermediate_fields]
        return self._make_update_from(
            element_name=self.target.escaped_name,
            key_name=self.target.primary_key_field.escaped_name,
            from_name=self._intermediate_table, from_key_name=key_name,
            field_names=field_names)
    # End update property
# End QueryAddXYCoordinates class


if __name__ == '__main__':  # pragma: no cover
    pass
