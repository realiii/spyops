# -*- coding: utf-8 -*-
"""
Abstract Classes in support of Query objects
"""


from abc import ABCMeta, abstractmethod
from collections import defaultdict
from functools import cache, cached_property
from typing import Callable, Generator, Optional, TYPE_CHECKING
from warnings import warn

from fudgeo import FeatureClass, MemoryGeoPackage
from fudgeo.constant import COMMA_SPACE, FETCH_SIZE
from fudgeo.enumeration import ShapeType
from pyproj import CRS
from shapely import GeometryCollection
from shapely.constructive import boundary
from shapely.coordinates import transform
from shapely.creation import box
from shapely.set_operations import union_all

from spyops.crs.transform import (
    get_transform_best_guess, make_transformer_function)
from spyops.crs.util import (
    crs_from_srs, get_crs_from_source, srs_from_crs)
from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.environment.context import Swap
from spyops.environment.core import HasZM, zm_config
from spyops.environment.util import get_geographic_transformation, get_grid_size
from spyops.geometry.config import geometry_config
from spyops.geometry.extent import extent_from_feature_class, is_degenerate
from spyops.geometry.util import filter_features, get_geoms_iter, to_shapely
from spyops.geometry.wa.poly import polygonize
from spyops.query.mixin import (
    GroupQueryMixin, IntermediateTableContextMixin, OperatorMixin)
from spyops.shared.constant import (
    DOT, EMPTY, QUESTION, SKIP_FILE_PREFIXES, UNDERSCORE)
from spyops.shared.element import copy_feature_class, create_feature_class
from spyops.shared.enumeration import AttributeOption
from spyops.shared.exception import BadExtentWarning
from spyops.shared.field import (
    ORIG_FID, clone_field, get_geometry_column_name, make_field_names,
    make_unique_fields, validate_fields)
from spyops.shared.hint import (
    ELEMENT, EXTENT, FEATURE_CLASSES, FIELDS, GRID_SIZE, NAMES, SORT_FIELDS,
    XY_TOL)
from spyops.shared.records import select_transform_insert
from spyops.shared.sql import IN, NOT_IN, SQL_ALL_ID, SQL_NO_ID
from spyops.shared.util import make_unique_name


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Field, SpatialReferenceSystem
    from pyproj.transformer import Transformer
    from shapely import LineString, Polygon
    from shapely.strtree import STRtree
    from shapely.geometry.base import BaseMultipartGeometry
    from spyops.environment.base import Extent
    from spyops.environment.core import ZMConfig
    from spyops.geometry.config import GeometryConfig


class AbstractElementQuery(metaclass=ABCMeta):
    """
    Abstract Query Support
    """
    def __init__(self, element: ELEMENT, *, where_clause: str = EMPTY) -> None:
        """
        Initialize the AbstractElementQuery class
        """
        super().__init__()
        self._element: ELEMENT = element
        self._where_clause: str = where_clause
    # End init built-in

    def _get_where_clause(self) -> str:
        """
        Get Where Clause
        """
        return (self._where_clause or EMPTY).strip() or SQL_ALL_ID
    # End _get_where_clause method

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
    def _make_insert(element_name: str, field_names: str,
                     field_count: int) -> str:
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
# End AbstractElementQuery class


