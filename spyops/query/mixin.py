# -*- coding: utf-8 -*-
"""
Mixins
"""


from datetime import datetime
from functools import cache, cached_property
from math import nan
from typing import Self, TYPE_CHECKING, Union

from fudgeo import FeatureClass, Field
from fudgeo.constant import COMMA_SPACE, FETCH_SIZE
from fudgeo.util import escape_name
from numpy import array, ones_like
from shapely.constructive import centroid
from shapely.coordinates import get_coordinates

from spyops.crs.unit import (
    DecimalDegrees, LinearUnit, degrees_to_meters,
    get_linear_unit_conversion_factor, get_unit_name, unit_factory)
from spyops.crs.util import crs_from_srs
from spyops.environment import ANALYSIS_SETTINGS
from spyops.shared.constant import DOT, DRID, EMPTY, METRE, SEMI

from spyops.shared.database import add_aggregates, remove_aggregates
from spyops.shared.field import (
    NUMBERS, TYPE_ALIAS_LUT, make_field_names, make_unique_fields)
from spyops.shared.hint import ELEMENT, EXTENT, FIELDS, STATS_FIELDS
from spyops.shared.keywords import METERS_ATTR, VALUE_ATTR
from spyops.shared.sql import IN, TEMP_SCHEMA


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray
    from pyproj import CRS


class AggregateContextMixin:
    """
    Aggregate Context Mixin
    """
    def __enter__(self) -> Self:
        """
        Context Manager Enter
        """
        # noinspection PyUnresolvedReferences
        add_aggregates(self.source.geopackage.connection)
        return self
    # End enter built-in

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Context Manager Exit
        """
        # noinspection PyUnresolvedReferences
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
        # noinspection PyUnresolvedReferences
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
        # noinspection PyUnresolvedReferences
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
    # noinspection PyUnusedLocal
    def _spatial_index_where(self, element: ELEMENT,
                             extent: EXTENT = (0, 0, 0, 0)) -> str:
        """
        Make a where clause stub that can be used to select features which
        intersect an extent. The query is based on a spatial index (if present).
        """
        if not isinstance(element, FeatureClass):
            return EMPTY
        # noinspection PyTypeChecker
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

    def _build_spatial_rank(self, element: ELEMENT) -> str:
        """
        Build Spatial Rank
        """
        # noinspection PyUnresolvedReferences
        primary = element.primary_key_field.escaped_name
        index_where = self._spatial_index_where(element)
        # noinspection PyUnresolvedReferences
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
        # noinspection PyUnresolvedReferences
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
        # noinspection PyUnresolvedReferences
        with self.source.geopackage.connection as cin:
            cin.execute(f"""DROP TABLE IF EXISTS {TEMP_SCHEMA}{DOT}{name}""")
    # End _delete_intermediate method

    @cached_property
    def _intermediate_table(self) -> str:
        """
        Intermediate Table
        """
        name = self._intermediate_name
        # noinspection PyUnresolvedReferences
        defs = COMMA_SPACE.join(repr(f) for f in self._intermediate_fields)
        # noinspection PyUnresolvedReferences
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
        # noinspection PyUnresolvedReferences
        return escape_name(f'tmp_{self.source.name}_{self._short_name}_{now}')
    # End _intermediate_name property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        # noinspection PyUnresolvedReferences
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
                      geoms: Union[list, 'ndarray'],
                      unit: LinearUnit | DecimalDegrees,
                      broadcast: bool = True) -> Union['ndarray', float]:
        """
        Convert Unit
        """
        has_linear, _ = self._unit_types
        if is_geodesic:
            if has_linear:
                value = getattr(unit, METERS_ATTR, nan)
            else:
                value = getattr(unit, VALUE_ATTR, nan)
                coordinates = get_coordinates(centroid(geoms))
                values = degrees_to_meters(
                    crs, coordinates=coordinates, value=value)
                if not broadcast:
                    return values[0]
                return values
        else:
            has_linear, _ = self._unit_types
            if has_linear:
                # NOTE return in units of the CRS
                value = getattr(unit, METERS_ATTR, nan)
                value *= self._get_conversion_factor(crs)
            else:
                value = getattr(unit, VALUE_ATTR, nan)
        if not broadcast:
            return value
        return ones_like(geoms, dtype=float) * value
    # End _convert_unit method

    def _convert_units(self, is_geodesic: bool, crs: 'CRS', geoms: 'ndarray',
                       units: list[LinearUnit | DecimalDegrees | None]) \
            -> 'ndarray':
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
                # NOTE return in units of the source CRS
                return meters * self._get_conversion_factor()
            else:
                # NOTE this will be in decimal degrees
                return array([getattr(unit, VALUE_ATTR, nan)
                              for unit in units], dtype=float)
    # End _convert_units method

    @cache
    def _get_conversion_factor(self, crs: 'CRS') -> float:
        """
        Get Conversion Factor
        """
        if not (unit_name := get_unit_name(crs)):
            return 1.
        return get_linear_unit_conversion_factor(
            from_name=METRE, to_name=unit_name)
    # End _get_conversion_factor method

    @property
    def _is_distance_from_field(self) -> bool:
        """
        Is Distance from Field?
        """
        # noinspection PyUnresolvedReferences
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
        # noinspection PyUnresolvedReferences
        return self._config.distance.data_type.casefold().startswith(aliases)
    # End _is_numeric_field property

    @cached_property
    def _unit_types(self) -> tuple[bool, bool]:
        """
        Check for Linear and Angular Units, return tuple of truth
        """
        # noinspection PyUnresolvedReferences
        elm = self.source
        # noinspection PyUnresolvedReferences
        distance = self._config.distance
        if not self._is_distance_from_field:
            is_linear = isinstance(distance, LinearUnit)
            return is_linear, not is_linear
        if self._is_numeric_field:
            # noinspection PyUnresolvedReferences
            is_projected = self.source_crs.is_projected
            return is_projected, not is_projected
        distance: Field
        null_clause = f'{distance.escaped_name} IS NOT NULL'
        # noinspection PyUnresolvedReferences
        if index_where := self._spatial_index_where(elm):
            where_clause = f'{index_where} AND {null_clause}'
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


if __name__ == '__main__':  # pragma: no cover
    pass
