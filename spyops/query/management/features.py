# -*- coding: utf-8 -*-
"""
Query Classes for management.features module
"""


from abc import ABCMeta, abstractmethod
from collections import defaultdict
from functools import cache, cached_property, partial
from operator import itemgetter
from typing import Callable, Generator, Optional, TYPE_CHECKING, Union

from fudgeo import FeatureClass, Field, MemoryGeoPackage, SpatialReferenceSystem
from fudgeo.constant import COMMA_SPACE, FETCH_SIZE, SHAPE
from fudgeo.enumeration import FieldType, ShapeType
from fudgeo.geometry import Point
from numpy import array
from pyproj import CRS
from shapely import (
    GeometryCollection, LineString, Point as ShapelyPoint, Polygon,
    get_num_coordinates, get_num_geometries)
from shapely.constructive import boundary
from shapely.coordinates import get_coordinates
from shapely.geometry.multilinestring import MultiLineString
from shapely.set_operations import union_all
from shapely.strtree import STRtree

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.crs.transform import make_transformer_function
from spyops.crs.util import get_crs_from_source, srs_from_crs
from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.environment.context import Swap
from spyops.environment.core import HasZM, ZMConfig, zm_config
from spyops.geometry.adjust import GEOMETRY_ADJUST_Z
from spyops.geometry.attribute import (
    area_geodesic, area_planar, get_hole_count, get_inside_xy, length_geodesic,
    length_planar, line_azimuth, line_end, line_start)
from spyops.geometry.centroid import GEOMETRY_CENTROID
from spyops.geometry.enumeration import DimensionOption
from spyops.geometry.extent import (
    extent_from_geometry, extent_from_parts, extent_maximum, extent_minimum)
from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.minimum import GEOMETRY_MINIMUM, GEOMETRY_MINIMUM_ATTRS
from spyops.geometry.segment import GEOMETRY_SEGMENT
from spyops.geometry.util import filter_features, get_geoms_iter, to_shapely
from spyops.geometry.vertex import (
    GEOMETRY_VERTICES_ALL, GEOMETRY_VERTICES_BOTH_ENDS, GEOMETRY_VERTICES_END,
    GEOMETRY_VERTICES_MIDDLE, GEOMETRY_VERTICES_START)
from spyops.geometry.wa import polygonize
from spyops.query.base import (
    AbstractQueryGroup, AbstractSourceQuery, AbstractSourceUpdateQuery,
    BaseQuerySelect)
from spyops.shared.constant import DRID, EMPTY
from spyops.shared.enumeration import (
    GeometryAttribute, MinimumGeometryOption, PointTypeOption, WeightOption)
from spyops.shared.field import (
    MBG_LENGTH, MBG_ORIENTATION, MBG_WIDTH, ORIG_FID, ORIG_SEQ, POINT_M,
    POINT_X, POINT_Y, POINT_Z, REASON, VALUE, add_key_fields, add_orig_fid,
    clone_field, get_geometry_column_name, make_field_names, validate_fields)
from spyops.shared.hint import (
    ELEMENT, FEATURE_CLASSES, FIELDS, GRID_SIZE, LINE_TYPE, NAMES, POINT_TYPE,
    SORT_FIELDS, XY_TOL)
from spyops.shared.keywords import HAS_M_KEY, HAS_Z_KEY, SRS_ID_KEY
from spyops.shared.records import select_transform_insert
from spyops.shared.sql import SQL_ALL_ID


if TYPE_CHECKING:  # pragma: no cover
    from sqlite3 import Connection
    from fudgeo import Table
    from numpy import ndarray


class QueryMultiPartToSinglePart(AbstractSourceQuery):
    """
    Queries for MultiPart to SinglePart
    """
    def __init__(self, source: FeatureClass, target: FeatureClass) -> None:
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
        Get Unique Fields and add ORIG_FID
        """
        return add_orig_fid(self.source)
    # End _get_unique_fields method

    @property
    def select(self) -> str:
        """
        Select from Source including FID
        """
        return self.select_with_fid
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
    def __init__(self, source: FeatureClass, target: 'Table',
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
        _, geom = self._intermediate_fields
        return [geom.escaped_name]
    # End _get_field_names method

    @property
    def drop_empty(self) -> str:
        """
        Drop Empty Features from Source Feature Class
        """
        name = self._intermediate_table
        orig_fid, _ = self._intermediate_fields
        # noinspection PyUnresolvedReferences
        key_name = self.source.primary_key_field.escaped_name
        return f"""
            DELETE FROM {self.source.escaped_name} 
            WHERE {key_name} IN (SELECT {orig_fid.name} FROM {name})
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
        orig_fid, _ = self._intermediate_fields
        fields = [orig_fid]
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
        # noinspection PyUnresolvedReferences
        target_key_name = self.target.primary_key_field.escaped_name
        return self._make_update_from(
            element_name=self.target.escaped_name, key_name=target_key_name,
            field_names=field_names, from_name=self._intermediate_table,
            from_key_name=key_name, from_field_names=from_field_names)
    # End update property
# End QueryRepairGeometry class


