# -*- coding: utf-8 -*-
"""
Query Classes for management.features module
"""


from functools import cached_property, partial
from operator import attrgetter, itemgetter
from typing import Callable, TYPE_CHECKING

from fudgeo.enumeration import ShapeType
from shapely import get_num_coordinates, get_num_geometries

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.crs.transform import make_transformer_function
from spyops.environment import ANALYSIS_SETTINGS
from spyops.geometry.attribute import (
    get_hole_count, get_inside_xy, line_end, line_start)
from spyops.geometry.centroid import GEOMETRY_CENTROID
from spyops.geometry.extent import extent_maximum, extent_minimum
from spyops.query.base import (
    AbstractSourceQuery, AbstractSourceUpdateQuery, BaseQuerySelect)
from spyops.shared.constant import (
    LINES_ATTR, POINTS_ATTR, POLYGONS_ATTR, SQL_FULL)
from spyops.shared.enumeration import GeometryAttribute, WeightOption
from spyops.shared.field import (
    ORIG_FID, POINT_M, POINT_X, POINT_Y, POINT_Z, VALUE,
    get_geometry_column_name, make_field_names, make_unique_fields,
    validate_fields)
from spyops.shared.hint import FIELDS, NAMES


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, Field


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


class QueryAddXYCoordinates(AbstractSourceUpdateQuery):
    """
    Queries for Add XY Coordinates
    """
    def __init__(self, source: 'FeatureClass', weight_option: WeightOption) -> None:
        """
        Initialize the QueryAddXYCoordinates class
        """
        super().__init__(source)
        self._option: WeightOption = weight_option
    # End init built-in

    def _get_field_names(self) -> NAMES:
        """
        Get Field Names
        """
        _, *field_names = [f.escaped_name for f in self._intermediate_fields]
        return field_names
    # End _get_field_names method

    @property
    def _short_name(self) -> str:
        """
        Short Name
        """
        return 'add_xy_coords'
    # End _stub property

    def _prepare_source(self) -> None:
        """
        Prepare Source by removing any of the controlled fields and then
        re-add just the controlled fields needed.
        """
        self.source.drop_fields((POINT_X, POINT_Y, POINT_Z, POINT_M))
        _, *fields = self._intermediate_fields
        self.source.add_fields(fields)
    # End _prepare_source method

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

    @property
    def centroid_getter(self) -> Callable:
        """
        Centroid Getter
        """
        getter = GEOMETRY_CENTROID[self.source.shape_type]
        return partial(getter, has_z=self.source.has_z, has_m=self.source.has_m,
                       use_xy_length=self._option == WeightOption.TWO_D)
    # End centroid_getter property
# End QueryAddXYCoordinates class


