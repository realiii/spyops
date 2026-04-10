# -*- coding: utf-8 -*-
"""
Abstract Classes in support of Query objects
"""


from abc import ABCMeta, abstractmethod
from datetime import datetime
from functools import cache, cached_property
from typing import Callable, Generator, Optional, Self, TYPE_CHECKING
from warnings import warn

from fudgeo import FeatureClass, Table
from fudgeo.constant import COMMA_SPACE
from fudgeo.util import escape_name
from numpy import isfinite
from pyproj import CRS
from shapely.creation import box
from shapely.ops import transform

from spyops.crs.transform import (
    get_transform_best_guess, make_transformer_function)
from spyops.crs.util import (
    crs_from_srs, get_crs_from_source, srs_from_crs)
from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.core import HasZM, zm_config
from spyops.environment.util import get_geographic_transformation, get_grid_size
from spyops.geometry.config import geometry_config
from spyops.geometry.extent import extent_from_feature_class
from spyops.shared.constant import (
    DOT, DRID, EMPTY, QUESTION, SKIP_FILE_PREFIXES, UNDERSCORE)
from spyops.shared.element import copy_feature_class, create_feature_class
from spyops.shared.enumeration import AttributeOption
from spyops.shared.exception import BadExtentWarning
from spyops.shared.field import (
    clone_field, get_geometry_column_name, make_field_names, make_unique_fields,
    validate_fields)
from spyops.shared.hint import ELEMENT, EXTENT, FIELDS, GRID_SIZE, NAMES, XY_TOL
from spyops.shared.sql import IN, NOT_IN, SQL_ALL_ID, SQL_NO_ID, TEMP_SCHEMA
from spyops.shared.util import make_unique_name


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Field, SpatialReferenceSystem
    from pyproj.transformer import Transformer
    from shapely import Polygon
    from shapely.geometry.base import BaseMultipartGeometry
    from spyops.environment.base import Extent
    from spyops.environment.core import ZMConfig
    from spyops.geometry.config import GeometryConfig