class QueryAddXYCoordinates(AbstractSourceUpdateQuery):
    """
    Queries for Add XY Coordinates
    """
    def __init__(self, source: FeatureClass,
                 weight_option: WeightOption) -> None:
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
    def __init__(self, source: FeatureClass, field: Field,
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


class QueryXYTablePoint(AbstractSourceQuery):
    """
    Query for XY Table to Point Feature Class
    """
    def __init__(self, source: ELEMENT, target: FeatureClass,
                 fields: tuple[Field | None, ...],
                 coordinate_system: CRS | SpatialReferenceSystem) -> None:
        """
        Initialize the QueryXYTablePoint class
        """
        # noinspection PyTypeChecker
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
    def point_class(self) -> POINT_TYPE:
        """
        Point Class
        """
        has_z, has_m = self._has_zm
        return FUDGEO_GEOMETRY_LOOKUP[ShapeType.point][has_z, has_m]
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

    @property
    def zm_config(self) -> ZMConfig:
        """
        ZM Configuration
        """
        has_z, has_m = self._has_zm
        return ZMConfig(is_different=False, z_enabled=has_z, m_enabled=has_m)
    # End zm_config property

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
# End QueryXYTablePoint class


class QueryXYTableLine(QueryXYTablePoint):
    """
    Query for XY to Line Feature Class
    """
    def __init__(self, source: ELEMENT, target: FeatureClass,
                 fields: tuple[Field, Field, Field, Field],
                 coordinate_system: CRS | SpatialReferenceSystem) -> None:
        """
        Initialize the QueryXYTableLine class
        """
        super().__init__(source, target=target, fields=fields,
                         coordinate_system=coordinate_system)
    # End init built-in

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.linestring
    # End _get_target_shape_type method

    @cached_property
    def source_transformer(self) -> Callable | None:
        """
        Transformer
        """
        return None
    # End source_transformer property

    @property
    def filter_extent(self) -> Polygon | None:
        """
        Filter Extent
        """
        return None
    # End filter_extent property

    @property
    def _has_zm(self) -> HasZM:
        """
        Has ZM
        """
        return HasZM(has_z=False, has_m=False)
    # End _has_zm property

    @cached_property
    def spatial_reference_system(self) -> SpatialReferenceSystem:
        """
        Spatial Reference System, the output coordinate system of the query
        which is determined by the output coordinate system of the analysis
        environment and if not set, the input coordinate system.
        """
        if isinstance(self._coord_sys, CRS):
            return srs_from_crs(self._coord_sys)
        return self._coord_sys
    # End spatial_reference_system property
# End QueryXYTableLine class


class QueryFeatureEnvelopeToPolygon(BaseQuerySelect):
    """
    Query Feature Envelope to Polygon
    """
    def __init__(self, source: FeatureClass, target: FeatureClass,
                 as_multi_part: bool) -> None:
        """
        Initialize the QueryFeatureEnvelopeToPolygon class
        """
        super().__init__(source, target=target)
        self._as_multi_part: bool = as_multi_part
    # End init built-in

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields and add ORIG_FID
        """
        return add_orig_fid(self.source)
    # End _get_unique_fields method

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        if self.as_multi_part:
            return ShapeType.multi_polygon
        return ShapeType.polygon
    # End _get_target_shape_type method

    @property
    def as_multi_part(self) -> bool:
        """
        As Multi Part, check the input Shape Type to see if the output should
        be multipart or not.
        """
        shape_type = self.source.shape_type
        if ShapeType.point in shape_type:
            return False
        return self._as_multi_part
    # End as_multi_part property

    @property
    def extent_getter(self) -> Callable:
        """
        Extent Getter
        """
        if self.as_multi_part:
            return extent_from_parts
        return extent_from_geometry
    # End extent_getter property

    @property
    def select(self) -> str:
        """
        Select from Source including FID
        """
        return self.select_with_fid
    # End select property

    @cached_property
    def zm_config(self) -> 'ZMConfig':
        """
        ZM Configuration

        Only generating a 2D extent regardless of the input feature class
        dimensions, which means that the presence of Z or M on the source
        (or from the settings) handled as is_different=True to ensure that
        geometry casting occurs.
        """
        zm = zm_config(self.source)
        is_different = zm.z_enabled or zm.m_enabled
        return ZMConfig(
            is_different=is_different, z_enabled=zm.z_enabled,
            m_enabled=zm.m_enabled)
    # End zm_config property
# End QueryFeatureEnvelopeToPolygon class


class AbstractQueryMinimumBoundingGeometry(AbstractQueryGroup,
                                           metaclass=ABCMeta):
    """
    Abstract Query Minimum Bounding Geometry Class
    """
    def __init__(self, source: FeatureClass, target: FeatureClass,
                 geometry_type: MinimumGeometryOption, *,
                 add_geometric_attributes: bool, fields: FIELDS) -> None:
        """
        Initialize the AbstractQueryMinimumBoundingGeometry class
        """
        super().__init__(
            source, target=target, fields=fields or [], xy_tolerance=None)
        self._geometry_type: MinimumGeometryOption = geometry_type
        self._add_attrs: bool = add_geometric_attributes
    # End init built-in

    @cached_property
    def zm_config(self) -> 'ZMConfig':
        """
        ZM Configuration

        Only generating a 2D bounding geometry regardless of the input feature
        class dimensions, which means that the presence of Z or M on the source
        (or from the settings) handled as is_different=True to ensure that
        geometry casting occurs.
        """
        zm = zm_config(self.source)
        is_different = zm.z_enabled or zm.m_enabled
        return ZMConfig(
            is_different=is_different, z_enabled=zm.z_enabled,
            m_enabled=zm.m_enabled)
    # End zm_config property

    @property
    def add_attributes(self) -> bool:
        """
        Add Geometric Attributes
        """
        return self._add_attrs
    # End add_attributes property

    @cached_property
    def _bounding_function(self) -> Callable:
        """
        Bounding Function
        """
        return GEOMETRY_MINIMUM[self._geometry_type]
    # End _bounding_function property

    @cached_property
    def _attribute_function(self) -> Callable:
        """
        Attribute Function
        """
        if not self.add_attributes:
            return lambda _: ()
        return GEOMETRY_MINIMUM_ATTRS[self._geometry_type]
    # End _attribute_function property

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.polygon
    # End _get_target_shape_type method

    @cached_property
    def source_transformer(self) -> Callable | None:
        """
        Source Transformer, overloaded since we want to ignore Z and M
        """
        elm = self.source
        transformer = self._get_transformer(elm)
        return make_transformer_function(
            elm.shape_type, has_z=False, has_m=False,
            transformer=transformer)
    # End source_transformer property

    @abstractmethod
    def grouped_geometries(self) -> Generator[dict[int, tuple], None, None]:
        """
        Grouped Geometries stored as a dictionary of Dense Rank IDs as the key
        and a tuple of Bounding Geometry + Optional Attributes as the value.
        Page over the number of groups to avoid loading all geometries into
        memory at once.

        This method builds up a dictionary of geometries and yields it when it
        reaches (or exceeds) fetch size.  There is an expectation that when a
        geometry is stitched together with its aggregate row that the geometry
        will be popped from the dictionary.
        """
        pass
    # End grouped_geometries method

    def _process_geometries(self, ids: 'ndarray',
                            geoms: Union['ndarray', list]) -> dict[int, tuple]:
        """
        Process Geometries
        """
        bounder = self._bounding_function
        attributer = self._attribute_function
        polygons = bounder(geoms)
        if self.add_attributes:
            attributes = attributer(polygons)
            return {id_: (geom, attrs) for id_, geom, attrs in
                    zip(ids, polygons, attributes)}
        else:
            return {id_: (geom, ()) for id_, geom in zip(ids, polygons)}
    # End _process_geometries method

    @abstractmethod
    def _get_key_fields(self) -> tuple[Field, ...]:
        """
        Get Key Fields
        """
        pass
    # End _get_key_fields method
# End AbstractQueryMinimumBoundingGeometry class


class QueryMinimumBoundingGeometryList(AbstractQueryMinimumBoundingGeometry):
    """
    Queries for Minimum Bounding Geometry (List)
    """
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        if self.add_attributes:
            return add_key_fields(list(self._fields), self._get_key_fields())
        return self._fields
    # End _get_unique_fields method

    def _get_key_fields(self) -> tuple[Field, ...]:
        """
        Get Key Fields
        """
        return MBG_WIDTH, MBG_LENGTH, MBG_ORIENTATION
    # End _get_key_fields method

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        elm = self.source
        index_where = self._spatial_index_where(elm)
        return f"""
            SELECT {DRID}, {self._group_names}
            FROM (SELECT dense_rank() OVER (
                    ORDER BY {self._group_names}) AS {DRID}, {self._group_names} 
                  FROM {elm.escaped_name} {index_where})
            GROUP BY {DRID} 
        """
    # End select property

    @property
    def select_geometry(self) -> str:
        """
        Select Geometry
        """
        elm = self.source
        geom = get_geometry_column_name(elm, include_geom_type=True)
        index_where = self._spatial_index_where(elm)
        return f"""
            SELECT * 
            FROM (SELECT {geom}, dense_rank() OVER (
                    ORDER BY {self._group_names}) AS {DRID}
                  FROM {elm.escaped_name} {index_where})
            WHERE {DRID} BETWEEN ? AND ?
        """
    # End select_geometry property

    def grouped_geometries(self) -> Generator[dict[int, tuple], None, None]:
        """
        Grouped Geometries stored as a dictionary of Dense Rank IDs as the key
        and a tuple of Bounding Geometry + Optional Attributes as the value.
        Page over the number of groups to avoid loading all geometries into
        memory at once.

        This method builds up a dictionary of geometries and yields it when it
        reaches (or exceeds) fetch size.  There is an expectation that when a
        geometry is stitched together with its aggregate row that the geometry
        will be popped from the dictionary.
        """
        grouped = {}
        size = FETCH_SIZE // 5
        steps, remainder = divmod(self.group_count, size)
        steps += bool(remainder)
        sql = self.select_geometry
        bounder = self._bounding_function
        attributer = self._attribute_function
        with self.source.geopackage.connection as cin:
            for step in range(steps):
                features, geometries = self._fetch_features(
                    cin, sql=sql, size=size, step=step)
                if not features:
                    continue
                ids = array([i for _, i in features], dtype=int)
                ranks = defaultdict(list)
                for id_, geom in zip(ids, geometries):
                    ranks[id_].append(geom)
                ids, geometries = zip(*ranks.items())
                geometries = [GeometryCollection(geoms) for geoms in geometries]
                grouped.update(self._process_geometries(ids, geometries))
                if len(grouped) >= FETCH_SIZE:
                    yield grouped
        yield grouped
    # End grouped_geometries method

    def _fetch_features(self, connection: 'Connection', sql: str, size: int,
                        step: int) -> tuple[list[tuple], 'ndarray']:
        """
        Fetch Features
        """
        start = 1 + (step * size)
        end = (step + 1) * size
        cursor = connection.execute(sql, (start, end))
        features = filter_features(cursor.fetchall())
        return to_shapely(
            features, transformer=self.source_transformer,
            option=DimensionOption.TWO_D)
    # End _fetch_features method
# End QueryMinimumBoundingGeometryList class


class QueryMinimumBoundingGeometryAll(AbstractQueryMinimumBoundingGeometry):
    """
    Queries for Minimum Bounding Geometry (All)
    """
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        if self.add_attributes:
            return self._get_key_fields()
        return []
    # End _get_unique_fields method

    def _get_key_fields(self) -> tuple[Field, ...]:
        """
        Get Key Fields
        """
        return MBG_WIDTH, MBG_LENGTH, MBG_ORIENTATION
    # End _get_key_fields method

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        return EMPTY
    # End select property

    @property
    def select_geometry(self) -> str:
        """
        Select Geometry
        """
        elm = self.source
        geom = get_geometry_column_name(elm, include_geom_type=True)
        index_where = self._spatial_index_where(elm)
        return f"""
            SELECT {geom} 
            FROM {elm.escaped_name} {index_where}
        """
    # End select_geometry property

    @cached_property
    def group_count(self) -> int:
        """
        Group Count
        """
        return len(self.source)
    # End group_count property

    def grouped_geometries(self) -> Generator[dict[int, tuple], None, None]:
        """
        Grouped Geometries stored as a dictionary of Dense Rank IDs as the key
        and a tuple of Bounding Geometry + Optional Attributes as the value.

        This method builds up a dictionary of geometries and yields it when it
        reaches (or exceeds) fetch size.  There is an expectation that when a
        geometry is stitched together with its aggregate row that the geometry
        will be popped from the dictionary.
        """
        key = 1
        size = FETCH_SIZE // 5
        steps, remainder = divmod(self.group_count, size)
        steps += bool(remainder)
        sql = self.select_geometry
        collections = []
        with self.source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            while features := cursor.fetchmany(size):
                if not (features := filter_features(features)):
                    continue
                features, geometries = to_shapely(
                    features, transformer=self.source_transformer,
                    option=DimensionOption.TWO_D)
                if not features:
                    continue
                collections.append(GeometryCollection(geometries))
        if not collections:
            yield {key: (Polygon(), ())}
        else:
            geom = self._bounding_function(GeometryCollection(collections))
            if geom is None or geom.is_empty:
                yield {key: (Polygon(), ())}
            else:
                if self.add_attributes:
                    attrs, = self._attribute_function([geom])
                else:
                    attrs = ()
                yield {key: (geom, attrs)}
    # End grouped_geometries method
# End QueryMinimumBoundingGeometryAll class


class QueryMinimumBoundingGeometryNone(AbstractQueryMinimumBoundingGeometry):
    """
    Queries for Minimum Bounding Geometry (None)
    """
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        if self.add_attributes:
            fields = validate_fields(self.source, fields=self.source.fields)
            return add_key_fields(list(fields), self._get_key_fields())
        return add_orig_fid(self.source)
    # End _get_unique_fields method

    def _get_key_fields(self) -> tuple[Field, ...]:
        """
        Get Key Fields
        """
        return ORIG_FID, MBG_WIDTH, MBG_LENGTH, MBG_ORIENTATION
    # End _get_key_fields method

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        elm = self.source
        # noinspection PyUnresolvedReferences
        name = self.source.primary_key_field.escaped_name
        if self.add_attributes:
            index = 4
        else:
            index = 1
        field_names = make_field_names(self._get_unique_fields()[index:])
        # NOTE double up on the key name, first value is used for lookup in
        #  the geometry dictionary, the second is used to store in ORIG_FID
        key_names = self._concatenate(name, name)
        field_names = self._concatenate(key_names, field_names)
        index_where = self._spatial_index_where(elm)
        return f"""
            SELECT {field_names} 
            FROM {elm.escaped_name} {index_where}
        """
    # End select property

    @property
    def select_geometry(self) -> str:
        """
        Select Geometry
        """
        elm = self.source
        geom = get_geometry_column_name(elm, include_geom_type=True)
        index_where = self._spatial_index_where(elm)
        # noinspection PyUnresolvedReferences
        name = self.source.primary_key_field.escaped_name
        geom_and_fid = self._concatenate(geom, name)
        return f"""
            SELECT {geom_and_fid} 
            FROM {elm.escaped_name} {index_where}
        """
    # End select_geometry property

    @cached_property
    def group_count(self) -> int:
        """
        Group Count
        """
        return len(self.source)
    # End group_count property

    def grouped_geometries(self) -> Generator[dict[int, tuple], None, None]:
        """
        Grouped Geometries stored as a dictionary of Dense Rank IDs as the key
        and a tuple of Bounding Geometry + Optional Attributes as the value.
        Page over the number of groups to avoid loading all geometries into
        memory at once.

        This method builds up a dictionary of geometries and yields it when it
        reaches (or exceeds) fetch size.  There is an expectation that when a
        geometry is stitched together with its aggregate row that the geometry
        will be popped from the dictionary.
        """
        grouped = {}
        size = FETCH_SIZE // 5
        sql = self.select_geometry
        with self.source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            while features := cursor.fetchmany(size):
                if not (features := filter_features(features)):
                    continue
                features, geometries = to_shapely(
                    features, transformer=self.source_transformer,
                    option=DimensionOption.TWO_D)
                if not features:
                    continue
                ids = array([i for _, i in features], dtype=int)
                grouped.update(self._process_geometries(ids, geometries))
                if len(grouped) >= FETCH_SIZE:
                    yield grouped
        yield grouped
    # End grouped_geometries method
# End QueryMinimumBoundingGeometryNone class


class QueryFeatureToPoint(BaseQuerySelect):
    """
    Query Feature to Point
    """
    def __init__(self, source: FeatureClass, target: FeatureClass,
                 inside: bool, weight_option: WeightOption) -> None:
        """
        Initialize the QueryFeatureToPoint class
        """
        super().__init__(source, target=target)
        self._inside: bool = inside
        self._option: WeightOption = weight_option
    # End init built-in

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields and add ORIG_FID
        """
        return add_orig_fid(self.source)
    # End _get_unique_fields method

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.point
    # End _get_target_shape_type method

    @property
    def coordinate_getter(self) -> Callable:
        """
        Coordinate Getter
        """
        if self._inside:
            return get_inside_xy
        has_z = self.source.has_z
        has_m = self.source.has_m
        return partial(
            GEOMETRY_CENTROID[self.source.shape_type], has_z=has_z,
            has_m=has_m, use_xy_length=self._option == WeightOption.TWO_D)
    # End coordinate_getter property

    @property
    def point_class(self) -> POINT_TYPE:
        """
        Point Class
        """
        if self._inside:
            return Point
        has_z, has_m = self._has_zm
        return FUDGEO_GEOMETRY_LOOKUP[ShapeType.point][has_z, has_m]
    # End point_class property

    @property
    def select(self) -> str:
        """
        Select from Source including FID
        """
        return self.select_with_fid
    # End select property

    @cached_property
    def zm_config(self) -> 'ZMConfig':
        """
        ZM Configuration, only generating a 2D point for inside.
        """
        zm = zm_config(self.source)
        if not self._inside:
            return zm
        is_different = zm.z_enabled or zm.m_enabled
        return ZMConfig(
            is_different=is_different, z_enabled=zm.z_enabled,
            m_enabled=zm.m_enabled)
    # End zm_config property
# End QueryFeatureToPoint class


class QueryFeatureVerticesToPoints(BaseQuerySelect):
    """
    Query Feature Vertices to Points
    """
    def __init__(self, source: FeatureClass, target: FeatureClass,
                 point_type: PointTypeOption) -> None:
        """
        Initialize the QueryFeatureVerticesToPoints class
        """
        super().__init__(source, target=target)
        self._point_type: PointTypeOption = point_type
    # End init built-in

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields and add ORIG_FID
        """
        return add_orig_fid(self.source)
    # End _get_unique_fields method

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.point
    # End _get_target_shape_type method

    @property
    def vertex_getter(self) -> Callable:
        """
        Vertex Getter
        """
        source = self.source
        shape_type = source.shape_type
        if self._point_type == PointTypeOption.MID:
            func = GEOMETRY_VERTICES_MIDDLE[shape_type]
            kwargs = {HAS_Z_KEY: source.has_z,
                      HAS_M_KEY: source.has_m,
                      SRS_ID_KEY: source.spatial_reference_system.srs_id}
            return partial(func, **kwargs)
        elif self._point_type == PointTypeOption.START:
            return GEOMETRY_VERTICES_START[shape_type]
        elif self._point_type == PointTypeOption.END:
            return GEOMETRY_VERTICES_END[shape_type]
        elif self._point_type == PointTypeOption.BOTH_ENDS:
            return GEOMETRY_VERTICES_BOTH_ENDS[shape_type]
        else:
            return GEOMETRY_VERTICES_ALL[shape_type]
    # End vertex_getter property

    @property
    def select(self) -> str:
        """
        Select from Source including FID
        """
        return self.select_with_fid
    # End select property

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
# End QueryFeatureVerticesToPoints class


class QuerySplitLineAtVertices(BaseQuerySelect):
    """
    Query Split Line at Vertices
    """
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields and add ORIG_FID and ORIG_SEQ
        """
        fields = validate_fields(self.source, fields=self.source.fields)
        return add_key_fields(list(fields), [ORIG_FID, ORIG_SEQ])
    # End _get_unique_fields method

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.linestring
    # End _get_target_shape_type method

    @property
    def select(self) -> str:
        """
        Select from Source including FID
        """
        return self.select_with_fid
    # End select property

    @property
    def segment_getter(self) -> Callable:
        """
        Segment Getter
        """
        elm = self.source
        srs_id = elm.spatial_reference_system.srs_id
        cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.linestring][elm.has_z, elm.has_m]
        return partial(GEOMETRY_SEGMENT[elm.shape_type],
                       **{SRS_ID_KEY: srs_id, 'geom_cls': cls})
    # End segment_getter property

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
# End QuerySplitLineAtVertices class


