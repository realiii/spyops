# -*- coding: utf-8 -*-
"""
Mixins
"""


from collections import defaultdict
from datetime import datetime
from functools import cache, cached_property
from math import nan
from typing import Callable, Optional, Self, TYPE_CHECKING, Union

from bottleneck import nanmean
from fudgeo import FeatureClass, Field
from fudgeo.constant import COMMA_SPACE, FETCH_SIZE
from fudgeo.util import escape_name
from numpy import array, ones_like
from shapely.constructive import centroid
from shapely.coordinates import get_coordinates, transform
from shapely.creation import box

from spyops.crs.transform import make_transformer_function
from spyops.crs.unit import (
    DecimalDegrees, LinearUnit, degrees_to_meters,
    get_linear_unit_conversion_factor, get_unit_name, unit_factory)
from spyops.crs.util import crs_from_srs, get_crs_from_source
from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.core import HasZM, zm_config
from spyops.geometry.enumeration import DimensionOption
from spyops.geometry.extent import extent_from_feature_class
from spyops.geometry.util import filter_features, to_shapely
from spyops.shared.constant import DOT, DRID, EMPTY, METRE, SEMI

from spyops.shared.database import add_aggregates, remove_aggregates
from spyops.shared.field import (
    FC_COUNT, FEAT_COUNT, NUMBERS, ORIG_FID, ORIG_NAME, OVERLAP_FID,
    TYPE_ALIAS_LUT, make_field_names, make_unique_fields)
from spyops.shared.hint import (
    ELEMENT, EXTENT, FIELDS, GRID_SIZE, STATS_FIELDS, UNIT)
from spyops.shared.keywords import METERS_ATTR, VALUE_ATTR
from spyops.shared.sql import IN, TEMP_SCHEMA


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Table
    from numpy import ndarray
    from pyproj import CRS
    from shapely import Polygon
    from shapely.geometry.base import BaseGeometry
    from shapely.strtree import STRtree
    from spyops.environment.core import ZMConfig
    from spyops.query.base import QueryFeatureIntermediate