class AbstractFeatureClassQuery(AbstractElementQuery, metaclass=ABCMeta):
    """
    Abstract Feature Class Query
    """
    def __init__(self, element: FeatureClass, *, where_clause: str = EMPTY,
                 xy_tolerance: XY_TOL = None) -> None:
        """
        Initialize the AbstractFeatureClassQuery class
        """
        super().__init__(element, where_clause=where_clause)
        self._xy_tolerance: XY_TOL = xy_tolerance
    # End init built-in

    def _get_transformer(self, feature_class: FeatureClass) \
            -> Optional['Transformer']:
        """
        Get Transformer
        """
        if not (srs := self.spatial_reference_system):
            return None
        crs = crs_from_srs(srs)
        fc_crs = crs_from_srs(feature_class.spatial_reference_system)
        return self._get_transformer_or_guess(fc_crs, crs)
    # End _get_transformer method

    @staticmethod
    def _get_transformer_or_guess(from_crs: CRS, to_crs: CRS) \
            -> Optional['Transformer']:
        """
        Get Transformer from Geographic Transformations or Best Guess
        """
        if transformer := get_geographic_transformation(
                source_crs=from_crs, target_crs=to_crs,
                transformations=ANALYSIS_SETTINGS.geographic_transformations):
            return transformer
        return get_transform_best_guess(from_crs, to_crs)
    # End _get_transformer_or_guess method

    def _get_extent_polygon(self, extent: 'Extent', crs: 'CRS') -> 'Polygon':
        """
        Get Extent Polygon in the specified Coordinate Reference System
        """
        polygon = extent.polygon
        if transformer := self._get_transformer_or_guess(extent.crs, crs):
            # noinspection bad-argument-type
            polygon = transform(
                polygon, transformer.transform, interleaved=False)
            if is_degenerate(polygon.bounds):
                warn('Bad extent polygon after transformation, '
                     'extent will be ignored', category=BadExtentWarning,
                     skip_file_prefixes=SKIP_FILE_PREFIXES)
        return polygon
    # End _get_extent_polygon method

    def _spatial_index_where(self, element: FeatureClass,
                             extent: EXTENT = (0, 0, 0, 0)) -> str:
        """
        Make a where clause stub that can be used to select features which
        intersect an extent. The query is based on a spatial index (if present).
        """
        if not isinstance(element, FeatureClass):
            return EMPTY
        primary = element.primary_key_field
        if not element.has_spatial_index or not primary:  # pragma: no cover
            return EMPTY
        if is_degenerate(extent):
            return EMPTY
        min_x, min_y, max_x, max_y = extent
        return f"""{primary.escaped_name} {{}} (
            SELECT id  
            FROM {element.spatial_index_name} 
            WHERE minx <= {max_x} AND maxx >= {min_x} AND 
                  miny <= {max_y} AND maxy >= {min_y})
        """
    # End _spatial_index_where function

    @cached_property
    def source_crs(self) -> CRS:
        """
        Source CRS
        """
        return get_crs_from_source(self.source)
    # End source_crs property

    @cached_property
    def source_transformer(self) -> Callable | None:
        """
        Source Transformer
        """
        elm = self.source
        transformer = self._get_transformer(elm)
        return make_transformer_function(
            elm.shape_type, has_z=elm.has_z, has_m=elm.has_m,
            transformer=transformer)
    # End source_transformer property

    @cached_property
    def spatial_reference_system(self) -> Optional['SpatialReferenceSystem']:
        """
        Spatial Reference System, the output coordinate system of the query
        which is determined by the output coordinate system of the analysis
        environment and if not set, the spatial reference system of the source.
        """
        if not isinstance(self.source, FeatureClass):
            return None
        crs = ANALYSIS_SETTINGS.output_coordinate_system
        if isinstance(crs, CRS):
            return srs_from_crs(crs)
        return self.source.spatial_reference_system
    # End spatial_reference_system property

    @cached_property
    def grid_size(self) -> GRID_SIZE:
        """
        Grid Size
        """
        return get_grid_size(
            source=self.source, xy_tolerance=self._xy_tolerance,
            target_srs=self.spatial_reference_system)
    # End grid_size property
# End AbstractFeatureClassQuery class


class AbstractElementGroupQuery(GroupQueryMixin, AbstractElementQuery,
                                metaclass=ABCMeta):
    """
    Abstract Group Query
    """
    def __init__(self, element: ELEMENT, fields: FIELDS) -> None:
        """
        Initialize the AbstractElementGroupQuery class
        """
        super().__init__(element)
        self._fields: FIELDS = fields
        self._group_names: str = make_field_names(fields)
    # End init built-in
# End AbstractElementGroupQuery class


