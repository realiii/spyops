# -*- coding: utf-8 -*-
"""
Abstract Classes in support of Query objects
"""


from abc import ABCMeta, abstractmethod
from functools import cache, cached_property
from typing import TYPE_CHECKING, Union

from fudgeo import FeatureClass, Field
from fudgeo.constant import COMMA_SPACE
from shapely.creation import box

from gisworks.environment.core import zm_config
from gisworks.geometry.config import geometry_config
from gisworks.geometry.extent import extent_from_feature_class
from gisworks.geometry.multi import build_multi
from gisworks.shared.constant import (
    EMPTY, IN, NOT_IN, QUESTION, SQL_EMPTY, SQL_FULL, UNDERSCORE)
from gisworks.shared.element import copy_feature_class
from gisworks.shared.enumeration import AttributeOption
from gisworks.shared.field import (
    clone_field, get_geometry_column_name, make_field_names, validate_fields)
from gisworks.shared.hint import ELEMENT, EXTENT, FIELDS, XY_TOL
from gisworks.shared.util import make_unique_name


if TYPE_CHECKING:  # pragma: no cover
    from shapely import MultiLineString, MultiPoint, MultiPolygon
    from gisworks.environment.core import ZMConfig
    from gisworks.geometry.config import GeometryConfig


class AbstractQuery(metaclass=ABCMeta):
    """
    Base Query Support
    """
    def __init__(self, element: ELEMENT) -> None:
        """
        Initialize the AbstractQuery class
        """
        super().__init__()
        self._element: ELEMENT = element
    # End init built-in

    @staticmethod
    def _make_select(element: ELEMENT, field_names: str,
                     where_clause: str) -> str:
        """
        Make SQL statement for Select
        """
        return f"""
            SELECT {field_names}
            FROM {element.escaped_name} 
            WHERE {where_clause}
        """
    # End _make_select function

    @staticmethod
    def _make_insert(element_name: str, field_names: str, field_count: int) -> str:
        """
        Make SQL statement for Insert
        """
        return f"""
            INSERT INTO {element_name}({field_names}) 
            VALUES ({COMMA_SPACE.join(QUESTION * field_count)})
        """
    # End _make_insert function

    @cache
    def _field_names_and_count(self, element: ELEMENT) -> tuple[int, str, str]:
        """
        Field Names for Select and Insert + Derive Field Count
        """
        fields = validate_fields(element, fields=element.fields)
        select_names = insert_names = make_field_names(fields)
        field_count = len(fields)
        if isinstance(element, FeatureClass):
            geom = get_geometry_column_name(element)
            geom_type = get_geometry_column_name(
                element, include_geom_type=True)
            select_names = self._concatenate(geom_type, select_names)
            insert_names = self._concatenate(geom, insert_names)
            field_count += 1
        return field_count, insert_names, select_names
    # End _field_names_and_count method

    @staticmethod
    def _concatenate(left: str, right: str) -> str:
        """
        Conditionally Concatenate field names
        """
        if not right:
            return left
        return f'{left}{COMMA_SPACE}{right}'
    # End _concatenate method

    @property
    def source(self) -> ELEMENT:
        """
        Source
        """
        return self._element
    # End source property

    @property
    @abstractmethod
    def select(self) -> str:  # pragma: no cover
        """
        Selection Query
        """
        pass
    # End select property

    @property
    @abstractmethod
    def insert(self) -> str:  # pragma: no cover
        """
        Insert Query
        """
        pass
    # End insert property
# End AbstractQuery class