class QueryPolygonToLine(BaseQuerySelect):
    """
    Query Polygon to Line
    """
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields and add ORIG_FID and ORIG_SEQ
        """
        return add_orig_fid(self.source)
    # End _get_unique_fields method

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.linestring
    # End _get_target_shape_type method

    @property
    def select(self) -> str:
        """
        Select from Source including FID
        """
        return self.select_with_fid
    # End select property

    @property
    def polygon_getter(self) -> Callable:
        """
        Polygon Getter
        """
        if self.source.is_multi_part:
            return lambda x: x
        return lambda x: [x]
    # End polygon_getter property

    @property
    def line_class(self) -> LINE_TYPE:
        """
        Line Class
        """
        has_z = self.source.has_z
        has_m = self.source.has_m
        return FUDGEO_GEOMETRY_LOOKUP[ShapeType.linestring][has_z, has_m]
    # End line_class property

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
# End QueryPolygonToLine class


class QueryFeatureToPrepare(BaseQuerySelect):
    """
    Query for each input to Feature to Polygon / Feature to Line
    """
    def __init__(self, source: FeatureClass, target: Optional[FeatureClass],
                 xy_tolerance: XY_TOL = None) -> None:
        """
        Initialize the QueryFeatureToPrepare class
        """
        # noinspection PyTypeChecker
        super().__init__(source, target=target, xy_tolerance=xy_tolerance)
    # End init built-in

    @cache
    def _field_names_and_count(self, element: FeatureClass) -> tuple[int, str, str]:
        """
        Limit fields to just geometry
        """
        insert_names = get_geometry_column_name(element)
        select_names = get_geometry_column_name(element, include_geom_type=True)
        return 1, insert_names, select_names
    # End _field_names_and_count method

    def _get_unique_fields(self) -> FIELDS:
        """
        Limit fields to just geometry, sans attributes
        """
        return []
    # End _get_unique_fields method
# End QueryFeatureToPrepare class


class BaseQueryFeatureTo(AbstractSourceQuery):
    """
    Base Query Feature To
    """
    def __init__(self, source: FEATURE_CLASSES, target: FeatureClass,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the BaseQueryFeatureTo class
        """
        src, *_ = source
        super().__init__(src, target=target, xy_tolerance=xy_tolerance)
        self._source: FEATURE_CLASSES = source
    # End init built-in

    @cached_property
    def spatial_reference_system(self) -> Optional['SpatialReferenceSystem']:
        """
        Spatial Reference System, the output coordinate system of the query
        which is determined by the output coordinate system of the analysis
        environment and if not set, the spatial reference system of the first
        feature class in the source.
        """
        crs = ANALYSIS_SETTINGS.output_coordinate_system
        if isinstance(crs, CRS):
            return srs_from_crs(crs)
        source, *_ = self._source
        return source.spatial_reference_system
    # End spatial_reference_system property

    @cached_property
    def zm_config(self) -> 'ZMConfig':
        """
        ZM Configuration
        """
        return zm_config(*self._source)
    # End zm_config property

    @property
    def insert(self) -> str:
        """
        Insert SQL
        """
        elm = self.target
        fields = self._get_unique_fields()
        insert_field_names = make_field_names(fields)
        insert_field_names = self._concatenate(
            get_geometry_column_name(elm), insert_field_names)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=len(fields) + 1)
    # End insert property

    @property
    def _has_zm(self) -> HasZM:
        """
        Has ZM
        """
        has_z = any(source.has_z for source in self._source)
        has_m = any(source.has_m for source in self._source)
        return HasZM(has_z=has_z, has_m=has_m)
    # End _has_zm property

    def _get_lines(self, scratch: MemoryGeoPackage) \
            -> tuple[list, list[QueryFeatureToPrepare], GRID_SIZE]:
        """
        Get lines from the input feature classes, the lines will be
        in the Output Coordinate System and planarized.
        """
        sizes = []
        lines = []
        queries = []
        xy_tol = self._xy_tolerance
        srs = self.spatial_reference_system
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, srs):
            for i, source in enumerate(self._source):
                query = QueryFeatureToPrepare(
                    source, target=FeatureClass(scratch, name=f'fc_{i}'),
                    xy_tolerance=xy_tol)
                queries.append(query)
                fc = select_transform_insert(query)
                if not len(fc):
                    continue
                self._fetch_lines_sizes(query, lines=lines, sizes=sizes)
        if not lines:
            return lines, queries, None
        grid_size = max([s for s in sizes if s is not None], default=None)
        lines = get_geoms_iter(union_all(lines, grid_size=grid_size))
        # noinspection PyTypeChecker
        return lines, queries, grid_size
    # End _get_lines method

    @staticmethod
    def _fetch_lines_sizes(query: QueryFeatureToPrepare,
                           lines: list[LineString],
                           sizes: list[GRID_SIZE]) -> None:
        """
        Fetch Lines from memory feature classes and grid sizes from query
        """
        fc = query.target
        cursor = fc.select(include_primary=True)
        is_polygon = ShapeType.polygon in fc.shape_type
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            _, geoms = to_shapely(features, transformer=None)
            if is_polygon:
                geoms = boundary(geoms)
            lines.extend(geoms)
            sizes.append(query.grid_size)
    # End _fetch_lines_sizes method

    def _get_null_record(self) -> tuple:
        """
        Get Null Record
        """
        return tuple([None] * len(self._get_unique_fields()))
    # End _get_null_record method