class AggregateContextMixin:
    """
    Aggregate Context Mixin
    """
    def __enter__(self) -> Self:
        """
        Context Manager Enter
        """
        # noinspection unresolved-references
        add_aggregates(self.source.geopackage.connection)
        return self
    # End enter built-in

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Context Manager Exit
        """
        # noinspection unresolved-references
        remove_aggregates(self.source.geopackage.connection)
        return False
    # End exit built-in
# End AggregateContextMixin class


class StatisticsMixin(AggregateContextMixin):
    """
    Statistics Mixin
    """
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        # noinspection unresolved-references
        fields = self._fields
        stat_fields = [stat.output_field for stat in self.statistics]
        stat_fields = make_unique_fields(fields, stat_fields)
        return [*fields, *stat_fields]
    # End _get_unique_fields method

    @cached_property
    def statistics(self) -> STATS_FIELDS:
        """
        Statistics with repeated output names removed
        """
        keepers = []
        names = set()
        # noinspection unresolved-references
        for stat in self._statistics:
            name = stat.output_name.casefold()
            if name in names:
                continue
            names.add(name)
            keepers.append(stat)
        return keepers
    # End statistics property
# End StatisticsMixin class


class GroupQueryMixin:
    """
    Group Query Mixin
    """
    # noinspection unused-parameter
    def _spatial_index_where(self, element: ELEMENT,
                             extent: EXTENT = (0, 0, 0, 0)) -> str:
        """
        Make a where clause stub that can be used to select features which
        intersect an extent. The query is based on a spatial index (if present).
        """
        if not isinstance(element, FeatureClass):
            return EMPTY
        # noinspection bad-argument-type
        if not (extent := ANALYSIS_SETTINGS.extent):
            return EMPTY
        # noinspection unresolved-references
        polygon = self._get_extent_polygon(
            extent, crs=crs_from_srs(element.spatial_reference_system))
        # noinspection protected-member,unresolved-references
        if index_where := super()._spatial_index_where(
                element, extent=polygon.bounds):
            index_where = f'WHERE ({index_where.format(IN)})'
        return index_where
    # End _spatial_index_where function

    def _build_spatial_rank(self, element: ELEMENT) -> str:
        """
        Build Spatial Rank
        """
        # noinspection unresolved-references
        primary = element.primary_key_field.escaped_name
        index_where = self._spatial_index_where(element)
        # noinspection unresolved-references
        return f"""
            {primary} IN (SELECT {primary}
            FROM (SELECT {primary}, 
                         dense_rank() OVER (ORDER BY {self._group_names}) AS {DRID} 
                  FROM {element.escaped_name} {index_where})
            WHERE {DRID} = ?) 
        """
    # End _build_spatial_rank method
# End GroupQueryMixin class


class IntermediateTableContextMixin:
    """
    Intermediate Table Mixin
    """
    def __enter__(self) -> Self:
        """
        Context Manager Enter
        """
        # noinspection unresolved-references
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
        # noinspection unresolved-references
        with self.source.geopackage.connection as cin:
            cin.execute(f"""DROP TABLE IF EXISTS {TEMP_SCHEMA}{DOT}{name}""")
    # End _delete_intermediate method

    @cached_property
    def _intermediate_table(self) -> str:
        """
        Intermediate Table
        """
        name = self._intermediate_name
        # noinspection unresolved-references
        defs = COMMA_SPACE.join(repr(f) for f in self._intermediate_fields)
        # noinspection unresolved-references
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
        # noinspection unresolved-references
        return escape_name(f'tmp_{self.source.name}_{self._short_name}_{now}')
    # End _intermediate_name property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        # noinspection unresolved-references
        return self._make_insert(
            self._intermediate_table,
            field_names=make_field_names(self._intermediate_fields),
            field_count=len(self._intermediate_fields))
    # End insert property
# End IntermediateTableContextMixin class


class UnitTypeMixin:
    """
    Unit Type Mixin
    """
    def _convert_unit(self, is_geodesic: bool, crs: 'CRS',
                      geoms: Union[list, 'ndarray'], unit: UNIT,
                      broadcast: bool = True) -> Union['ndarray', float]:
        """
        Convert Unit
        """
        if is_geodesic:
            if isinstance(unit, LinearUnit):
                value = unit.meters
            else:
                coordinates = get_coordinates(centroid(geoms))
                # noinspection bad-argument-type
                values = degrees_to_meters(
                    crs, coordinates=coordinates, value=unit.value)
                if not broadcast:
                    return nanmean(values)
                return values
        else:
            if isinstance(unit, LinearUnit):
                value = unit.meters
                # NOTE return in units of the CRS
                # noinspection argument-list,unresolved-references
                value *= self._get_conversion_factor(crs)
            else:
                value = unit.value
        if not broadcast:
            # noinspection bad-return
            return value
        return ones_like(geoms, dtype=float) * value
    # End _convert_unit method

    def _convert_units(self, is_geodesic: bool, crs: 'CRS', geoms: 'ndarray',
                       units: list[UNIT | None]) -> 'ndarray':
        """
        Convert Units
        """
        meters = array([getattr(unit, METERS_ATTR, nan)
                        for unit in units], dtype=float)
        if is_geodesic:
            degrees = [(i, unit.value) for i, unit in enumerate(units)
                       if isinstance(unit, DecimalDegrees)]
            if not degrees:
                return meters
            ids, values = zip(*degrees)
            ids = array(ids, dtype=int)
            coordinates = get_coordinates(centroid(geoms[ids]))
            meters[ids] = degrees_to_meters(
                crs, coordinates=coordinates,
                value=array(values, dtype=float))
            return meters
        else:
            # NOTE planar buffer type only occurs when there is no mixture of
            #  units which means fully linear or fully angular
            has_linear, _ = self._unit_types
            if has_linear:
                # NOTE return in units of the CRS
                # noinspection argument-list
                return meters * self._get_conversion_factor(crs)
            else:
                # NOTE this will be in decimal degrees
                return array([getattr(unit, VALUE_ATTR, nan)
                              for unit in units], dtype=float)
    # End _convert_units method

    @cache
    def _get_conversion_factor(self, crs: 'CRS',
                               use_horizontal: bool = True) -> float:
        """
        Get Conversion Factor
        """
        if not (unit_name := get_unit_name(crs, use_horizontal=use_horizontal)):
            return 1.
        return get_linear_unit_conversion_factor(
            from_name=METRE, to_name=unit_name)
    # End _get_conversion_factor method

    @property
    def _is_distance_from_field(self) -> bool:
        """
        Is Distance from Field?
        """
        # noinspection unresolved-references
        return isinstance(self._config.distance, Field)
    # End _is_distance_from_field property

    @cached_property
    def _is_numeric_field(self) -> bool:
        """
        Is Numeric Field
        """
        if not self._is_distance_from_field:
            return False
        aliases = set(NUMBERS)
        for data_type in NUMBERS:
            aliases.update(TYPE_ALIAS_LUT[data_type])
        aliases = tuple(a.casefold() for a in aliases)
        # noinspection unresolved-references
        return self._config.distance.data_type.casefold().startswith(aliases)
    # End _is_numeric_field property

    @cached_property
    def _unit_types(self) -> tuple[bool, bool]:
        """
        Check for Linear and Angular Units, return tuple of truth
        """
        # noinspection unresolved-references
        elm = self.source
        # noinspection unresolved-references
        distance = self._config.distance
        if not self._is_distance_from_field:
            is_linear = isinstance(distance, LinearUnit)
            return is_linear, not is_linear
        if self._is_numeric_field:
            # noinspection unresolved-references
            is_projected = self.source_crs.is_projected
            return is_projected, not is_projected
        distance: Field
        null_clause = f'{distance.escaped_name} IS NOT NULL'
        # noinspection unresolved-references
        if index_where := self._spatial_index_where(elm):
            where_clause = f'{index_where} AND {null_clause}'
            where_clause = where_clause.format(IN)
        else:
            where_clause = f'WHERE {null_clause}'
        has_linear = has_angular = False
        with elm.geopackage.connection as cin:
            cursor = cin.execute(f"""
                SELECT DISTINCT {distance.escaped_name}
                FROM {elm.escaped_name} {where_clause}
            """)
            while rows := cursor.fetchmany(FETCH_SIZE):
                units = sum([[unit_factory(v) for v in value.split(SEMI)]
                             for value, in rows], [])
                units = [unit for unit in units if unit]
                has_linear = has_linear or any(
                    isinstance(u, LinearUnit) for u in units)
                has_angular = has_angular or any(
                    isinstance(u, DecimalDegrees) for u in units)
                if has_linear and has_angular:
                    return has_linear, has_angular
        return has_linear, has_angular
    # End _unit_types property
# End UnitTypeMixin class


class DropEmptyMixin:
    """
    Drop Empty Mixin
    """
    @property
    def drop_empty(self) -> str:
        """
        Drop Empty Features from Source Feature Class
        """
        # noinspection unresolved-references
        name = self._intermediate_table
        # noinspection unresolved-references
        orig_fid, _ = self._intermediate_fields
        # noinspection unresolved-references
        key_name = self.source.primary_key_field.escaped_name
        # noinspection unresolved-references
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
        # noinspection unresolved-references
        name = self._intermediate_table
        # noinspection SqlWithoutWhere
        return f"""DELETE FROM {name}"""
    # End truncate method

    @property
    def insert_identifiers(self) -> str:
        """
        Insert Query for Identifiers
        """
        # noinspection unresolved-references
        orig_fid, _ = self._intermediate_fields
        fields = [orig_fid]
        # noinspection unresolved-references
        return self._make_insert(
            self._intermediate_table,
            field_names=make_field_names(fields), field_count=len(fields))
    # End insert_identifiers property
# End DropEmptyMixin class


class OperatorMixin:
    """
    Operator Mixin
    """
    @property
    def _has_zm(self) -> HasZM:
        """
        Has ZM
        """
        # noinspection unresolved-references
        has_z = self.source.has_z or self.operator.has_z
        # noinspection unresolved-references
        has_m = self.source.has_m or self.operator.has_m
        return HasZM(has_z=has_z, has_m=has_m)
    # End _has_zm property

    def _shared_extent(self, element: FeatureClass) -> EXTENT:
        """
        Shared Extent between source and operator
        """
        # noinspection unresolved-references
        source_box: 'Polygon' = box(*self.source_extent)
        # noinspection unresolved-references
        operator_box: 'Polygon' = box(*self.operator_extent)
        # noinspection unresolved-references
        if element is self.source:
            # noinspection unresolved-references
            transformer = self._get_transformer_or_guess(
                from_crs=self.operator_crs, to_crs=self.source_crs)
            if transformer:
                operator_box = transform(
                    operator_box, transformer.transform, interleaved=False)
        else:
            # noinspection unresolved-references
            transformer = self._get_transformer_or_guess(
                from_crs=self.source_crs, to_crs=self.operator_crs)
            if transformer:
                source_box = transform(
                    source_box, transformer.transform, interleaved=False)
        return operator_box.intersection(source_box).bounds
    # End _shared_extent method

    def _get_extent_where(self, element: FeatureClass) -> str:
        """
        Get where clause that accounts for the analysis extent
        """
        if not (extent := ANALYSIS_SETTINGS.extent):
            return EMPTY
        # noinspection unresolved-references
        if element is self.source:
            # noinspection unresolved-references
            crs = self.source_crs
        else:
            crs = self.operator_crs
        # noinspection unresolved-references
        polygon = self._get_extent_polygon(extent, crs=crs)
        # noinspection unresolved-references
        return self._spatial_index_where(
            element, extent=polygon.bounds).format(IN)
    # End _get_extent_where method

    @cached_property
    def has_intersection(self) -> bool:
        """
        Has Intersection between source and operator
        """
        # noinspection unresolved-references
        transformer = self._get_transformer_or_guess(
            from_crs=self.operator_crs, to_crs=self.source_crs)
        operator_box: 'Polygon' = box(*self.operator_extent)
        if transformer:
            operator_box = transform(
                operator_box, transformer.transform, interleaved=False)
        # noinspection unresolved-references
        return operator_box.intersects(box(*self.source_extent))
    # End has_intersection property

    @cached_property
    def zm_config(self) -> 'ZMConfig':
        """
        ZM Configuration
        """
        # noinspection unresolved-references
        return zm_config(self.source, self.operator)
    # End zm_config property

    @property
    def select_operator(self) -> str:
        """
        Selection Query for Operator
        """
        elm = self.operator
        # noinspection unresolved-references
        *_, field_names = self._field_names_and_count(elm)
        # noinspection unresolved-references
        return self._make_intersection_query(elm, field_names=field_names)
    # End select_operator property

    @property
    def select_disjoint(self) -> str:
        """
        Selection query for disjoint
        """
        # noinspection unresolved-references
        return self._make_disjoint_select(self.source)
    # End select_disjoint property

    @property
    def operator(self) -> FeatureClass:
        """
        Operator
        """
        # noinspection unresolved-references
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
        # noinspection unresolved-references
        transformer = self._get_transformer(elm)
        return make_transformer_function(
            elm.shape_type, has_z=elm.has_z, has_m=elm.has_m,
            transformer=transformer)
    # End operator_transformer property
# End OperatorMixin class


class CountOverlapMixin:
    """
    Count Overlap Mixin
    """
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        return FEAT_COUNT, FC_COUNT
    # End _get_unique_fields method

    def _build_attribute_groups(self, tree: 'STRtree',
                                queries: list['QueryFeatureIntermediate'],
                                grid_size: GRID_SIZE) \
            -> defaultdict[int, list[tuple]]:
        """
        Build Attributes Groups where key is planarized geometry index and
        values are the list of intersecting (fid, fc_name)
        """
        grouped = defaultdict(list)
        for query in queries:
            geoms, fids = self._get_geoms_attributes(query.target)
            if not geoms:
                continue
            # noinspection unresolved-references
            if not (grouper := self._index_overlay(tree, geoms, grid_size)):
                continue
            name = query.source.name
            attributes = [(fid, name) for fid in fids]
            for i, indexes in grouper.items():
                grouped[i].extend([attributes[idx] for idx in indexes])
        return grouped
    # End _build_attribute_groups method

    def _add_attributes(self, geometries: list,
                        queries: list[QueryFeatureIntermediate],
                        grid_size: GRID_SIZE) \
            -> list[tuple['BaseGeometry', tuple]]:
        """
        Add Attributes, keeping all matches between planarized geometries
        (using representative point) and source geometries.
        """
        # noinspection unresolved-references
        tree = self._make_tree(geometries)
        grouped = self._build_attribute_groups(tree, queries, grid_size)
        self._build_overlaps_table(grouped)
        return self._summarize_by_planarized(geometries, grouped)
    # End _add_attributes method

    def _summarize_by_planarized(self, geometries: list,
                                 grouped: defaultdict[int, list[tuple]]) \
            -> list[tuple['BaseGeometry', tuple]]:
        """
        Summarize grouped attributes on a per planarized geometry basis
        keeping only the geometries that have at least the minimum number of
        intersecting features.
        """
        results = []
        # noinspection unresolved-references
        threshold = self._min_count
        for i, geom in enumerate(geometries):
            if i not in grouped:
                continue
            _, names = zip(*grouped[i])
            feature_count = len(names)
            if feature_count < threshold:
                continue
            fc_count = len(set(names))
            results.append((geom, (feature_count, fc_count)))
        return results
    # End _summarize_by_planarized method

    def _build_overlaps_table(self, grouped: defaultdict[int, list[tuple]]) -> None:
        """
        Build Overlaps table
        """
        if not grouped or not self.overlap_table:
            return
        records = []
        # noinspection unresolved-references
        threshold = self._min_count
        for i, values in grouped.items():
            if len(values) < threshold:
                continue
            records.extend([(i, fid, name) for fid, name in values])
        tbl = self.overlap_table
        names = [f.escaped_name for f in self._get_overlap_fields()]
        # noinspection SqlInsertValues
        sql_insert = f"""
            INSERT INTO {tbl.escaped_name} ({COMMA_SPACE.join(names)}) 
            VALUES (?, ?, ?)
        """
        # noinspection unresolved-references
        with tbl.geopackage.connection as cout:
            cout.executemany(sql_insert, records)
    # End _build_overlaps_table method

    @cached_property
    def overlap_table(self) -> Optional['Table']:
        """
        Optional Overlap Table
        """
        # noinspection unresolved-references
        table = self._overlap
        if table is None:
            return None
        return table.geopackage.create_table(
            table.name, fields=self._get_overlap_fields(),
            overwrite=ANALYSIS_SETTINGS.overwrite)
    # End overlap_table property

    @staticmethod
    def _get_overlap_fields() -> FIELDS:
        """
        Get Overlap Fields
        """
        return OVERLAP_FID, ORIG_FID, ORIG_NAME
    # End _get_overlap_fields method

    def _get_geoms_attributes(self, feature_class: FeatureClass | None) \
            -> tuple[list['BaseGeometry'], list]:
        """
        Get Geometries and Attributes
        """
        geometries = []
        fids = []
        if not feature_class:
            return geometries, fids
        cursor = feature_class.select(fields=[ORIG_FID])
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            features, geoms = to_shapely(
                features, transformer=None, option=DimensionOption.TWO_D)
            fids.extend([fid for _, fid in features])
            geometries.extend(geoms)
        return geometries, fids
    # End _get_geoms_attributes method
# End CountOverlapMixin class


if __name__ == '__main__':  # pragma: no cover
    pass
