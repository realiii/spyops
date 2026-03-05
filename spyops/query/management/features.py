# -*- coding: utf-8 -*-
"""
Query Classes for management.features module
"""


from functools import cached_property, partial
from operator import itemgetter
from typing import Callable, TYPE_CHECKING, Type

from fudgeo import Field, SpatialReferenceSystem
from fudgeo.enumeration import ShapeType
from fudgeo.geometry import Point, PointZ, PointM, PointZM
from pyproj import CRS
from shapely import get_num_coordinates, get_num_geometries, Polygon

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.crs.transform import make_transformer_function
from spyops.crs.util import get_crs_from_source, srs_from_crs
from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.core import HasZM
from spyops.geometry.attribute import (
    area_geodesic, area_planar, extent_maximum, extent_minimum, get_hole_count,
    get_inside_xy, length_geodesic, length_planar, line_azimuth, line_end,
    line_start)
from spyops.geometry.centroid import GEOMETRY_CENTROID
from spyops.query.base import (
    AbstractSourceQuery, AbstractSourceUpdateQuery, BaseQuerySelect)
from spyops.shared.enumeration import GeometryAttribute, WeightOption
from spyops.shared.field import (
    ORIG_FID, POINT_M, POINT_X, POINT_Y, POINT_Z, REASON, VALUE,
    get_geometry_column_name, make_field_names, make_unique_fields,
    validate_fields)
from spyops.shared.hint import FIELDS, GRID_SIZE, NAMES, XY_TOL
from spyops.shared.sql import SQL_ALL_ID


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, Table


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
            self.source, field_names=select_names, where_clause=SQL_ALL_ID)
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


class QueryCopyFeatures(BaseQuerySelect):
    """
    Query for Copy Features
    """
# End QueryCopyFeatures class