class AbstractFeatureClassGroupQuery(GroupQueryMixin, AbstractFeatureClassQuery,
                                     metaclass=ABCMeta):
    """
    Abstract Feature Class Group Query
    """
    def __init__(self, element: FeatureClass, fields: FIELDS, *,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractFeatureClassGroupQuery class
        """
        super().__init__(element, xy_tolerance=xy_tolerance)
        self._fields: FIELDS = fields
        self._group_names: str = make_field_names(fields)
    # End init built-in
# End AbstractFeatureClassGroupQuery class


class AbstractSourceQuery(AbstractFeatureClassQuery, metaclass=ABCMeta):
    """
    Abstract Source Query
    """
    def __init__(self, source: FeatureClass, target: FeatureClass, *,
                 where_clause: str = EMPTY, xy_tolerance: XY_TOL = None) -> None:
        """
        Initialize the AbstractSourceQuery class
        """
        super().__init__(
            source, where_clause=where_clause, xy_tolerance=xy_tolerance)
        self._target: FeatureClass = target
    # End init built-in

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        return validate_fields(self.source, fields=self.source.fields)
    # End _get_unique_fields method

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type based on Output Type Option and Source Shape Type
        """
        return self.source.shape_type
    # End _get_target_shape_type method

    def _create_feature_class(self, shape_type: str,
                              has_zm: HasZM) -> FeatureClass:
        """
        Create Feature Class
        """
        # noinspection PyTypeChecker
        return create_feature_class(
            geopackage=self._target.geopackage, name=self._target.name,
            shape_type=shape_type, fields=self._get_unique_fields(),
            srs=self.spatial_reference_system,
            z_enabled=has_zm.has_z, m_enabled=has_zm.has_m)
    # End _create_feature_class method

    @property
    def _has_zm(self) -> HasZM:
        """
        Has ZM
        """
        return HasZM(has_z=self.source.has_z, has_m=self.source.has_m)
    # End _has_zm property

    def _make_full_query(self, element: FeatureClass) -> str:
        """
        Make Full Query, return all features
        """
        where = self._get_extent_where(element) or SQL_ALL_ID
        *_, field_names = self._field_names_and_count(element)
        return self._make_select(
            element, field_names=field_names, where_clause=where)
    # End _make_full_query method

    def _shared_extent(self, element: FeatureClass) -> EXTENT:
        """
        Shared Extent between source and operator
        """
        if not (extent := ANALYSIS_SETTINGS.extent):
            return self.source_extent
        polygon = self._get_extent_polygon(extent, crs=self.source_crs)
        # noinspection PyTypeChecker
        polygon: 'Polygon' = polygon.intersection(box(*self.source_extent))
        return polygon.bounds
    # End _shared_extent method

    def _make_disjoint_select(self, element: FeatureClass) -> str:
        """
        Make Disjoint Select Statement using the input Element
        and accounting for the analysis extent
        """
        extent_where = self._get_extent_where(element)
        *_, field_names = self._field_names_and_count(element)
        if not self.has_intersection:
            return self._make_select(
                element, field_names=field_names,
                where_clause=extent_where or SQL_ALL_ID)
        if not (where := self._spatial_index_where(
                element, extent=self._shared_extent(element))):  # pragma: no cover
            return extent_where or SQL_ALL_ID
        where = where.format(NOT_IN)
        if extent_where:
            where = f'({where}) AND ({extent_where})'
        return self._make_select(
            element, field_names=field_names, where_clause=where)
    # End _make_disjoint_select method

    def _get_extent_where(self, element: FeatureClass) -> str:
        """
        Get where clause that accounts for the analysis extent

        In this implementation it is always empty since we have the analysis
        extent already accounted for in the shared extent method.
        """
        return EMPTY
    # End _get_extent_where method

    def _make_intersection_query(self, element: FeatureClass, field_names: str,
                                 where_clause: str = EMPTY) -> str:
        """
        Make Intersection Query
        """
        extent_where = self._get_extent_where(element)
        if not self.has_intersection:
            return self._make_select(
                element, field_names=field_names, where_clause=SQL_NO_ID)
        if where := self._spatial_index_where(
                element, extent=self._shared_extent(element)):
            clauses = extent_where, where.format(IN), where_clause
        else:  # pragma: no cover
            clauses = extent_where, where_clause or SQL_ALL_ID
        where = ' AND '.join(f'({w})' for w in clauses if w)
        return self._make_select(
            element, field_names=field_names, where_clause=where)
    # End _make_intersection_query method

    def _build_select(self, fields: FIELDS) -> str:
        """
        Build Select from a list of fields
        """
        where_clause = self._get_where_clause()
        select_names = self._get_select_names(fields)
        if ANALYSIS_SETTINGS.extent:
            return self._make_intersection_query(
                self.source, field_names=select_names,
                where_clause=where_clause)
        return self._make_select(
            self.source, field_names=select_names, where_clause=where_clause)
    # End _build_select method

    def _get_select_names(self, fields: FIELDS) -> str:
        """
        Get Select Names
        """
        select_names = make_field_names(fields)
        try:
            geom_type = get_geometry_column_name(
                self.source, include_geom_type=True)
        except AttributeError:
            pass
        else:
            select_names = self._concatenate(geom_type, select_names)
        return select_names
    # End _get_select_names method

    @cached_property
    def has_intersection(self) -> bool:
        """
        Has Intersection between source and operator
        """
        if not (extent := ANALYSIS_SETTINGS.extent):
            return True
        polygon = self._get_extent_polygon(extent, crs=self.source_crs)
        # noinspection PyTypeChecker
        return bool(polygon.intersects(box(*self.source_extent)))
    # End has_intersection property

    @cached_property
    def zm_config(self) -> 'ZMConfig':
        """
        ZM Configuration
        """
        return zm_config(self.source)
    # End zm_config property

    @cached_property
    def geometry_config(self) -> 'GeometryConfig':
        """
        Geometry Configuration
        """
        return geometry_config(
            self.target, cast_geom=self.zm_config.is_different)
    # End geometry_config property

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        return self.select_intersect
    # End select property

    @property
    def select_intersect(self) -> str:
        """
        Selection query for intersection
        """
        elm = self.source
        *_, field_names = self._field_names_and_count(elm)
        return self._make_intersection_query(
            elm, field_names=field_names,
            where_clause=self._get_where_clause())
    # End select_intersect property

    @property
    def select_with_fid(self) -> str:
        """
        Select from Source including FID
        """
        fields = validate_fields(self.source, fields=self.source.fields)
        # noinspection PyTypeChecker
        return self._build_select([self.source.primary_key_field, *fields])
    # End select_with_fid property

    @property
    def select_only_fid(self) -> str:
        """
        Select from Source using only the FID for attributes
        """
        # noinspection PyTypeChecker
        return self._build_select([self.source.primary_key_field])
    # End select_only_fid property

    @property
    def select_source(self) -> str:
        """
        Selection Query for Source
        """
        return self.select
    # End select_source property

    @cached_property
    def source_extent(self) -> EXTENT:
        """
        Source Extent
        """
        return extent_from_feature_class(self.source)
    # End source_extent property

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
        Target Empty
        """
        shape_type = self._get_target_shape_type()
        return self._create_feature_class(shape_type, has_zm=self._has_zm)
    # End target_empty property

    @cached_property
    def target_full(self) -> FeatureClass:
        """
        Full Copy of the Source Feature Class
        """
        return copy_feature_class(
            self.source, target=self._target, where_clause=SQL_ALL_ID,
            zm=self.zm_config)
    # End target_full property
# End AbstractSourceQuery class


class AbstractSourceUpdateQuery(IntermediateTableContextMixin,
                                AbstractSourceQuery):
    """
    Abstract Source Update Query
    """
    def __init__(self, source: FeatureClass, where_clause: str = EMPTY,
                 xy_tolerance: XY_TOL = None) -> None:
        """
        Initialize the AbstractSourceQuery class
        """
        super().__init__(source, target=source, where_clause=where_clause,
                         xy_tolerance=xy_tolerance)
    # End init built-in

    @property
    @abstractmethod
    def _short_name(self) -> str:
        """
        Short Name
        """
        pass
    # End _short_name property

    @abstractmethod
    def _prepare_source(self) -> None:
        """
        Source Preparation Steps
        """
        pass
    # End _prepare_source method

    @property
    @abstractmethod
    def _intermediate_fields(self) -> FIELDS:
        """
        Intermediate Fields
        """
        pass
    # End _intermediate_fields property

    @staticmethod
    def _make_update_from(element_name: str, key_name: str, field_names: NAMES,
                          from_name: str, from_key_name: str,
                          from_field_names: NAMES) -> str:
        """
        Make SQL statement for Update
        """
        sets = [f'{fn} = {from_name}{DOT}{ffn}'
                for fn, ffn in zip(field_names, from_field_names)]
        return f"""
            UPDATE {element_name} 
            SET {COMMA_SPACE.join(sets)} 
            FROM {from_name}
            WHERE {element_name}{DOT}{key_name} = {from_name}{DOT}{from_key_name}
        """
    # End _make_update_from method

    @abstractmethod
    def _get_field_names(self) -> NAMES:
        """
        Get Field Names
        """
        pass
    # End _get_field_names method

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
        # noinspection PyUnresolvedReferences
        key_name = self.source.primary_key_field.escaped_name
        select_names = self._concatenate(geom_type, key_name)
        where_clause = self._get_where_clause()
        if ANALYSIS_SETTINGS.extent:
            return self._make_intersection_query(
                self.source, field_names=select_names,
                where_clause=where_clause)
        return self._make_select(
            self.source, field_names=select_names, where_clause=where_clause)
    # End select property

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
# End AbstractSourceUpdateQuery class


class AbstractSpatialQuery(OperatorMixin, AbstractSourceQuery,
                           metaclass=ABCMeta):
    """
    Abstract Spatial Query Support
    """
    def __init__(self, source: FeatureClass, target: FeatureClass | None,
                 operator: FeatureClass, *, xy_tolerance: XY_TOL,
                 where_clause: str = EMPTY) -> None:
        """
        Initialize the AbstractSpatialQuery class
        """
        # noinspection PyTypeChecker
        super().__init__(source, target=target, xy_tolerance=xy_tolerance,
                         where_clause=where_clause)
        self._operator: FeatureClass = operator
    # End init built-in
# End AbstractSpatialQuery class


class AbstractSpatialAttribute(AbstractSpatialQuery, metaclass=ABCMeta):
    """
    Abstract class extending with attribute options
    """
    def __init__(self, source: FeatureClass, target: FeatureClass | None,
                 operator: FeatureClass, attribute_option: AttributeOption, *,
                 xy_tolerance: XY_TOL, where_clause: str = EMPTY) -> None:
        """
        Initialize the AbstractSpatialAttribute class
        """
        super().__init__(source, target=target, operator=operator,
                         xy_tolerance=xy_tolerance, where_clause=where_clause)
        self._attr_option: AttributeOption = attribute_option
    # End init built-in

    @cache
    def _field_names_and_count(self, element: FeatureClass) -> tuple[int, str, str]:
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
        # noinspection PyTypeChecker
        return fields
    # End _get_fields method

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields and Rename Primary Key Columns if included
        """
        if self._attr_option == AttributeOption.ALL:
            src_fields = self._get_fields(self.source)[1:]
            op_fields = self._get_fields(self.operator)[1:]
            src_fields = [self.output_fid_source, *src_fields]
            op_fields = make_unique_fields(src_fields, op_fields)
            return [*src_fields, self.output_fid_operator, *op_fields]
        elif self._attr_option == AttributeOption.ONLY_FID:
            return self.output_fid_source, self.output_fid_operator
        else:
            src_fields = self._get_fields(self.source)
            op_fields = self._get_fields(self.operator)
            op_fields = make_unique_fields(src_fields, op_fields)
            return [*src_fields, *op_fields]
    # End _get_unique_fields method

    @staticmethod
    def _make_fid_field(field: 'Field', element: ELEMENT) -> 'Field':
        """
        Make FID Field
        """
        name = f'{field.name}{UNDERSCORE}{element.name}'
        return clone_field(field, name=name, allow_null=True)
    # End _make_fid_field method

    def _avoid_name_clash(self, field: 'Field') -> 'Field':
        """
        Avoid Name Clash with Source or Operator Fields
        """
        if self._attr_option != AttributeOption.ALL:
            return field
        # NOTE use slice (not unpacking) to avoid ValueError if no fields
        src_fields = self._get_fields(self.source)
        op_fields = self._get_fields(self.operator)
        fields = [*src_fields, *op_fields]
        field, = make_unique_fields(fields, [field])
        return field
    # End _avoid_name_clash method

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
    def input_fid_source(self) -> 'Field':
        """
        Input FID for Source
        """
        # noinspection PyTypeChecker
        return self.source.primary_key_field
    # End input_fid_source property

    @property
    def input_fid_operator(self) -> 'Field':
        """
        Input FID for Operator
        """
        # noinspection PyTypeChecker
        return self.operator.primary_key_field
    # End input_fid_operator property

    @cached_property
    def output_fid_source(self) -> 'Field':
        """
        Output FID for Source
        """
        field = self._make_fid_field(self.input_fid_source, self.source)
        return self._avoid_name_clash(field)
    # End output_fid_source property

    @cached_property
    def output_fid_operator(self) -> 'Field':
        """
        Output FID for Operator
        """
        source = self.output_fid_source
        names = {source.name.casefold()}
        field = self._make_fid_field(self.input_fid_operator, self.operator)
        field.name = make_unique_name(field.name, names=names)
        return self._avoid_name_clash(field)
    # End output_fid_operator property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        return self._build_insert(self.target, fields=self._get_unique_fields())
    # End insert property
# End AbstractSpatialAttribute class


class BaseQuerySelect(AbstractSourceQuery):
    """
    Base Query for Simple Selection that honors Analysis Extent
    """
    def __init__(self, source: FeatureClass, target: ELEMENT,
                 where_clause: str = EMPTY,
                 xy_tolerance: XY_TOL = None) -> None:
        """
        Initialize the BaseQuerySelect class
        """
        # noinspection PyTypeChecker
        super().__init__(source, target=target, xy_tolerance=xy_tolerance)
        self._where_clause: str = where_clause
    # End init built-in

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        elm = self.source
        *_, select_field_names = self._field_names_and_count(elm)
        where_clause = self._get_where_clause()
        if ANALYSIS_SETTINGS.extent:
            return self._make_intersection_query(
                elm, field_names=select_field_names, where_clause=where_clause)
        return self._make_select(
            elm, field_names=select_field_names, where_clause=where_clause)
    # End select property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self.target
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property
# End BaseQuerySelect class


class BaseQuerySelectOrderBy(BaseQuerySelect):
    """
    Base Query Select Order By
    """
    def __init__(self, source: FeatureClass, target: ELEMENT,
                 where_clause: str = EMPTY, sort_fields: SORT_FIELDS = (),
                 xy_tolerance: XY_TOL = None) -> None:
        """
        Initialize the BaseQuerySelectOrderBy class
        """
        super().__init__(source, target=target, where_clause=where_clause,
                         xy_tolerance=xy_tolerance)
        self._sort_fields: SORT_FIELDS = sort_fields
    # End init built-in

    def _add_order_by(self, sql: str) -> str:
        """
        Add Order By
        """
        if not self._sort_fields:
            return sql
        sorts = COMMA_SPACE.join([f'{field!r}' for field in self._sort_fields])
        return f'{sql} ORDER BY {sorts}'
    # End _add_order_by method

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        sql = super().select
        return self._add_order_by(sql)
    # End select property
# End BaseQuerySelectOrderBy class


class AbstractQueryGroup(GroupQueryMixin, AbstractSourceQuery,
                         metaclass=ABCMeta):
    """
    Abstract Query Group
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass', *,
                 fields: FIELDS, xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractQueryGroup class
        """
        super().__init__(source, target=target, xy_tolerance=xy_tolerance)
        self._fields: FIELDS = fields
        self._group_names: str = make_field_names(fields)
    # End init built-in

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self.target
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property

    @cached_property
    def group_count(self) -> int:
        """
        Group Count
        """
        elm = self.source
        index_where = self._spatial_index_where(elm)
        with elm.geopackage.connection as cin:
            cursor = cin.execute(f"""
                SELECT COUNT(*) AS CNT 
                FROM (SELECT DISTINCT {self._group_names} 
                      FROM {elm.escaped_name} {index_where})
            """)
            count, = cursor.fetchone()
        return count
    # End group_count property

    @property
    @abstractmethod
    def select_geometry(self) -> str:
        """
        Select Geometry
        """
        pass
    # End select_geometry property
# End AbstractQueryGroup class


class AbstractQueryDissolve(AbstractQueryGroup):
    """
    Abstract Query Dissolve
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass', *,
                 fields: FIELDS, as_multi_part: bool,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractQueryDissolve class
        """
        super().__init__(source, target=target, fields=fields,
                         xy_tolerance=xy_tolerance)
        self._as_multi_part: bool = as_multi_part
    # End init built-in

    @abstractmethod
    def dissolved_geometries(self) \
            -> Generator[dict[int, 'BaseMultipartGeometry'], None, None]:
        """
        Dissolved Geometries stored as a dictionary of Dense Rank IDs
        and Multi-Part Geometries.  Page over the number of groups to
        avoid loading all geometries into memory at once.

        This method builds up a dictionary of geometries and yields it when it
        reaches (or exceeds) fetch size.  There is an expectation that when a
        geometry is stitched together with its aggregate row that the geometry
        will be popped from the dictionary.
        """
        pass
    # End dissolved_geometries method
# End AbstractQueryDissolve class


class QueryFeatureIntermediate(BaseQuerySelect):
    """
    Query for each input for use into an intermediate feature class
    """
    def __init__(self, source: FeatureClass, target: FeatureClass | None,
                 xy_tolerance: XY_TOL = None) -> None:
        """
        Initialize the QueryFeatureIntermediate class
        """
        # noinspection PyTypeChecker
        super().__init__(source, target=target, xy_tolerance=xy_tolerance)
    # End init built-in

    @cache
    def _field_names_and_count(self, element: FeatureClass) -> tuple[int, str, str]:
        """
        Limit fields to just geometry
        """
        insert_names = self._concatenate(
            get_geometry_column_name(element), ORIG_FID.name)
        select_names = self._concatenate(
            get_geometry_column_name(element, include_geom_type=True),
            element.primary_key_field.name)
        return 2, insert_names, select_names
    # End _field_names_and_count method

    def _get_unique_fields(self) -> FIELDS:
        """
        Limit fields to just geometry, sans attributes
        """
        return [ORIG_FID]
    # End _get_unique_fields method
# End QueryFeatureIntermediate class


class AbstractQueryFeatureClasses(AbstractSourceQuery):
    """
    Abstract Query Feature Classes
    """
    def __init__(self, source: FEATURE_CLASSES, target: FeatureClass,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractQueryFeatureClasses class
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

    def _get_lines(self, scratch: 'MemoryGeoPackage') \
            -> tuple[list, list[QueryFeatureIntermediate], GRID_SIZE]:
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
                query = QueryFeatureIntermediate(
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
    def _fetch_lines_sizes(query: QueryFeatureIntermediate,
                           lines: list['LineString'],
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
# End AbstractQueryFeatureClasses class


class AbstractQueryFeatureClassesPolygon(AbstractQueryFeatureClasses):
    """
    Abstract Query Feature Classes Polygon
    """
    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.polygon
    # End _get_target_shape_type method

    @staticmethod
    def _close_scratch(scratch: MemoryGeoPackage) -> None:
        """
        Close Scratch GeoPackage
        """
        if conn := scratch.connection:
            conn.close()
    # End _close_scratch method

    def build_features(self) -> list[tuple['Polygon', tuple]]:
        """
        Polygonized Features
        """
        scratch = MemoryGeoPackage.create()
        lines, queries, _ = self._get_lines(scratch)
        if not len(lines):
            self._close_scratch(scratch)
            return []
        if not (polygons := self._build_polygons(lines)):
            self._close_scratch(scratch)
            return []
        results = self._add_attributes(polygons, queries)
        self._close_scratch(scratch)
        return results
    # End build_features method

    @abstractmethod
    def _add_attributes(self, polygons: list['Polygon'],
                        queries: list[QueryFeatureIntermediate]) \
            -> list[tuple['Polygon', tuple]]:
        """
        Add Attributes, keeping all matches between label points and planarized
        """
        pass
    # End _add_attributes method

    @staticmethod
    def _index_overlay(tree: 'STRtree', geoms: list) \
            -> defaultdict[int, list[int]]:
        """
        Build cross-reference between planarized polygons and other geometries
        """
        intersects = tree.query(geoms, predicate='intersects')
        grouper = defaultdict(list)
        for pnt_idx, poly_idx in intersects.T.tolist():
            grouper[poly_idx].append(pnt_idx)
        return grouper
    # End _index_overlay method

    @staticmethod
    def _build_polygons(lines: list['LineString']) -> list['Polygon']:
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

    @abstractmethod
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        pass
    # End _get_unique_fields method

    @abstractmethod
    def _get_geoms_attributes(self) -> tuple[list, list[tuple]]:
        """
        Get Geometries and Attributes
        """
        pass
    # End _get_geoms_attributes method
# End AbstractQueryFeatureClassesPolygon class


if __name__ == '__main__':  # pragma: no cover
    pass