# End BaseQueryFeatureTo class


class QueryFeatureToPolygon(BaseQueryFeatureTo):
    """
    Query Feature to Polygon
    """
    def __init__(self, source: FEATURE_CLASSES, target: FeatureClass,
                 label: Optional[FeatureClass], xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QueryFeatureToPolygon class
        """
        super().__init__(source, target=target, xy_tolerance=xy_tolerance)
        self._label: Optional[FeatureClass] = label
    # End init built-in

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.polygon
    # End _get_target_shape_type method

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        label = self._label
        if label is None:
            return []
        return validate_fields(label, fields=label.fields)
    # End _get_unique_fields method

    def build_features(self) -> list[tuple[Polygon, tuple]]:
        """
        Polygonized Features
        """
        scratch = MemoryGeoPackage.create()
        lines, _, _ = self._get_lines(scratch)
        if conn := scratch.connection:
            conn.close()
        if not len(lines):
            return []
        if not (polygons := self._build_polygons(lines)):
            return []
        return self._add_attributes(polygons)
    # End build_features method

    def _add_attributes(self, polygons: list[Polygon]) \
            -> list[tuple[Polygon, tuple]]:
        """
        Add Attributes, keeping all matches between label points and planarized
        """
        nulls = self._get_null_record()
        points, attributes = self._get_points_attributes()
        if not attributes:
            return [(polygon, nulls) for polygon in polygons]
        if not (grouper := self._index_overlay(points, polygons)):
            return [(polygon, nulls) for polygon in polygons]
        results = []
        for i, polygon in enumerate(polygons):
            if i in grouper:
                results.extend(
                    [(polygon, attributes[idx]) for idx in grouper[i]])
            else:
                results.append((polygon, nulls))
        return results
    # End _add_attributes method

    def _get_points_attributes(self) -> tuple[list[ShapelyPoint], list[tuple]]:
        """
        Get Points and Attributes
        """
        points = []
        attributes = []
        if self._label is None or not self._get_unique_fields():
            return points, attributes
        # noinspection PyTypeChecker
        query = QueryCopyFeatures(self._label, target=None)
        transformer = query.source_transformer
        srs = self.spatial_reference_system
        with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, srs),
              self._label.geopackage.connection as cin):
            cursor = cin.execute(query.select)
            while features := cursor.fetchmany(FETCH_SIZE):
                if not (features := filter_features(features)):
                    continue
                features, geoms = to_shapely(
                    features, transformer=transformer,
                    option=DimensionOption.TWO_D)
                if not features:
                    continue
                points.extend(geoms)
                attributes.extend([feature[1:] for feature in features])
        return points, attributes
    # End _get_points_attributes method

    @staticmethod
    def _index_overlay(points: list[ShapelyPoint], polygons: list[Polygon]) \
            -> defaultdict[int, list[int]]:
        """
        Build cross-reference between label planarized polygons and label points
        for use in assigning attributes to polygons
        """
        tree = STRtree(polygons)
        intersects = tree.query(points, predicate='intersects')
        grouper = defaultdict(list)
        for pnt_idx, poly_idx in intersects.T.tolist():
            grouper[poly_idx].append(pnt_idx)
        return grouper
    # End _index_overlay method

    @staticmethod
    def _build_polygons(lines: list[LineString]) -> list[Polygon]:
        """
        Build Polygons
        """
        collections = polygonize(lines)
        if isinstance(collections, GeometryCollection):
            collections = [collections]
        planarized = []
        for collection in collections:
            planarized.extend(get_geoms_iter(collection))
        return planarized
    # End _build_polygons method
# End QueryFeatureToPolygon class


class QueryFeatureToLine(BaseQueryFeatureTo):
    """
    Query Feature To Line
    """
    def __init__(self, source: FEATURE_CLASSES, target: FeatureClass,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QueryFeatureToPolygon class
        """
        super().__init__(source, target=target, xy_tolerance=xy_tolerance)
    # End init built-in

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type based on Output Type Option and Source Shape Type
        """
        return ShapeType.linestring
    # End _get_target_shape_type method

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        return []
    # End _get_unique_fields method

    def build_features(self) -> list[tuple[LineString, tuple]]:
        """
        LineString Features
        """
        scratch = MemoryGeoPackage.create()
        lines, *_ = self._get_lines(scratch)
        if conn := scratch.connection:
            conn.close()
        combiner = self.geometry_config.combiner
        lines = get_geoms_iter(combiner(MultiLineString(lines)))
        # noinspection PyTypeChecker
        return [(line, ()) for line in lines]
    # End build_features method
# End QueryFeatureToLine class


class AbstractQueryPointsToLine(AbstractQueryGroup):
    """
    Abstract Query Points to Line
    """
    def __init__(self, source: FeatureClass, target: FeatureClass,
                 group_fields: FIELDS, sort_fields: SORT_FIELDS,
                 close_line: bool, is_continuous: bool) -> None:
        """
        Initialize the AbstractQueryPointsToLine class
        """
        super().__init__(
            source, target=target, fields=group_fields or [], xy_tolerance=None)
        self._sort_fields: SORT_FIELDS = sort_fields or []
        self._close_line: bool = close_line
        self._is_continuous: bool = is_continuous
    # End init built-in

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.linestring
    # End _get_target_shape_type method

    @cache
    def _field_names_and_count(self, element: FeatureClass) -> tuple[int, str, str]:
        """
        Field Names for Select and Insert + Derive Field Count
        """
        fields, select_names = self._build_select_names(element, element.fields)
        field_count, insert_names = self._build_insert_names(element, fields)
        return field_count, insert_names, select_names
    # End _field_names_and_count method

    def _build_insert_names(self, element: FeatureClass,
                            fields: FIELDS) -> tuple[int, str]:
        """
        Build Insert Name and get Field Count
        """
        field_count = len(fields) + 1
        insert_names = self._concatenate(
            get_geometry_column_name(element), make_field_names(fields))
        return field_count, insert_names
    # End _build_insert_names method

    def _build_select_names(self, element: FeatureClass,
                            fields: FIELDS) -> tuple[FIELDS, str]:
        """
        Build Select Names
        """
        fields = validate_fields(element, fields=fields)
        geom_type = get_geometry_column_name(element, include_geom_type=True)
        return fields, self._concatenate(geom_type, make_field_names(fields))
    # End _build_select_names method

    @property
    def _line_class(self) -> LINE_TYPE:
        """
        Line Class
        """
        has_z, has_m = self._has_zm
        return FUDGEO_GEOMETRY_LOOKUP[ShapeType.linestring][has_z, has_m]
    # End _line_class property

    def _get_coordinates(self, points: defaultdict[int, list[ShapelyPoint]]) \
            -> dict[int, 'ndarray'] | dict[int, list]:
        """
        Get Coordinates from Points
        """
        has_z, has_m = self._has_zm
        coords = {id_: get_coordinates(pts, include_z=has_z, include_m=has_m)
                  for id_, pts in points.items()}
        coords = {id_: values for id_, values in coords.items()
                  if len(values) > 1}
        if self._close_line:
            coords = {id_: [*values, values[0]]
                      for id_, values in coords.items()}
        return coords
    # End _get_coordinates method

    def _build_segments(self, points: defaultdict[int, list[ShapelyPoint]],
                        attributes: defaultdict[int, list[tuple]]) \
            -> list[tuple[LineString, tuple]]:
        """
        Segment Lines and Attributes (Two Point Lines)
        """
        features = []
        cls = self._line_class
        coords = self._get_coordinates(points)
        # noinspection PyUnresolvedReferences
        srs_id = self.spatial_reference_system.srs_id
        attributes = self._get_segment_attrs(attributes)
        for id_, coords in coords.items():
            if id_ not in attributes:
                continue
            features.extend([
                (cls([start, end], srs_id=srs_id), *attrs)
                for start, end, attrs in
                zip(coords[:-1], coords[1:], attributes[id_])])
        features, geoms = to_shapely(features, transformer=None)
        return [(g, attrs) for g, (_, *attrs) in zip(geoms, features)]
    # End _build_segments method

    def _build_lines(self, points: defaultdict[int, list[ShapelyPoint]],
                     attributes: defaultdict[int, list[tuple]]) \
            -> list[tuple[LineString, tuple]]:
        """
        Continuous Lines and Attributes
        """
        features = []
        cls = self._line_class
        coords = self._get_coordinates(points)
        # noinspection PyUnresolvedReferences
        srs_id = self.spatial_reference_system.srs_id
        attributes = self._get_line_attrs(attributes)
        for id_, coords in coords.items():
            if id_ not in attributes:
                continue
            # noinspection PyTypeChecker
            features.append((cls(coords, srs_id=srs_id), *attributes[id_]))
        features, geoms = to_shapely(features, transformer=None)
        return [(g, attrs) for g, (_, *attrs) in zip(geoms, features)]
    # End _build_lines method

    def _close_segment_attrs(self, attributes: defaultdict[int, list[tuple]]) -> None:
        """
        Close Segment Attributes
        """
        if not self._close_line:
            return
        for id_, attrs in attributes.items():
            attributes[id_].append(attrs[0])
    # End _close_segment_attrs method

    @abstractmethod
    def _get_segment_attrs(self, attributes: defaultdict[int, list[tuple]]) \
            -> dict[int, list[tuple]]:  # pragma: no cover
        """
        Get Segment Attributes
        """
        pass
    # End _get_segment_attrs method

    @abstractmethod
    def _get_line_attrs(self, attributes: defaultdict[int, list[tuple]]) \
            -> dict[int, tuple]:  # pragma: no cover
        """
        Get Continuous Line Attributes
        """
        pass
    # End _get_line_attrs method

    @property
    def select_geometry(self) -> str:
        """
        Select Geometry
        """
        elm = self.source
        geom = get_geometry_column_name(elm, include_geom_type=True)
        index_where = self._spatial_index_where(elm)
        *_, select_names = self._field_names_and_count(elm)
        sql = f"""
            SELECT *  
            FROM (SELECT {geom}, dense_rank() OVER (
                    ORDER BY {self._group_names}) AS {DRID}, {select_names}
                  FROM {elm.escaped_name} {index_where})
            WHERE {DRID} BETWEEN ? AND ?
        """
        if not self._sort_fields:
            return sql
        sorts = COMMA_SPACE.join([f'{field!r}' for field in self._sort_fields])
        sorts = self._concatenate(DRID, sorts)
        return f'{sql} ORDER BY {sorts}'
    # End select_geometry property

    def line_features(self) -> Generator[list[tuple[LineString, tuple]], None, None]:
        """
        Line Features
        """
        results = []
        size = FETCH_SIZE // 5
        steps, remainder = divmod(self.group_count, size)
        steps += bool(remainder)
        sql = self.select_geometry
        if self._is_continuous:
            builder = self._build_lines
        else:
            builder = self._build_segments
        with self.source.geopackage.connection as cin:
            for step in range(steps):
                start = 1 + (step * size)
                end = (step + 1) * size
                cursor = cin.execute(sql, (start, end))
                features = filter_features(cursor.fetchall())
                features, points = to_shapely(
                    features, transformer=self.source_transformer)
                if not features:
                    continue
                point_grouper = defaultdict(list)
                attr_grouper = defaultdict(list)
                for (_, id_, _, *attrs), pt in zip(features, points):
                    point_grouper[id_].append(pt)
                    attr_grouper[id_].append(attrs)
                results.extend(builder(point_grouper, attr_grouper))
                if len(results) >= FETCH_SIZE:
                    yield results
                    results.clear()
        yield results
    # End line_features method
# End AbstractQueryPointsToLine class


class QueryPointsToLineNone(AbstractQueryPointsToLine):
    """
    Query Points to Line -- No Atttributes (besides group fields)
    """
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        fields = [s.field for s in self._sort_fields]
        return validate_fields(self.source, fields=[*self._fields, *fields])
    # End _get_unique_fields method

    @cache
    def _field_names_and_count(self, element: FeatureClass) -> tuple[int, str, str]:
        """
        Field Names for Select and Insert + Derive Field Count
        """
        fields = self._get_unique_fields()
        fields, select_names = self._build_select_names(element, fields)
        field_count, insert_names = self._build_insert_names(element, fields)
        return field_count, insert_names, select_names
    # End _field_names_and_count method

    def _get_segment_attrs(self, attributes: defaultdict[int, list[tuple]]) \
            -> dict[int, list[tuple]]:
        """
        Get Segment Attributes
        """
        return attributes
    # End _get_segment_attrs method

    def _get_line_attrs(self, attributes: defaultdict[int, list[tuple]]) \
            -> dict[int, tuple]:
        """
        Get Continuous Line Attributes
        """
        return {id_: attrs for id_, (attrs, *_) in attributes.items()}
    # End _get_line_attrs method
# End QueryPointsToLineNone class


class QueryPointsToLineBoth(AbstractQueryPointsToLine):
    """
    Query Points to Line -- Both Start and End Atttributes
    """
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        fields = []
        validated = validate_fields(self.source, fields=self.source.fields)
        for prefix in ('START', 'END'):
            for field in validated:
                fields.append(clone_field(
                    field, name=f'{prefix}_{field.name}', allow_null=True))
        return fields
    # End _get_unique_fields method

    @cache
    def _field_names_and_count(self, element: FeatureClass) -> tuple[int, str, str]:
        """
        Field Names for Select and Insert + Derive Field Count
        """
        _, select_names = self._build_select_names(element, element.fields)
        fields = self._get_unique_fields()
        field_count, insert_names = self._build_insert_names(element, fields)
        return field_count, insert_names, select_names
    # End _field_names_and_count method

    def _get_segment_attrs(self, attributes: defaultdict[int, list[tuple]]) \
            -> dict[int, list[tuple]]:
        """
        Get Segment Attributes
        """
        self._close_segment_attrs(attributes)
        for id_, attrs in attributes.items():
            attributes[id_] = [
                (*start, *end) for start, end in zip(attrs[:-1], attrs[1:])]
        return attributes
    # End _get_segment_attrs method

    def _get_line_attrs(self, attributes: defaultdict[int, list[tuple]]) \
            -> dict[int, tuple]:
        """
        Get Continuous Line Attributes
        """
        return {id_: (*attrs[0], *attrs[-1])
                for id_, attrs in attributes.items()}
    # End _get_line_attrs method
# End QueryPointsToLineBoth class


class QueryPointsToLineStart(AbstractQueryPointsToLine):
    """
    Query Points to Line -- Start Atttributes
    """
    def _get_segment_attrs(self, attributes: defaultdict[int, list[tuple]]) \
            -> dict[int, list[tuple]]:
        """
        Get Segment Attributes
        """
        self._close_segment_attrs(attributes)
        for id_ in attributes:
            # noinspection PyArgumentEqualDefault
            attributes[id_].pop(-1)
        return attributes
    # End _get_segment_attrs method

    def _get_line_attrs(self, attributes: defaultdict[int, list[tuple]]) \
            -> dict[int, tuple]:
        """
        Get Continuous Line Attributes
        """
        return {id_: attrs for id_, (attrs, *_) in attributes.items()}
    # End _get_line_attrs method
# End QueryPointsToLineStart class


class QueryPointsToLineEnd(AbstractQueryPointsToLine):
    """
    Query Points to Line -- End Atttributes
    """
    def _get_segment_attrs(self, attributes: defaultdict[int, list[tuple]]) \
            -> dict[int, list[tuple]]:
        """
        Get Segment Attributes
        """
        self._close_segment_attrs(attributes)
        for id_ in attributes:
            attributes[id_].pop(0)
        return attributes
    # End _get_segment_attrs method

    def _get_line_attrs(self, attributes: defaultdict[int, list[tuple]]) \
            -> dict[int, tuple]:
        """
        Get Continuous Line Attributes
        """
        return {id_: attrs for id_, (*_, attrs) in attributes.items()}
    # End _get_line_attrs method
# End QueryPointsToLineEnd class


class QueryAdjust3DZ(AbstractSourceUpdateQuery):
    """
    Queries for Adjust 3D Z
    """
    def __init__(self, source: FeatureClass,
                 adjuster: Callable[['ndarray'], 'ndarray'],
                 where_clause: str) -> None:
        """
        Initialize the QueryAdjust3DZ class
        """
        super().__init__(source, where_clause=where_clause)
        self._adjuster: Callable[['ndarray'], 'ndarray'] = adjuster
    # End init built-in

    def _get_field_names(self) -> NAMES:
        """
        Get Field Names
        """
        return self.source.geometry_column_name,
    # End _get_field_names method

    @property
    def _short_name(self) -> str:
        """
        Short Name
        """
        return 'adjust_z'
    # End _short_name property

    def _prepare_source(self) -> None:
        """
        Override
        """
        pass
    # End _prepare_source method

    @property
    def _intermediate_fields(self) -> FIELDS:
        """
        Intermediate Fields
        """
        return ORIG_FID, Field(SHAPE, data_type=FieldType.text)
    # End _intermediate_fields property

    @property
    def z_adjuster(self) -> Callable:
        """
        Z Adjuster
        """
        adjust_z = GEOMETRY_ADJUST_Z[self.source.shape_type]
        return partial(adjust_z, adjuster=self._adjuster)
    # End z_adjuster property
# End QueryAdjust3DZ class


if __name__ == '__main__':  # pragma: no cover
    pass