class AbstractSpatialQuery(AbstractQuery, metaclass=ABCMeta):
    """
    Abstract Spatial Query Support
    """
    def __init__(self, source: FeatureClass, target: FeatureClass | None,
                 operator: FeatureClass) -> None:
        """
        Initialize the AbstractSpatialQuery class
        """
        super().__init__(source)
        self._target: FeatureClass = target
        self._operator: FeatureClass = operator
    # End init built-in

    @cached_property
    def zm_config(self) -> 'ZMConfig':
        """
        ZM Configuration
        """
        return zm_config(self.source, self.operator)
    # End zm_config property

    @cached_property
    def geometry_config(self) -> 'GeometryConfig':
        """
        Geometry Configuration
        """
        return geometry_config(
            self.target, cast_geom=self.zm_config.is_different)
    # End geometry_config property

    @cached_property
    def geometry(self) -> Union['MultiPolygon', 'MultiLineString', 'MultiPoint']:
        """
        Multi-Part Geometry of the Operator Feature Class
        """
        return build_multi(self.operator)
    # End geometry property

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        return self.select_intersect
    # End select property

    @cached_property
    def operator_extent(self) -> EXTENT:
        """
        Operator Extent
        """
        return extent_from_feature_class(self.operator)
    # End operator_extent property

    @cached_property
    def source_extent(self) -> EXTENT:
        """
        Source Extent
        """
        return extent_from_feature_class(self.source)
    # End source_extent property

    @cached_property
    def shared_extent(self) -> EXTENT:
        """
        Shared Extent between source and operator
        """
        shared = box(*self.operator_extent).intersection(
            box(*self.source_extent))
        return shared.bounds
    # End shared_extent property

    @cached_property
    def has_intersection(self) -> bool:
        """
        Has Intersection between source and operator
        """
        return box(*self.operator_extent).intersects(box(*self.source_extent))
    # End has_intersection property

    @staticmethod
    def _spatial_index_where(element: FeatureClass, extent: EXTENT) -> str:
        """
        Make a where clause stub that can be used to select features which
        intersect an extent. The query is based on a spatial index (if present).
        """
        primary = element.primary_key_field
        if not element.has_spatial_index or not primary:  # pragma: no cover
            return EMPTY
        min_x, min_y, max_x, max_y = extent
        return f"""{primary.escaped_name} {{}} (
            SELECT id  
            FROM {element.spatial_index_name} 
            WHERE minx <= {max_x} AND maxx >= {min_x} AND 
                  miny <= {max_y} AND maxy >= {min_y})
        """
    # End _spatial_index_wheres function

    @property
    def source(self) -> FeatureClass:
        """
        Source
        """
        return self._element
    # End source property

    @property
    def operator(self) -> FeatureClass:
        """
        Operator
        """
        return self._operator
    # End operator property

    @property
    def target(self) -> FeatureClass:
        """
        Alias for Target Empty
        """
        return self.target_empty
    # End target property

    @cached_property
    def target_empty(self) -> FeatureClass:
        """
        Only the Structure of the Source copied to the Target Feature Class
        """
        return copy_feature_class(
            self.source, target=self._target, where_clause=SQL_EMPTY,
            config=self.zm_config)
    # End target_empty property

    @cached_property
    def target_full(self) -> FeatureClass:
        """
        Full Copy of the Source Feature Class
        """
        return copy_feature_class(
            self.source, target=self._target, where_clause=SQL_FULL,
            config=self.zm_config)
    # End target_full property

    @property
    def select_operator(self) -> str:
        """
        Selection Query for Operator
        """
        return self._make_intersection_query(self.operator)
    # End select_operator property

    @property
    def select_intersect(self) -> str:
        """
        Selection query for intersection
        """
        return self._make_intersection_query(self.source)
    # End select_intersect property

    def _make_intersection_query(self, element: FeatureClass) -> str:
        """
        Make Intersection Query
        """
        if where := self._spatial_index_where(element, extent=self.shared_extent):
            where = where.format(IN)
        else:  # pragma: no cover
            where = SQL_FULL
        *_, select_field_names = self._field_names_and_count(element)
        return self._make_select(
            element, field_names=select_field_names, where_clause=where)
    # End _make_intersection_query method

    @property
    def select_disjoint(self) -> str:
        """
        Selection query for disjoint
        """
        return self._make_disjoint_select(self.source)
    # End select_disjoint property

    def _make_disjoint_select(self, element: FeatureClass) -> str:
        """
        Make Disjoint Select Statement using the input Element
        """
        if not (where := self._spatial_index_where(
                element, extent=self.shared_extent)):  # pragma: no cover
            return EMPTY
        *_, select_field_names = self._field_names_and_count(element)
        return self._make_select(
            element, field_names=select_field_names,
            where_clause=where.format(NOT_IN))
    # End _make_disjoint_select method
# End AbstractSpatialQuery class


