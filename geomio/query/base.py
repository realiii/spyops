# -*- coding: utf-8 -*-
"""
Abstract Classes in support of Query objects
"""


from abc import ABCMeta, abstractmethod
from functools import cache, cached_property

from fudgeo import FeatureClass, Field
from fudgeo.constant import COMMA_SPACE, FID
from shapely import box

from geomio.shared.base import OverlayConfig
from geomio.shared.constant import (
    DUNDER_FID, EMPTY, IN, NOT_IN, QUESTION, SQL_EMPTY, SQL_FULL, UNDERSCORE)
from geomio.shared.element import copy_feature_class, create_feature_class
from geomio.shared.enumeration import AttributeOption
from geomio.shared.field import (
    clone_field, get_geometry_column_name, make_field_names, validate_fields)
from geomio.shared.geometry import extent_from_feature_class, overlay_config
from geomio.shared.hint import ELEMENT, EXTENT, FIELDS
from geomio.shared.util import make_unique_name


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
        select_field_names = insert_field_names = make_field_names(fields)
        field_count = len(fields)
        if isinstance(element, FeatureClass):
            geom = get_geometry_column_name(element)
            geom_type = get_geometry_column_name(
                element, include_geom_type=True)
            select_field_names = f'{geom_type}{COMMA_SPACE}{select_field_names}'
            insert_field_names = f'{geom}{COMMA_SPACE}{insert_field_names}'
            field_count += 1
        return field_count, insert_field_names, select_field_names
    # End _field_names_and_count method

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
    def __init__(self, source: FeatureClass, target: FeatureClass,
                 operator: FeatureClass) -> None:
        """
        Initialize the AbstractSpatialQuery class
        """
        super().__init__(source)
        self._target: FeatureClass = target
        self._operator: FeatureClass = operator
    # End init built-in

    @cached_property
    def config(self) -> OverlayConfig:
        """
        Overlay Configuration
        """
        return overlay_config(
            self.source, target=self.target, operator=self.operator)
    # End config property

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
            self.source, target=self._target, where_clause=SQL_EMPTY)
    # End target_empty property

    @cached_property
    def target_full(self) -> FeatureClass:
        """
        Full Copy of the Source Feature Class
        """
        return copy_feature_class(
            self.source, target=self._target, where_clause=SQL_FULL)
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

    def _make_intersection_query(self, elm: FeatureClass) -> str:
        """
        Make Intersection Query
        """
        if where := self._spatial_index_where(elm, extent=self.shared_extent):
            where = where.format(IN)
        else:  # pragma: no cover
            where = SQL_FULL
        *_, select_field_names = self._field_names_and_count(elm)
        return self._make_select(
            elm, field_names=select_field_names, where_clause=where)
    # End _make_intersection_query method

    @property
    def select_disjoint(self) -> str:
        """
        Selection query for disjoint
        """
        elm = self.source
        if not (where := self._spatial_index_where(
                elm, extent=self.shared_extent)):  # pragma: no cover
            return EMPTY
        *_, select_field_names = self._field_names_and_count(elm)
        return self._make_select(
            elm, field_names=select_field_names,
            where_clause=where.format(NOT_IN))
    # End select_disjoint property
# End AbstractSpatialQuery class


class AbstractSpatialAttribute(AbstractSpatialQuery, metaclass=ABCMeta):
    """
    Abstract class extending with attribute options
    """
    def __init__(self, source: FeatureClass, target: FeatureClass,
                 operator: FeatureClass,
                 attribute_option: AttributeOption) -> None:
        """
        Initialize the AbstractSpatialAttribute class
        """
        super().__init__(source=source, target=target, operator=operator)
        self._attr_option: AttributeOption = attribute_option
    # End init built-in

    @cache
    def _field_names_and_count(self, element: ELEMENT) -> tuple[int, str, str]:
        """
        Override field names for Selection -- ignore insert names and count
        """
        fields = self._get_fields(element)
        geom_type = get_geometry_column_name(element, include_geom_type=True)
        select_field_names = make_field_names(fields)
        return 0, EMPTY, f'{geom_type}{COMMA_SPACE}{select_field_names}'
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
            src, *src_fields = self._get_fields(self.source)
            op, *op_fields = self._get_fields(self.operator)
            src, op = self._make_primaries(src, op)
            # NOTE make unique if the fid field names are already in use
            src = self._make_unique_fields(src_fields, [src])
            op = self._make_unique_fields(op_fields, [op])
            fields = [*src, *src_fields]
            op_fields = self._make_unique_fields(fields, [*op, *op_fields])
            return [*fields, *op_fields]
        elif self._attr_option == AttributeOption.ONLY_FID:
            src, *_ = self._get_fields(self.source)
            op, *_ = self._get_fields(self.operator)
            return self._make_primaries(src, op)
        else:
            return self._get_unique_fields_sans_fid()
    # End _get_unique_fields method

    def _get_unique_fields_sans_fid(self) -> list[Field]:
        """
        Get Unique Fields for the SANS_FID Attribute Option
        """
        src_fields = self._get_fields(self.source)
        op_fields = self._get_fields(self.operator)
        op_fields = self._make_unique_fields(src_fields, op_fields)
        return [*src_fields, *op_fields]
    # End _get_unique_fields_sans_fid method

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
        name = field.name
        if name.startswith(DUNDER_FID):
            name = FID
        return clone_field(field, name=f'{name}{UNDERSCORE}{element.name}')
    # End _make_fid_field method

    def _make_primaries(self, source: Field, operator: Field) -> tuple[Field, Field]:
        """
        Make Unique Primary Key Columns
        """
        source = self._make_fid_field(source, self.source)
        operator = self._make_fid_field(operator, self.operator)
        names = {source.name.casefold()}
        operator.name = make_unique_name(operator.name, names=names)
        return source, operator
    # End _make_primaries method

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        fields = self._get_unique_fields()
        names = make_field_names(fields)
        geom_name = get_geometry_column_name(self.target)
        return self._make_insert(
            self.target.escaped_name,
            field_names=f'{geom_name}{COMMA_SPACE}{names}',
            field_count=len(fields) + 1)
    # End insert property

    @cached_property
    def target_empty(self) -> FeatureClass:
        """
        Build the structure needed for the output feature class
        """
        return create_feature_class(
            geopackage=self._target.geopackage, name=self._target.name,
            shape_type=self.source.shape_type,
            srs=self.source.spatial_reference_system,
            fields=self._get_unique_fields(),
            z_enabled=self.source.has_z, m_enabled=self.source.has_m)
    # End target_empty property
# End AbstractSpatialAttribute class


if __name__ == '__main__':  # pragma: no cover
    pass
