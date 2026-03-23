# -*- coding: utf-8 -*-
"""
Query Classes for management.proximity module
"""


from concurrent.futures.process import ProcessPoolExecutor
from math import nan
from functools import cache, cached_property, partial
from typing import Callable, Generator, NamedTuple, TYPE_CHECKING

from fudgeo import Field
from fudgeo.constant import COMMA_SPACE, FETCH_SIZE
from fudgeo.enumeration import ShapeType
from numpy import array, isfinite, ones_like, unique
from shapely.constructive import centroid
from shapely.coordinates import get_coordinates
from shapely.predicates import is_empty

from spyops.crs.transform import make_transformer_function
from spyops.crs.unit import (
    DecimalDegrees, LinearUnit, degrees_to_meters,
    get_linear_unit_conversion_factor, get_unit_name, unit_factory)
from spyops.environment import Setting
from spyops.geometry.buffer import geodesic_buffer, planar_buffer
from spyops.geometry.enumeration import DimensionOption
from spyops.geometry.multi import build_dissolved
from spyops.geometry.util import (
    filter_features, get_validity, make_none_mask, to_shapely)
from spyops.query.base import AbstractQueryDissolve
from spyops.shared.constant import DRID, EMPTY, METRE
from spyops.shared.enumeration import (
    BufferTypeOption, EndOption, SideOption)
from spyops.shared.field import (
    NUMBERS, TYPE_ALIAS_LUT, get_geometry_column_name)
from spyops.shared.hint import FIELDS, XY_TOL
from spyops.shared.keywords import (
    CRS_KEY, END_OPTION, METERS_ATTR, RESOLUTION, SHAPE_TYPE_KEY, SIDE_OPTION,
    VALUE_ATTR)


if TYPE_CHECKING:  # pragma: no cover
    from sqlite3 import Connection
    from fudgeo import FeatureClass
    from numpy import ndarray
    from shapely import MultiPolygon


class BufferConfig(NamedTuple):
    """
    Buffer Config
    """
    distance: Field | LinearUnit | DecimalDegrees
    buffer_type: BufferTypeOption
    side_option: SideOption
    end_option: EndOption
    resolution: int
# End BufferConfig class