class AbstractSpatialAttribute(AbstractSpatialQuery, metaclass=ABCMeta):
    """
    Abstract class extending with attribute options
    """
    def __init__(self, source: FeatureClass, target: FeatureClass | None,
                 operator: FeatureClass, attribute_option: AttributeOption,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractSpatialAttribute class
        """
        super().__init__(source=source, target=target, operator=operator)
        self._attr_option: AttributeOption = attribute_option
        self._xy_tolerance: XY_TOL = xy_tolerance
    # End init built-in

    @cache
    def _field_names_and_count(self, element: ELEMENT) -> tuple[int, str, str]:
        """
        Override field names for Selection -- ignore insert names and count
        """
        fields = self._get_fields(element)
        select_names = make_field_names(fields)
        geom_type = get_geometry_column_name(element, include_geom_type=True)
        return 0, EMPTY, self._concatenate(geom_type, select_names)
    # End _field_names_and_count method

    def _get_fields(self, element: ELEMENT) -> FIELDS:
        """
        Get Fields from Element based on Attribute Option
        """
        if self._attr_option in (AttributeOption.ALL, AttributeOption.SANS_FID):
            fields = validate_fields(element, fields=element.fields)
        else:
            fields = []
        if self._attr_option in (AttributeOption.ALL, AttributeOption.ONLY_FID):
            fields = [element.primary_key_field, *fields]
        return fields
    # End _get_fields method

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields and Rename Primary Key Columns if included
        """
        if self._attr_option == AttributeOption.ALL:
            _, *src_fields = self._get_fields(self.source)
            _, *op_fields = self._get_fields(self.operator)
            src_fields = [self.output_fid_source, *src_fields]
            op_fields = self._make_unique_fields(src_fields, op_fields)
            return [*src_fields, self.output_fid_operator, *op_fields]
        elif self._attr_option == AttributeOption.ONLY_FID:
            return self.output_fid_source, self.output_fid_operator
        else:
            src_fields = self._get_fields(self.source)
            op_fields = self._get_fields(self.operator)
            op_fields = self._make_unique_fields(src_fields, op_fields)
            return [*src_fields, *op_fields]
    # End _get_unique_fields method

    @staticmethod
    def _make_unique_fields(base: FIELDS, others: FIELDS) -> FIELDS:
        """
        Make Unique Fields
        """
        names = {f.name.casefold() for f in base}
        return [clone_field(f, name=make_unique_name(f.name, names=names))
                for f in others]
    # End _make_unique_fields method

    @staticmethod
    def _make_fid_field(field: Field, element: ELEMENT) -> Field:
        """
        Make FID Field
        """
        return clone_field(field, name=f'{field.name}{UNDERSCORE}{element.name}')
    # End _make_fid_field method

    @cached_property
    def output_fid_source(self) -> Field:
        """
        Output FID for Source
        """
        field = self._make_fid_field(self.source.primary_key_field, self.source)
        return self._avoid_name_clash(field)
    # End output_fid_source property

    @cached_property
    def output_fid_operator(self) -> Field:
        """
        Output FID for Operator
        """
        source = self.output_fid_source
        names = {source.name.casefold()}
        field = self._make_fid_field(
            self.operator.primary_key_field, element=self.operator)
        field.name = make_unique_name(field.name, names=names)
        return self._avoid_name_clash(field)
    # End output_fid_operator property

    def _avoid_name_clash(self, field: Field) -> Field:
        """
        Avoid Name Clash with Source or Operator Fields
        """
        if self._attr_option != AttributeOption.ALL:
            return field
        # NOTE use slice (not unpacking) to avoid ValueError if no fields
        src_fields = self._get_fields(self.source)[1:]
        op_fields = self._get_fields(self.operator)[1:]
        fields = [*src_fields, *op_fields]
        field, = self._make_unique_fields(fields, [field])
        return field
    # End _avoid_name_clash method

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        return self._build_insert(self.target, fields=self._get_unique_fields())
    # End insert property

    def _build_insert(self, element: FeatureClass, fields: FIELDS) -> str:
        """
        Build Insert Statement from Fields
        """
        names = make_field_names(fields)
        geom_name = get_geometry_column_name(element)
        return self._make_insert(
            element.escaped_name,
            field_names=self._concatenate(geom_name, names),
            field_count=len(fields) + 1)
    # End _build_insert method

    @property
    @abstractmethod
    def target_empty(self) -> FeatureClass:  # pragma: no cover
        """
        Build the structure needed for the output feature class
        """
        pass
    # End target_empty property
# End AbstractSpatialAttribute class


if __name__ == '__main__':  # pragma: no cover
    pass