class AbstractQuery(metaclass=ABCMeta):
    """
    Base Query Support
    """
    def __init__(self, element: ELEMENT, *, xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractQuery class
        """
        super().__init__()
        self._element: ELEMENT = element
        self._xy_tolerance: XY_TOL = xy_tolerance
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
            polygon = transform(transformer.transform, polygon)
            if not isfinite(polygon.bounds).all():
                warn('Bad extent polygon after transformation, '
                     'extent will be ignored', category=BadExtentWarning,
                     skip_file_prefixes=SKIP_FILE_PREFIXES)
        return polygon
    # End _get_extent_polygon method

    def _spatial_index_where(self, element: FeatureClass,
                             extent: EXTENT) -> str:
        """
        Make a where clause stub that can be used to select features which
        intersect an extent. The query is based on a spatial index (if present).
        """
        primary = element.primary_key_field
        if not element.has_spatial_index or not primary:  # pragma: no cover
            return EMPTY
        if not isfinite(extent).all():
            return EMPTY
        min_x, min_y, max_x, max_y = extent
        return f"""{primary.escaped_name} {{}} (
            SELECT id  
            FROM {element.spatial_index_name} 
            WHERE minx <= {max_x} AND maxx >= {min_x} AND 
                  miny <= {max_y} AND maxy >= {min_y})
        """
    # End _spatial_index_where function

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


class GroupQueryMixin:
    """
    Group Query Mixin
    """
    # noinspection PyUnusedLocal
    def _spatial_index_where(self, element: ELEMENT, extent: EXTENT) -> str:
        """
        Make a where clause stub that can be used to select features which
        intersect an extent. The query is based on a spatial index (if present).
        """
        if not isinstance(element, FeatureClass):
            return EMPTY
        if not (extent := ANALYSIS_SETTINGS.extent):
            return EMPTY
        # noinspection PyUnresolvedReferences
        polygon = self._get_extent_polygon(
            extent, crs=crs_from_srs(element.spatial_reference_system))
        # noinspection PyProtectedMember,PyUnresolvedReferences
        if index_where := super()._spatial_index_where(
                element, extent=polygon.bounds):
            index_where = f'WHERE ({index_where.format(IN)})'
        return index_where
    # End _spatial_index_where function
# End GroupQueryMixin class


class AbstractGroupQuery(GroupQueryMixin, AbstractQuery, metaclass=ABCMeta):
    """
    Abstract Group Query
    """
    def __init__(self, element: ELEMENT, fields: FIELDS, *,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractGroupQuery class
        """
        super().__init__(element, xy_tolerance=xy_tolerance)
        self._fields: FIELDS = fields
        self._group_names: str = make_field_names(fields)
    # End init built-in

    def _build_spatial_rank(self, element: ELEMENT) -> str:
        """
        Build Spatial Rank
        """
        primary = element.primary_key_field.escaped_name
        # NOTE this extent not used, simply filling a required argument
        index_where = self._spatial_index_where(element, extent=(0, 0, 0, 0))
        # noinspection PyUnresolvedReferences
        return f"""
            {primary} IN (SELECT {primary}
            FROM (SELECT {primary}, 
                         dense_rank() OVER (ORDER BY {self._group_names}) AS {DRID} 
                  FROM {element.escaped_name} {index_where})
            WHERE {DRID} = ?) 
        """
    # End _build_spatial_rank method
# End AbstractGroupQuery class


class AbstractSourceQuery(AbstractQuery, metaclass=ABCMeta):
    """
    Abstract Source Query
    """
    def __init__(self, source: FeatureClass, target: FeatureClass, *,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractSourceQuery class
        """
        super().__init__(source, xy_tolerance=xy_tolerance)
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
        return polygon.intersection(box(*self.source_extent, ccw=False)).bounds
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

    @cached_property
    def has_intersection(self) -> bool:
        """
        Has Intersection between source and operator
        """
        if not (extent := ANALYSIS_SETTINGS.extent):
            return True
        polygon = self._get_extent_polygon(extent, crs=self.source_crs)
        return polygon.intersects(box(*self.source_extent))
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
        return self._make_intersection_query(elm, field_names=field_names)
    # End select_intersect property

    @property
    def select_with_fid(self) -> str:
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
    # End select_with_fid property

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


class AbstractSourceUpdateQuery(AbstractSourceQuery):
    """
    Abstract Source Update Query
    """
    def __init__(self, source: FeatureClass) -> None:
        """
        Initialize the AbstractSourceQuery class
        """
        super().__init__(source, target=source, xy_tolerance=None)
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

    def _delete_intermediate(self) -> None:
        """
        Delete Intermediate
        """
        name = self._intermediate_name
        with self.source.geopackage.connection as cin:
            cin.execute(f"""DROP TABLE IF EXISTS {TEMP_SCHEMA}{DOT}{name}""")
    # End _delete_intermediate method

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
        return escape_name(f'tmp_{self.source.name}_{self._short_name}_{now}')
    # End _intermediate_name property

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
        select_names = self._concatenate(
            geom_type, self.source.primary_key_field.escaped_name)
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
# End AbstractSourceUpdateQuery class


class AbstractSpatialQuery(AbstractSourceQuery, metaclass=ABCMeta):
    """
    Abstract Spatial Query Support
    """
    def __init__(self, source: FeatureClass, target: FeatureClass | None,
                 operator: FeatureClass, *, xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractSpatialQuery class
        """
        super().__init__(source, target=target, xy_tolerance=xy_tolerance)
        self._operator: FeatureClass = operator
    # End init built-in

    @property
    def _has_zm(self) -> HasZM:
        """
        Has ZM
        """
        has_z = self.source.has_z or self.operator.has_z
        has_m = self.source.has_m or self.operator.has_m
        return HasZM(has_z=has_z, has_m=has_m)
    # End _has_zm property

    def _shared_extent(self, element: FeatureClass) -> EXTENT:
        """
        Shared Extent between source and operator
        """
        source_box = box(*self.source_extent)
        operator_box = box(*self.operator_extent)
        if element is self.source:
            transformer = self._get_transformer_or_guess(
                from_crs=self.operator_crs, to_crs=self.source_crs)
            if transformer:
                operator_box = transform(transformer.transform, operator_box)
        else:
            transformer = self._get_transformer_or_guess(
                from_crs=self.source_crs, to_crs=self.operator_crs)
            if transformer:
                source_box = transform(transformer.transform, source_box)
        return operator_box.intersection(source_box).bounds
    # End _shared_extent method

    def _get_extent_where(self, element: FeatureClass) -> str:
        """
        Get where clause that accounts for the analysis extent
        """
        if not (extent := ANALYSIS_SETTINGS.extent):
            return EMPTY
        if element is self.source:
            crs = self.source_crs
        else:
            crs = self.operator_crs
        polygon = self._get_extent_polygon(extent, crs=crs)
        return self._spatial_index_where(
            element, extent=polygon.bounds).format(IN)
    # End _get_extent_where method

    @cached_property
    def has_intersection(self) -> bool:
        """
        Has Intersection between source and operator
        """
        transformer = self._get_transformer_or_guess(
            from_crs=self.operator_crs, to_crs=self.source_crs)
        # noinspection PyTypeChecker
        operator_box: 'Polygon' = box(*self.operator_extent)
        if transformer:
            operator_box = transform(transformer.transform, operator_box)
        # noinspection PyTypeChecker
        return operator_box.intersects(box(*self.source_extent))
    # End has_intersection property

    @cached_property
    def zm_config(self) -> 'ZMConfig':
        """
        ZM Configuration
        """
        return zm_config(self.source, self.operator)
    # End zm_config property

    @property
    def select_operator(self) -> str:
        """
        Selection Query for Operator
        """
        elm = self.operator
        *_, field_names = self._field_names_and_count(elm)
        return self._make_intersection_query(elm, field_names=field_names)
    # End select_operator property

    @property
    def select_disjoint(self) -> str:
        """
        Selection query for disjoint
        """
        return self._make_disjoint_select(self.source)
    # End select_disjoint property

    @property
    def operator(self) -> FeatureClass:
        """
        Operator
        """
        return self._operator
    # End operator property

    @cached_property
    def operator_crs(self) -> CRS:
        """
        Operator CRS
        """
        return get_crs_from_source(self.operator)
    # End operator_crs property

    @cached_property
    def operator_extent(self) -> EXTENT:
        """
        Operator Extent
        """
        return extent_from_feature_class(self.operator)
    # End operator_extent property

    @cached_property
    def operator_transformer(self) -> Callable | None:
        """
        Operator Transformer
        """
        elm = self.operator
        transformer = self._get_transformer(elm)
        return make_transformer_function(
            elm.shape_type, has_z=elm.has_z, has_m=elm.has_m,
            transformer=transformer)
    # End operator_transformer property
# End AbstractSpatialQuery class


class AbstractSpatialAttribute(AbstractSpatialQuery, metaclass=ABCMeta):
    """
    Abstract class extending with attribute options
    """
    def __init__(self, source: FeatureClass, target: FeatureClass | None,
                 operator: FeatureClass, attribute_option: AttributeOption, *,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractSpatialAttribute class
        """
        super().__init__(source, target=target, operator=operator,
                         xy_tolerance=xy_tolerance)
        self._attr_option: AttributeOption = attribute_option
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
        return self.source.primary_key_field
    # End input_fid_source property

    @property
    def input_fid_operator(self) -> 'Field':
        """
        Input FID for Operator
        """
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
    def __init__(self, source: FeatureClass, target: FeatureClass | Table,
                 where_clause: str = EMPTY,
                 xy_tolerance: XY_TOL = None) -> None:
        """
        Initialize the BaseQuerySelect class
        """
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
        where_clause = (self._where_clause or EMPTY).strip() or SQL_ALL_ID
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


class AbstractQueryDissolve(GroupQueryMixin, AbstractSourceQuery,
                            metaclass=ABCMeta):
    """
    Abstract Query Dissolve
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass', *,
                 fields: FIELDS, as_multi_part: bool,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QueryDissolve class
        """
        super().__init__(source, target=target, xy_tolerance=xy_tolerance)
        self._fields: FIELDS = fields
        self._as_multi_part: bool = as_multi_part
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
        index_where = self._spatial_index_where(elm, extent=(0, 0, 0, 0))
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

    @abstractmethod
    def dissolved_geometries(self) \
            -> Generator[dict[int, 'BaseMultipartGeometry'], None, None]:
        """
        Dissolved Geometries stored as a dictionary of Dense Range IDs
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


if __name__ == '__main__':  # pragma: no cover
    pass
