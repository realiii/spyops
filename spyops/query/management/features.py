# -*- coding: utf-8 -*-
"""
Query Classes for management.features module
"""


from abc import ABCMeta, abstractmethod
from collections import defaultdict
from functools import cached_property, partial
from operator import itemgetter
from typing import Callable, Generator, TYPE_CHECKING, Type, Union

from fudgeo import Field, SpatialReferenceSystem
from fudgeo.constant import FETCH_SIZE
from fudgeo.enumeration import ShapeType
from fudgeo.geometry import Point, PointZ, PointM, PointZM
from numpy import array
from pyproj import CRS
from shapely import (
    GeometryCollection, Polygon, get_num_coordinates, get_num_geometries)

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.crs.transform import make_transformer_function
from spyops.crs.util import get_crs_from_source, srs_from_crs
from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.core import HasZM, ZMConfig, zm_config
from spyops.geometry.attribute import (
    area_geodesic, area_planar, get_hole_count, get_inside_xy, length_geodesic,
    length_planar, line_azimuth, line_end, line_start)
from spyops.geometry.centroid import GEOMETRY_CENTROID
from spyops.geometry.enumeration import DimensionOption
from spyops.geometry.extent import (
    extent_from_geometry, extent_from_parts, extent_maximum, extent_minimum)
from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.minimum import GEOMETRY_MINIMUM, GEOMETRY_MINIMUM_ATTRS
from spyops.geometry.util import filter_features, to_shapely
from spyops.query.base import (
    AbstractQueryGroup, AbstractSourceQuery, AbstractSourceUpdateQuery,
    BaseQuerySelect)
from spyops.shared.constant import DRID, EMPTY
from spyops.shared.enumeration import (
    GeometryAttribute, MinimumGeometryOption, WeightOption)
from spyops.shared.field import (
    MBG_LENGTH, MBG_ORIENTATION, MBG_WIDTH, ORIG_FID, POINT_M, POINT_X, POINT_Y,
    POINT_Z, REASON, VALUE, add_orig_fid, get_geometry_column_name,
    make_field_names, make_unique_fields, validate_fields)
from spyops.shared.hint import ELEMENT, FIELDS, GRID_SIZE, NAMES, XY_TOL
from spyops.shared.sql import SQL_ALL_ID


if TYPE_CHECKING:  # pragma: no cover
    from sqlite3 import Connection
    from fudgeo import FeatureClass, Table
    from numpy import ndarray


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
    def __init__(self, source: 'FeatureClass',
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


class QueryXYTablePoint(AbstractSourceQuery):
    """
    Query for XY Table to Point Feature Class
    """
    def __init__(self, source: ELEMENT, target: 'FeatureClass',
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
    def point_class(self) -> Type[Point | PointZ | PointM | PointZM]:
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
    def __init__(self, source: ELEMENT, target: 'FeatureClass',
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
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass',
                 as_multi_part: bool) -> None:
        """
        Initialize the QueryFeatureEnvelopeToPolygon class
        """
        super().__init__(source, target=target)
        self._as_multi_part: bool = as_multi_part
    # End init built-in

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields and Rename Primary Key Columns if included
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
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass',
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
        Get Target Shape Type based on Output Type Option and Source Shape Type
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
                            geometries: Union['ndarray', list]) \
            -> dict[int, tuple]:
        """
        Process Geometries
        """
        bounder = self._bounding_function
        attributer = self._attribute_function
        polygons = bounder(geometries)
        if self.add_attributes:
            attributes = attributer(polygons)
            return {id_: (geom, attrs) for id_, geom, attrs in
                    zip(ids, polygons, attributes)}
        else:
            return {id_: (geom, ()) for id_, geom in zip(ids, polygons)}
    # End _process_geometries method

    def _build_fields(self, fields: list[Field]) -> FIELDS:
        """
        Build Fields
        """
        key_fields = self._get_key_fields()
        keys = [f.name.casefold() for f in key_fields]
        names = [f.name.casefold() for f in fields]
        if not any(key in names for key in keys):
            return *key_fields, *fields
        for key, fld in zip(keys, key_fields):
            if key not in names:
                continue
            index = names.index(key)
            fld, = make_unique_fields([fld, *fields], others=[fields[index]])
            fields[index] = fld
        return *key_fields, *fields
    # End _build_fields method

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
            return self._build_fields(list(self._fields))
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
        # NOTE this extent not used, simply filling a required argument
        index_where = self._spatial_index_where(elm, extent=(0, 0, 0, 0))
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
        # NOTE this extent not used, simply filling a required argument
        index_where = self._spatial_index_where(elm, extent=(0, 0, 0, 0))
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
        # NOTE this extent not used, simply filling a required argument
        index_where = self._spatial_index_where(elm, extent=(0, 0, 0, 0))
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
            return self._build_fields(list(validate_fields(
                self.source, fields=self.source.fields)))
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
        # NOTE this extent not used, simply filling a required argument
        index_where = self._spatial_index_where(elm, extent=(0, 0, 0, 0))
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
        # NOTE this extent not used, simply filling a required argument
        index_where = self._spatial_index_where(elm, extent=(0, 0, 0, 0))
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


if __name__ == '__main__':  # pragma: no cover
    pass