class QueryCheckGeometry(BaseQuerySelect):
    """
    Query for Check Geometry
    """
    def __init__(self, source: 'FeatureClass', target: 'Table',
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QueryCheckGeometry class
        """
        super().__init__(source, target=target, xy_tolerance=xy_tolerance)
    # End init built-in

    @property
    def _fields(self) -> FIELDS:
        """
        Fields
        """
        return ORIG_FID, REASON
    # End _fields property

    @cached_property
    def grid_size(self) -> GRID_SIZE:
        """
        Grid Size Overload, use xy tolerance as-is
        """
        return self._xy_tolerance
    # End grid_size property

    @property
    def target(self) -> 'Table':
        """
        Target
        """
        return self.target_empty
    # End target property

    @cached_property
    def target_empty(self) -> 'Table':
        """
        Target Empty
        """
        return self._target.geopackage.create_table(
            self._target.name, fields=self._fields,
            description='Results from Check Geometry',
            overwrite=ANALYSIS_SETTINGS.overwrite)
    # End target_empty property
# End QueryCheckGeometry class


class QueryRepairGeometry(AbstractSourceUpdateQuery):
    """
    Query for Repair Geometry
    """
    @property
    def _short_name(self) -> str:
        """
        Short Name
        """
        return 'repair_geom'
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
        orig_id, geom = self._intermediate_fields
        return [geom.escaped_name]
    # End _get_field_names method

    @property
    def drop_empty(self) -> str:
        """
        Drop Empty Features from Source Feature Class
        """
        name = self._intermediate_table
        orig_id, _ = self._intermediate_fields
        key_name = self.source.primary_key_field.escaped_name
        return f"""
            DELETE FROM {self.source.escaped_name} 
            WHERE {key_name} IN (SELECT {orig_id.name} FROM {name})
        """
    # End drop_empty property

    @property
    def truncate(self) -> str:
        """
        Truncate Query for Intermediate Table
        """
        name = self._intermediate_table
        # noinspection SqlWithoutWhere
        return f"""DELETE FROM {name}"""
    # End truncate method

    @property
    def insert_identifiers(self) -> str:
        """
        Insert Query for Identifiers
        """
        orig_id, _ = self._intermediate_fields
        fields = [orig_id]
        return self._make_insert(
            self._intermediate_table,
            field_names=make_field_names(fields), field_count=len(fields))
    # End insert_identifiers property

    @property
    def update(self) -> str:
        """
        Update Query
        """
        field_names = self._get_field_names()
        key_name, *from_field_names = [
            f.escaped_name for f in self._intermediate_fields]
        return self._make_update_from(
            element_name=self.target.escaped_name,
            key_name=self.target.primary_key_field.escaped_name,
            field_names=field_names,
            from_name=self._intermediate_table, from_key_name=key_name,
            from_field_names=from_field_names)
    # End update property
# End QueryRepairGeometry class


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
    # End _short_name property

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
    def _output_crs(self) -> 'CRS':
        """
        Output CRS, if not set use the source CRS
        """
        if not (crs := ANALYSIS_SETTINGS.output_coordinate_system):
            crs = get_crs_from_source(self.source)
        return crs
    # End _output_crs property

    def _length_getter(self) -> Callable:
        """
        Length Getter
        """
        crs = self._output_crs
        attrs = GeometryAttribute.LENGTH, GeometryAttribute.PERIMETER
        if self._attribute in attrs and crs.is_projected:
            func = length_planar
        else:
            func = length_geodesic
        return partial(func, crs=crs, unit=self._length_unit)
    # End _length_getter method

    def _area_getter(self) -> Callable:
        """
        Area Getter
        """
        crs = self._output_crs
        if self._attribute == GeometryAttribute.AREA and crs.is_projected:
            func = area_planar
        else:
            func = area_geodesic
        return partial(func, crs=crs, unit=self._area_unit)
    # End _area_getter method

    @property
    def _short_name(self) -> str:
        """
        Short Name
        """
        return 'calc_geom_attrs'
    # End _short_name property

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
        elif attr in (GeometryAttribute.LENGTH_GEODESIC,
                      GeometryAttribute.LENGTH,
                      GeometryAttribute.PERIMETER_GEODESIC,
                      GeometryAttribute.PERIMETER):
            return self._length_getter()
        elif attr in (GeometryAttribute.AREA_GEODESIC,
                      GeometryAttribute.AREA):
            return self._area_getter()
        elif attr == GeometryAttribute.LINE_AZIMUTH:
            return partial(line_azimuth, crs=self._output_crs)
        else:
            return lambda _: None
    # End attribute_getter property
# End QueryCalculateGeometryAttributes class


class QueryXYTable(AbstractSourceQuery):
    """
    Query for XY Table to Point Feature Class
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass',
                 fields: tuple[Field | None, ...],
                 coordinate_system: CRS | SpatialReferenceSystem) -> None:
        """
        Initialize the QueryXYTable class
        """
        super().__init__(source, target=target, xy_tolerance=None)
        self._fields: tuple[Field | None, ...] = fields
        self._coord_sys: CRS | SpatialReferenceSystem = coordinate_system
    # End init built-in

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.point
    # End _get_target_shape_type method

    @property
    def point_class(self) -> Type[Point | PointZ | PointM | PointZM]:
        """
        Point Class
        """
        has_z, has_m = self._has_zm
        if has_z and has_m:
            return PointZM
        elif has_z:
            return PointZ
        elif has_m:
            return PointM
        return Point
    # End point_class property

    @property
    def item_getter(self) -> itemgetter:
        """
        Item Getter
        """
        indexes = []
        lookup = {field.name.casefold(): i for i, field in
                  enumerate(self._get_unique_fields())}
        for field in self._fields:
            if not field:
                continue
            indexes.append(lookup[field.name.casefold()])
        return itemgetter(*indexes)
    # End item_getter property

    @property
    def select(self) -> str:
        """
        Select from Source
        """
        select_names = make_field_names(self._get_unique_fields())
        return self._make_select(
            self.source, field_names=select_names, where_clause=SQL_ALL_ID)
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
        in_crs = get_crs_from_source(self._coord_sys)
        out_crs = get_crs_from_source(self.spatial_reference_system)
        transformer = self._get_transformer_or_guess(in_crs, out_crs)
        has_z, has_m = self._has_zm
        return make_transformer_function(
            self._get_target_shape_type(), has_z=has_z, has_m=has_m,
            transformer=transformer)
    # End source_transformer property

    @property
    def filter_extent(self) -> Polygon | None:
        """
        Filter Extent
        """
        if not (extent := ANALYSIS_SETTINGS.extent):
            return None
        return self._get_extent_polygon(
            extent, crs=get_crs_from_source(self._coord_sys))
    # End filter_extent property

    @property
    def _has_zm(self) -> HasZM:
        """
        Has ZM
        """
        *_, z_field, m_field = self._fields
        has_z = z_field is not None
        has_m = m_field is not None
        return HasZM(has_z=has_z, has_m=has_m)
    # End _has_zm property

    @cached_property
    def spatial_reference_system(self) -> SpatialReferenceSystem:
        """
        Spatial Reference System, the output coordinate system of the query
        which is determined by the output coordinate system of the analysis
        environment and if not set, the input coordinate system.
        """
        crs = ANALYSIS_SETTINGS.output_coordinate_system
        if isinstance(crs, CRS):
            return srs_from_crs(crs)
        if isinstance(self._coord_sys, CRS):
            return srs_from_crs(self._coord_sys)
        return self._coord_sys
    # End spatial_reference_system property
# End QueryXYTable class


if __name__ == '__main__':  # pragma: no cover
    pass