class QueryCalculateGeometryAttributes(AbstractSourceUpdateQuery):
    """
    Queries for Calculate Geometry Attributes
    """
    def __init__(self, source: 'FeatureClass', field: Field,
                 geometry_attribute: GeometryAttribute, *,
                 weight_option: WeightOption,
                 length_unit: LengthUnit, area_unit: AreaUnit) -> None:
        """
        Initialize the QueryCalculateGeometryAttributes class
        """
        super().__init__(source)
        self._field: Field = field
        self._attribute: GeometryAttribute = geometry_attribute
        self._option: WeightOption = weight_option
        self._length_unit: LengthUnit = length_unit
        self._area_unit: AreaUnit = area_unit
    # End init built-in

    def _get_field_names(self) -> NAMES:
        """
        Get Field Names
        """
        return self._field.escaped_name,
    # End _get_field_names method

    @property
    def _point_attributes(self) -> tuple[GeometryAttribute, ...]:
        """
        Point Attributes
        """
        return (GeometryAttribute.POINT_X, GeometryAttribute.POINT_Y,
                GeometryAttribute.POINT_Z, GeometryAttribute.POINT_M)
    # End _point_attributes property

    @property
    def _centroid_attributes(self) -> tuple[GeometryAttribute, ...]:
        """
        Centroid Attributes
        """
        return (GeometryAttribute.CENTROID_X, GeometryAttribute.CENTROID_Y,
                GeometryAttribute.CENTROID_Z, GeometryAttribute.CENTROID_M)
    # End _centroid_attributes property

    @property
    def _extent_minimum_attributes(self) -> tuple[GeometryAttribute, ...]:
        """
        Extent Minimum Attributes
        """
        return (GeometryAttribute.EXTENT_MIN_X, GeometryAttribute.EXTENT_MIN_Y,
                GeometryAttribute.EXTENT_MIN_Z, GeometryAttribute.EXTENT_MIN_M)
    # End _extent_minimum_attributes property

    @property
    def _extent_maximum_attributes(self) -> tuple[GeometryAttribute, ...]:
        """
        Extent Maximum Attributes
        """
        return (GeometryAttribute.EXTENT_MAX_X, GeometryAttribute.EXTENT_MAX_Y,
                GeometryAttribute.EXTENT_MAX_Z, GeometryAttribute.EXTENT_MAX_M)
    # End _extent_maximum_attributes property

    @property
    def _line_start_attributes(self) -> tuple[GeometryAttribute, ...]:
        """
        Line Start Attributes
        """
        return (GeometryAttribute.LINE_START_X, GeometryAttribute.LINE_START_Y,
                GeometryAttribute.LINE_START_Z, GeometryAttribute.LINE_START_M)
    # End _line_start_attributes property

    @property
    def _line_end_attributes(self) -> tuple[GeometryAttribute, ...]:
        """
        Line End Attributes
        """
        return (GeometryAttribute.LINE_END_X, GeometryAttribute.LINE_END_Y,
                GeometryAttribute.LINE_END_Z, GeometryAttribute.LINE_END_M)
    # End _line_end_attributes property

    @property
    def _inside_attributes(self) -> tuple[GeometryAttribute, ...]:
        """
        Inside Attributes
        """
        return GeometryAttribute.INSIDE_X, GeometryAttribute.INSIDE_Y
    # End _inside_attributes property

    @property
    def _short_name(self) -> str:
        """
        Short Name
        """
        return 'calc_geom_attrs'
    # End _stub property

    def _prepare_source(self) -> None:
        """
        Prepare Source, do nothing implementation
        """
        pass
    # End _prepare_source method

    @property
    def _intermediate_fields(self) -> FIELDS:
        """
        Intermediate Fields
        """
        return ORIG_FID, VALUE
    # End _intermediate_fields property

    @property
    def item_getter(self) -> Callable:
        """
        Item Getter
        """
        attr = self._attribute
        attributes = (
            self._point_attributes,
            self._centroid_attributes,
            self._extent_minimum_attributes,
            self._extent_maximum_attributes,
            self._inside_attributes,
            self._line_start_attributes,
            self._line_end_attributes,
        )
        for attrs in attributes:
            if attr not in attrs:
                continue
            index = attrs.index(attr)
            if index == 3:
                index = -1
            return itemgetter(index)
        return lambda x: x
    # End item_getter property

    @property
    def attribute_getter(self) -> Callable:
        """
        Attribute Getter
        """
        attr = self._attribute
        has_z = self.source.has_z
        has_m = self.source.has_m
        if attr in (*self._point_attributes, *self._centroid_attributes):
            return partial(
                GEOMETRY_CENTROID[self.source.shape_type], has_z=has_z,
                has_m=has_m, use_xy_length=self._option == WeightOption.TWO_D)
        elif attr in self._extent_minimum_attributes:
            return partial(extent_minimum, has_z=has_z, has_m=has_m)
        elif attr in self._extent_maximum_attributes:
            return partial(extent_maximum, has_z=has_z, has_m=has_m)
        elif attr in self._inside_attributes:
            return get_inside_xy
        elif attr in self._line_start_attributes:
            return partial(line_start, has_z=has_z, has_m=has_m)
        elif attr in self._line_end_attributes:
            return partial(line_end, has_z=has_z, has_m=has_m)
        elif attr == GeometryAttribute.POINT_COUNT:
            return get_num_coordinates
        elif attr == GeometryAttribute.PART_COUNT:
            return get_num_geometries
        elif attr == GeometryAttribute.HOLE_COUNT:
            return get_hole_count
        else:
            return lambda _: None
    # End attribute_getter property
# End QueryCalculateGeometryAttributes class


if __name__ == '__main__':  # pragma: no cover
    pass