class BufferMixin:
    """
    Buffer Mixin
    """
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
        # NOTE this extent is not used, simply filling a required argument
        null_clause = f'{distance.escaped_name} IS NOT NULL'
        # noinspection PyUnresolvedReferences
        if index_where := self._spatial_index_where(elm, extent=(0, 0, 0, 0)):
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
                units = [unit_factory(value) for value, in rows]
                units = [unit for unit in units if unit]
                has_linear = has_linear or any(
                    isinstance(u, LinearUnit) for u in units)
                has_angular = has_angular or any(
                    isinstance(u, DecimalDegrees) for u in units)
                if has_linear and has_angular:
                    return has_linear, has_angular
        return has_linear, has_angular
    # End _unit_types property

    @cached_property
    def buffer_type(self) -> BufferTypeOption:
        """
        Buffer Type
        """
        # noinspection PyUnresolvedReferences
        type_ = self._config.buffer_type
        if type_ == BufferTypeOption.GEODESIC:
            return type_
        has_linear, has_angular = self._unit_types
        if has_linear and has_angular:
            return BufferTypeOption.GEODESIC
        # noinspection PyUnresolvedReferences
        is_projected = self.source_crs.is_projected
        if (is_projected and has_angular) or (not is_projected and has_linear):
            return BufferTypeOption.GEODESIC
        return type_
    # End buffer_type property

    @cached_property
    def _buffer_function(self) -> Callable:
        """
        Buffer Function
        """
        # noinspection PyUnresolvedReferences
        kwargs = {
            CRS_KEY: self.source_crs,
            SHAPE_TYPE_KEY: self.source.shape_type,
            SIDE_OPTION: self._config.side_option,
            END_OPTION: self._config.end_option,
            RESOLUTION: self._config.resolution,
            str(Setting.XY_TOLERANCE): self._xy_tolerance,
        }
        if self.buffer_type == BufferTypeOption.PLANAR:
            func = planar_buffer
        else:
            func = geodesic_buffer
        return partial(func, **kwargs)
    # End _buffer_function property

    def _build_distance_field(self) -> str:
        """
        Build the distance field
        """
        if not self._is_distance_from_field:
            return EMPTY
        # noinspection PyUnresolvedReferences
        name = self._config.distance.escaped_name
        distance = f'{COMMA_SPACE}{name}'
        if not self._is_numeric_field:
            return distance
        # noinspection PyUnresolvedReferences
        unit = get_unit_name(self.source_crs)
        return f"{distance} || ' {unit}' AS {name}"
    # End _build_distance_field method

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type based on Output Type Option and Source Shape Type
        """
        return ShapeType.multi_polygon
    # End _get_target_shape_type method

    @cached_property
    def source_transformer(self) -> Callable | None:
        """
        Source Transformer, overloaded since we treat the geometry source
        as being the buffers which will always be MultiPolygons
        """
        # noinspection PyUnresolvedReferences
        elm = self.source
        # noinspection PyUnresolvedReferences
        transformer = self._get_transformer(elm)
        return make_transformer_function(
            self._get_target_shape_type(), has_z=False, has_m=False,
            transformer=transformer)
    # End source_transformer property

    @staticmethod
    def _fetch_features(connection: 'Connection', sql: str, size: int,
                        step: int) -> tuple[list[tuple], 'ndarray']:
        """
        Fetch Features
        """
        start = 1 + (step * size)
        end = (step + 1) * size
        cursor = connection.execute(sql, (start, end))
        features = filter_features(cursor.fetchall())
        return to_shapely(
            features, transformer=None, option=DimensionOption.TWO_D)
    # End _fetch_features method

    def _convert_unit(self, geometries: 'ndarray',
                      unit: LinearUnit | DecimalDegrees) -> 'ndarray':
        """
        Convert Unit
        """
        has_linear, _ = self._unit_types
        if self.buffer_type == BufferTypeOption.GEODESIC:
            if has_linear:
                value = getattr(unit, METERS_ATTR, nan)
            else:
                value = getattr(unit, VALUE_ATTR, nan)
                coordinates = get_coordinates(centroid(geometries))
                # noinspection PyUnresolvedReferences
                return degrees_to_meters(
                    self.source_crs, coordinates=coordinates, value=value)
        else:
            has_linear, _ = self._unit_types
            if has_linear:
                # NOTE return in units of the source CRS
                value = getattr(unit, METERS_ATTR, nan)
                value *= self._get_conversion_factor()
            else:
                value = getattr(unit, VALUE_ATTR, nan)
        return ones_like(geometries, dtype=float) * value
    # End _convert_unit method

    def _convert_units(self, geometries: 'ndarray',
                       units: list[LinearUnit | DecimalDegrees]) -> 'ndarray':
        """
        Convert Units
        """
        meters = array([getattr(unit, METERS_ATTR, nan)
                        for unit in units], dtype=float)
        if self.buffer_type == BufferTypeOption.GEODESIC:
            degrees = [(i, unit.value) for i, unit in enumerate(units)
                       if isinstance(unit, DecimalDegrees)]
            if not degrees:
                return meters
            ids, values = zip(*degrees)
            ids = array(ids, dtype=int)
            coordinates = get_coordinates(centroid(geometries[ids]))
            # noinspection PyUnresolvedReferences
            meters[ids] = degrees_to_meters(
                self.source_crs, coordinates=coordinates,
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
    def _get_conversion_factor(self) -> float:
        """
        Get Conversion Factor
        """
        # noinspection PyUnresolvedReferences
        unit_name = get_unit_name(self.source_crs)
        return get_linear_unit_conversion_factor(
            from_name=METRE, to_name=unit_name)
    # End _get_conversion_factor method
# End BufferMixin class


class QueryBufferDissolveList(BufferMixin, AbstractQueryDissolve):
    """
    Queries for Buffer (Dissolve List)
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass', *,
                 distance: Field | LinearUnit | DecimalDegrees,
                 buffer_type: BufferTypeOption, fields: FIELDS,
                 side_option: SideOption, end_option: EndOption,
                 resolution: int, xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QueryBufferDissolveList class
        """
        super().__init__(
            source, target=target, fields=fields, as_multi_part=True,
            xy_tolerance=xy_tolerance)
        self._config: BufferConfig = BufferConfig(
            distance=distance, buffer_type=buffer_type, side_option=side_option,
            end_option=end_option, resolution=resolution)
        self._counter: int = 0
    # End init built-in

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        return self._fields
    # End _get_unique_fields meth

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        elm = self.source
        # NOTE this extent not used, simply filling a required argument
        index_where = self._spatial_index_where(elm, extent=(0, 0, 0, 0))
        # noinspection PyUnresolvedReferences
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
        distance = self._build_distance_field()
        return f"""
            SELECT * 
            FROM (SELECT {geom}, dense_rank() OVER (
                    ORDER BY {self._group_names}) AS {DRID}{distance}
                  FROM {elm.escaped_name} {index_where})
            WHERE {DRID} BETWEEN ? AND ?
        """
    # End select_geometry property

    def dissolved_geometries(self) \
            -> Generator[dict[int, 'MultiPolygon'], None]:
        """
        Dissolved Geometries stored as a dictionary of Dense Range IDs
        and Multi-Part Geometries.  Page over the number of groups to
        avoid loading all geometries into memory at once.

        This method builds up a dictionary of geometries and yields it when it
        reaches (or exceeds) fetch size.  There is an expectation that when a
        geometry is stitched together with its aggregate row that the geometry
        will be popped from the dictionary.
        """
        size = FETCH_SIZE // 5
        steps, remainder = divmod(self.group_count, size)
        steps += bool(remainder)
        sql = self.select_geometry
        if self._is_distance_from_field:
            yield from self._from_field(sql, size, steps)
        else:
            yield from self._from_distance(sql, size, steps)
    # End dissolved_geometries method

    def _from_field(self, sql: str, size: int, steps: int) \
            -> Generator[dict[int, 'MultiPolygon'], None]:
        """
        Buffer and Dissolve using Distances from Field
        """
        dissolved = {}
        bufferer = self._buffer_function
        with self.source.geopackage.connection as cin:
            for step in range(steps):
                features, geometries = self._fetch_features(
                    cin, sql=sql, size=size, step=step)
                if not features:
                    continue
                units = [unit_factory(v) for _, _, v in features]
                # NOTE conversion validity
                valid = array([unit is not None for unit in units], dtype=bool)
                self._counter += ~valid.sum()
                if not valid.any():
                    continue
                ids = array([i for _, i, _ in features], dtype=int)
                ids = ids[valid]
                geometries = geometries[valid]
                # NOTE distance validity
                distances = self._convert_units(geometries, units=units)
                valid = isfinite(distances)
                self._counter += ~valid.sum()
                if not valid.any():
                    continue
                polygons = bufferer(geometries[valid], distances[valid])
                dissolved.update(self._dissolve_and_transform(polygons, ids[valid]))
                if len(dissolved) >= FETCH_SIZE:
                    yield dissolved
        yield dissolved
    # End _from_field method

    def _from_distance(self, sql: str, size: int, steps: int) \
            -> Generator[dict[int, 'MultiPolygon'], None]:
        """
        Buffer and Dissolve using Distances from Input Distance
        """
        dissolved = {}
        bufferer = self._buffer_function
        unit = self._config.distance
        with self.source.geopackage.connection as cin:
            for step in range(steps):
                features, geometries = self._fetch_features(
                    cin, sql=sql, size=size, step=step)
                if not features:
                    continue
                distances = self._convert_unit(geometries, unit=unit)
                # NOTE distance validity
                valid = isfinite(distances)
                self._counter += ~valid.sum()
                if not valid.any():
                    continue
                ids = array([i for _, i in features], dtype=int)
                polygons = bufferer(geometries[valid], distances[valid])
                dissolved.update(self._dissolve_and_transform(polygons, ids[valid]))
                if len(dissolved) >= FETCH_SIZE:
                    yield dissolved
        yield dissolved
    # End _from_distance method

    def _dissolve_and_transform(self, geometries: 'ndarray', ids: 'ndarray') \
            -> dict[int, 'MultiPolygon']:
        """
        Filter out None and Empty Geometries, Dissolve groups of Polygons,
        and then Apply Transform
        """
        mask = ~(make_none_mask(geometries) | is_empty(geometries))
        if not mask.any():
            return {}
        geometries, ids = self._dissolve_polygons(geometries[mask], ids[mask])
        if transformer := self.source_transformer:
            geometries = transformer(geometries)
            validity = get_validity(geometries, transformer=transformer)
            ids = ids[validity]
            geometries = geometries[validity]
        return dict(zip(ids, geometries))
    # End _dissolve_and_transform method

    def _dissolve_polygons(self, geometries: 'ndarray', ids: 'ndarray') \
            -> tuple[list, 'ndarray']:
        """
        Dissolve Polygons
        """
        builder = partial(build_dissolved, shape_type=ShapeType.multi_polygon,
                          grid_size=self._xy_tolerance)
        unique_ids = unique(ids)
        parts = [geometries[ids == i] for i in unique_ids]
        with ProcessPoolExecutor() as executor:
            geometries = list(executor.map(builder, parts))
        return geometries, unique_ids
    # End _dissolve_polygons method
# End QueryBuffer class


if __name__ == '__main__':  # pragma: no cover
    pass
