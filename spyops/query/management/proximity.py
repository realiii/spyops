# -*- coding: utf-8 -*-
"""
Query Classes for management.proximity module
"""


from abc import ABCMeta, abstractmethod
from concurrent.futures.thread import ThreadPoolExecutor as PoolExecutor
from math import nan
from functools import cache, cached_property, partial
from typing import (
    Callable, Generator, Iterator, NamedTuple, TYPE_CHECKING, Type)
from warnings import warn

from fudgeo import Field, MemoryGeoPackage
from fudgeo.constant import COMMA_SPACE, FETCH_SIZE
from fudgeo.enumeration import FieldType, ShapeType
from numpy import array, asarray, isfinite, ones_like, unique
from shapely import GeometryCollection, MultiPolygon
from shapely.constructive import centroid
from shapely.coordinates import get_coordinates
from shapely.predicates import is_empty

from spyops.crs.enumeration import DistanceUnit
from spyops.crs.transform import make_transformer_function
from spyops.crs.unit import (
    DISTANCE_UNIT_LUT, DecimalDegrees, LinearUnit, Meters, degrees_to_meters,
    get_linear_unit_conversion_factor, get_unit_name, unit_factory)
from spyops.environment import Setting
from spyops.geometry.buffer import geodesic_buffer, planar_buffer
from spyops.geometry.enumeration import DimensionOption
from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.multi import build_dissolved
from spyops.geometry.util import (
    filter_features, get_validity, make_none_mask, to_shapely)
from spyops.query.base import AbstractQueryDissolve
from spyops.shared.constant import DRID, EMPTY, METRE, SKIP_FILE_PREFIXES
from spyops.shared.enumeration import (
    BufferTypeOption, EndOption, SideOption)
from spyops.shared.exception import DistanceCalculationWarning, UnitParseWarning
from spyops.shared.field import (
    NUMBERS, TYPE_ALIAS_LUT, add_orig_fid, get_geometry_column_name,
    make_field_names, make_unique_fields, validate_fields)
from spyops.shared.hint import FIELDS, XY_TOL
from spyops.shared.keywords import (
    CRS_KEY, END_OPTION, METERS_ATTR, RESOLUTION, SHAPE_TYPE_KEY, SIDE_OPTION,
    VALUE_ATTR)


if TYPE_CHECKING:  # pragma: no cover
    from sqlite3 import Connection
    from fudgeo import FeatureClass
    from numpy import ndarray


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


class AbstractQueryBufferDissolve(AbstractQueryDissolve, metaclass=ABCMeta):
    """
    Abstract Query Buffer Dissolve Class
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass', *,
                 distance: Field | LinearUnit | DecimalDegrees,
                 buffer_type: BufferTypeOption, fields: FIELDS | None,
                 side_option: SideOption, end_option: EndOption,
                 resolution: int, xy_tolerance: XY_TOL) -> None:
        """
        Initialize the AbstractQueryBufferDissolve class
        """
        super().__init__(
            source, target=target, fields=fields or [], as_multi_part=True,
            xy_tolerance=xy_tolerance)
        self._config: BufferConfig = BufferConfig(
            distance=distance, buffer_type=buffer_type, side_option=side_option,
            end_option=end_option, resolution=resolution)
        self._counter: int = 0
    # End init built-in

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

    def show_warning(self) -> None:
        """
        Show Warning
        """
        # noinspection PyUnresolvedReferences
        counter = self._counter
        if not counter:
            return
        # noinspection PyUnresolvedReferences
        distance = self._config.distance
        if self._is_distance_from_field:
            category = UnitParseWarning
            msg = (f'Unable to parse {counter} distance(s) '
                   f'from {distance}')
        else:
            category = DistanceCalculationWarning
            msg = (f'Unable to calculate {counter} distance(s) '
                   f'from {distance !r}')
        warn(msg, category=category, skip_file_prefixes=SKIP_FILE_PREFIXES)
    # End show_warning method

    def dissolved_geometries(self) -> Generator[dict[int, MultiPolygon], None, None]:
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
            yield from self._from_field(sql, size=size, steps=steps)
        else:
            yield from self._from_distance(sql, size=size, steps=steps)
    # End dissolved_geometries method

    @abstractmethod
    def _from_field(self, sql: str, size: int, steps: int) \
            -> Generator[dict[int, MultiPolygon], None, None]:
        """
        Buffer and Dissolve using Distances from Field
        """
        pass
    # End _from_field method

    @abstractmethod
    def _from_distance(self, sql: str, size: int, steps: int) \
            -> Generator[dict[int, MultiPolygon], None, None]:
        """
        Buffer and Dissolve using Distances from Input Distance
        """
        pass
    # End _from_distance method

    def _dissolve_and_transform(self, geometries: 'ndarray', ids: 'ndarray') \
            -> dict[int, MultiPolygon]:
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
        with PoolExecutor() as executor:
            geometries = list(executor.map(builder, parts))
        return geometries, unique_ids
    # End _dissolve_polygons method

    def _get_units(self, features: list[tuple]) -> tuple[
            list[LinearUnit | DecimalDegrees | None], 'ndarray']:
        """
        Get Units and Conversion Validity
        """
        units = [unit_factory(feature[-1]) for feature in features]
        valid = array([unit is not None for unit in units], dtype=bool)
        self._counter += ~valid.sum()
        return units, valid
    # End _get_units method

    def _get_distances(self, geometries: 'ndarray',
                       units: list[LinearUnit | DecimalDegrees | None]) \
            -> tuple['ndarray', 'ndarray']:
        """
        Get Distances and Distance Validity
        """
        distances = self._convert_units(geometries, units=units)
        valid = isfinite(distances)
        self._counter += ~valid.sum()
        return distances, valid
    # End _get_distances method

    def _get_distances_broadcast(self, geometries: 'ndarray',
                                 unit: LinearUnit | DecimalDegrees) \
            -> tuple['ndarray', 'ndarray']:
        """
        Get Distances and Distance Validity, broadcasting unit to all geometries
        """
        distances = self._convert_unit(geometries, unit=unit)
        valid = isfinite(distances)
        self._counter += ~valid.sum()
        return distances, valid
    # End _get_distances_broadcast method
# End AbstractQueryBufferDissolve class


class QueryBufferDissolveList(AbstractQueryBufferDissolve):
    """
    Queries for Buffer (Dissolve List)
    """
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

    def _from_field(self, sql: str, size: int, steps: int) \
            -> Generator[dict[int, MultiPolygon], None, None]:
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
                units, valid = self._get_units(features)
                if not valid.any():
                    continue
                ids = array([i for _, i, _ in features], dtype=int)
                ids = ids[valid]
                geometries = geometries[valid]
                distances, valid = self._get_distances(geometries, units=units)
                if not valid.any():
                    continue
                polygons = bufferer(geometries[valid], distances[valid])
                dissolved.update(
                    self._dissolve_and_transform(polygons, ids[valid]))
                if len(dissolved) >= FETCH_SIZE:
                    yield dissolved
        yield dissolved
    # End _from_field method

    def _from_distance(self, sql: str, size: int, steps: int) \
            -> Generator[dict[int, MultiPolygon], None, None]:
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
                distances, valid = self._get_distances_broadcast(
                    geometries, unit=unit)
                if not valid.any():
                    continue
                ids = array([i for _, i in features], dtype=int)
                polygons = bufferer(geometries[valid], distances[valid])
                dissolved.update(
                    self._dissolve_and_transform(polygons, ids[valid]))
                if len(dissolved) >= FETCH_SIZE:
                    yield dissolved
        yield dissolved
    # End _from_distance method
# End QueryBufferDissolveList class


class QueryBufferDissolveAll(AbstractQueryBufferDissolve):
    """
    Queries for Buffer (Dissolve All)
    """
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        return []
    # End _get_unique_fields meth

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
        distance = self._build_distance_field()
        return f"""
            SELECT {geom}{distance} 
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

    def _from_field(self, sql: str, size: int, steps: int) \
            -> Generator[dict[int, MultiPolygon], None, None]:
        """
        Buffer and Dissolve using Distances from Field
        """
        counter = 0
        dissolved = {}
        bufferer = self._buffer_function
        with self.source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            while features := cursor.fetchmany(size):
                if not (features := filter_features(features)):
                    continue
                features, geometries = to_shapely(
                    features, transformer=None, option=DimensionOption.TWO_D)
                units, valid = self._get_units(features)
                if not valid.any():
                    continue
                geometries = geometries[valid]
                distances, valid = self._get_distances(geometries, units=units)
                if not valid.any():
                    continue
                polygons = bufferer(geometries[valid], distances[valid])
                ids = ones_like(polygons, dtype=int) * counter
                dissolved.update(self._dissolve_and_transform(polygons, ids))
                counter += 1
        yield from self._build_single_polygon(dissolved)
    # End _from_field method

    def _from_distance(self, sql: str, size: int, steps: int) \
            -> Generator[dict[int, MultiPolygon], None, None]:
        """
        Buffer and Dissolve using Distances from Input Distance
        """
        counter = 0
        dissolved = {}
        bufferer = self._buffer_function
        unit = self._config.distance
        with self.source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            while features := cursor.fetchmany(size):
                if not (features := filter_features(features)):
                    continue
                _, geometries = to_shapely(
                    features, transformer=None, option=DimensionOption.TWO_D)
                distances = self._convert_unit(geometries, unit=unit)
                # NOTE distance validity
                valid = isfinite(distances)
                self._counter += ~valid.sum()
                if not valid.any():
                    continue
                polygons = bufferer(geometries[valid], distances[valid])
                ids = ones_like(polygons, dtype=int) * counter
                dissolved.update(self._dissolve_and_transform(polygons, ids))
                counter += 1
        yield from self._build_single_polygon(dissolved)
    # End _from_distance method

    def _build_single_polygon(self, dissolved: dict[int, MultiPolygon]) \
            -> Generator[dict[int, MultiPolygon], None, None]:
        """
        Build Single Dissolved Polygon from Page-Dissolved Geometries
        """
        key = 1
        if not dissolved:
            yield {key: MultiPolygon([])}
        elif len(dissolved) == 1:
            _, result = dissolved.popitem()
            yield {key: result}
        else:
            geometries = array(list(dissolved.values()))
            # NOTE grid size is used here since we are dealing with
            #  geometry post transformation
            result = build_dissolved(
                geometries, shape_type=ShapeType.multi_polygon,
                grid_size=self.grid_size)
            yield {key: result}
    # End _build_single_polygon method
# End QueryBufferDissolveAll class


class QueryBufferDissolveNone(AbstractQueryBufferDissolve):
    """
    Queries for Buffer (Dissolve None)
    """
    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        return add_orig_fid(self.source)
    # End _get_unique_fields meth

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        elm = self.source
        name = self.source.primary_key_field.escaped_name
        field_names = make_field_names(self._get_unique_fields()[1:])
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
        distance = self._build_distance_field()
        name = self.source.primary_key_field.escaped_name
        geom_and_fid = self._concatenate(geom, name)
        return f"""
            SELECT {geom_and_fid}{distance} 
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

    def _from_field(self, sql: str, size: int, steps: int) \
            -> Generator[dict[int, MultiPolygon], None, None]:
        """
        Buffer and Dissolve using Distances from Field
        """
        dissolved = {}
        bufferer = self._buffer_function
        with self.source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            while features := cursor.fetchmany(size):
                if not (features := filter_features(features)):
                    continue
                features, geometries = to_shapely(
                    features, transformer=None, option=DimensionOption.TWO_D)
                units, valid = self._get_units(features)
                if not valid.any():
                    continue
                ids = array([i for _, i, _ in features], dtype=int)
                ids = ids[valid]
                geometries = geometries[valid]
                distances, valid = self._get_distances(geometries, units=units)
                if not valid.any():
                    continue
                polygons = bufferer(geometries[valid], distances[valid])
                dissolved.update(
                    self._dissolve_and_transform(polygons, ids[valid]))
                if len(dissolved) >= FETCH_SIZE:
                    yield dissolved
        yield dissolved
    # End _from_field method

    def _from_distance(self, sql: str, size: int, steps: int) \
            -> Generator[dict[int, MultiPolygon], None, None]:
        """
        Buffer and Dissolve using Distances from Input Distance
        """
        dissolved = {}
        bufferer = self._buffer_function
        unit = self._config.distance
        with self.source.geopackage.connection as cin:
            cursor = cin.execute(sql)
            while features := cursor.fetchmany(size):
                if not (features := filter_features(features)):
                    continue
                features, geometries = to_shapely(
                    features, transformer=None, option=DimensionOption.TWO_D)
                distances, valid = self._get_distances_broadcast(
                    geometries, unit=unit)
                if not valid.any():
                    continue
                ids = array([i for _, i in features], dtype=int)
                polygons = bufferer(geometries[valid], distances[valid])
                dissolved.update(
                    self._dissolve_and_transform(polygons, ids[valid]))
                if len(dissolved) >= FETCH_SIZE:
                    yield dissolved
        yield dissolved
    # End _from_distance method

    def _dissolve_polygons(self, geometries: 'ndarray', ids: 'ndarray') \
            -> tuple['ndarray', 'ndarray']:
        """
        Dissolve Polygons
        """
        return geometries, ids
    # End _dissolve_polygons method
# End QueryBufferDissolveNone class


class QueryMultipleBuffer(AbstractQueryBufferDissolve):
    """
    Query Multiple Buffer
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass',
                 distance_unit: DistanceUnit, distances: list[float], *,
                 buffer_type: BufferTypeOption = BufferTypeOption.PLANAR,
                 overlapping: bool = False, only_outside: bool = False,
                 field_name: str | None = None, resolution: int = 32,
                 xy_tolerance: XY_TOL = None) -> None:
        """
        Initialize the QueryMultipleBuffer class
        """
        side_option = self._get_side_option(source, only_outside=only_outside)
        super().__init__(source=source, target=target, distance=Meters(0),
                         buffer_type=buffer_type, fields=None,
                         side_option=side_option, end_option=EndOption.ROUND,
                         resolution=resolution, xy_tolerance=xy_tolerance)
        self._distance_unit: DistanceUnit = distance_unit
        self._distances: list[float] = sorted(set(distances))
        self._overlapping: bool = overlapping
        self._only_outside: bool = only_outside
        self._field_name: str | None = field_name
    # End init built-in

    def __iter__(self) -> Iterator[tuple[QueryBufferDissolveNone, str]]:
        """
        Iterate over the query results
        """
        config = self._config
        units, labels = self._distances_and_labels()
        for unit, label in reversed(list(zip(units, labels))):
            # noinspection PyTypeChecker
            query = QueryBufferDissolveNone(
                source=self.source, target=None, buffer_type=self.buffer_type,
                fields=None, distance=unit, side_option=config.side_option,
                end_option=config.end_option, resolution=config.resolution,
                xy_tolerance=self._xy_tolerance)
            update_sql = self._make_update_sql(label)
            yield query, update_sql
    # End iter built-in

    def _make_update_sql(self, distance: LinearUnit | DecimalDegrees) -> str:
        """
        Make Update SQL
        """
        if not self._distance_field:
            return EMPTY
        field = self._get_unique_fields()[-1]
        return f"""
            UPDATE {self.target.escaped_name}
            SET {field.escaped_name} = '{distance}'
            WHERE {field.escaped_name} IS NULL
        """
    # End _make_update_sql method

    def _distances_and_labels(self) \
            -> tuple[list[LinearUnit | DecimalDegrees], list[str]]:
        """
        Distances as Units and Corresponding Labels
        """
        unit = DISTANCE_UNIT_LUT[self._distance_unit]
        if ShapeType.polygon not in self.source.shape_type:
            units = [unit(d) for d in self._distances if d > 0]
            return units, self._make_labels(units)
        if self._overlapping:
            return self._distances_labels_overlap(unit)
        else:
            return self._distance_labels_sans(unit)
    # End _distances_and_labels method

    def _distances_labels_overlap(self, unit: Type[LinearUnit | DecimalDegrees]) \
            -> tuple[list[LinearUnit | DecimalDegrees], list[str]]:
        """
        Distances and Labels for Overlapping Polygons (aka Dissolve NONE)
        """
        if self._only_outside:
            negatives = [d for d in self._distances if d < 0][::-1]
            positives = [d for d in self._distances if d > 0]
            units = [unit(d) for d in [*negatives, *positives]]
            labels = self._make_labels(units)
        else:
            units = self._include_original_polygon(unit)
            if 0 in self._distances:
                labels = self._make_labels(units)
            else:
                labels = [str(unit) if unit.value else EMPTY for unit in units]
        return units, labels
    # End _distances_labels_overlap method

    def _distance_labels_sans(self, unit: Type[LinearUnit | DecimalDegrees]) \
            -> tuple[list[LinearUnit | DecimalDegrees], list[str]]:
        """
        Distance Labels for Non-Overlapping Polygons (aka Dissolve ALL)
        """
        if self._only_outside:
            units = [unit(d) for d in self._distances if d]
        else:
            units = self._include_original_polygon(unit)
        return units, self._make_labels(units)
    # End _distance_labels_sans method

    @staticmethod
    def _make_labels(units: list[LinearUnit | DecimalDegrees]) -> list[str]:
        """
        Make Labels
        """
        return [str(unit) for unit in units]
    # End _make_labels method

    def _include_original_polygon(self, unit: Type[LinearUnit | DecimalDegrees]) \
            -> list[LinearUnit | DecimalDegrees]:
        """
        Include Original Polygon
        """
        if min(self._distances) < 0:
            return [unit(d) for d in sorted({0, *self._distances})]
        return [unit(d) for d in self._distances]
    # End _include_original_polygon method

    @cached_property
    def _distance_field(self) -> Field | None:
        """
        Distance Field
        """
        if not (name := self._field_name):
            return None
        if isinstance(name, Field):
            name = name.name
        if not isinstance(name, str):
            return None
        if not (name := name.strip()):
            return None
        return Field(name, data_type=FieldType.text)
    # End _distance_field property

    def dissolved_geometries(self) -> list[tuple[MultiPolygon, tuple]]:
        """
        Overload
        """
        ordered = []
        distances = []
        config = self._config
        has_field = self._distance_field is not None
        scratch = MemoryGeoPackage.create()
        source = self._create_dissolved_source(scratch)
        units, labels = self._distances_and_labels()
        for unit, label in zip(units, labels):
            # noinspection PyTypeChecker
            query = QueryBufferDissolveAll(
                source=source, target=None, buffer_type=self.buffer_type,
                fields=None, distance=unit, side_option=config.side_option,
                end_option=config.end_option, resolution=config.resolution,
                xy_tolerance=self._xy_tolerance)
            if not (geoms := next(query.dissolved_geometries(), {})):
                continue
            geom, = geoms.values()
            if geom.is_empty:
                continue
            if has_field:
                attrs = label,
            else:
                attrs = ()
            ordered.append((geom, attrs))
            distances.append(unit.value)
        scratch.connection.close()
        return self._resolve_overlaps(ordered, distances=distances)
    # End dissolved_geometries method

    def _create_dissolved_source(self, memory: MemoryGeoPackage) \
            -> 'FeatureClass':
        """
        Create Dissolved Feature Class
        """
        geoms = []
        shape_type = self.source.shape_type
        with self.source.geopackage.connection as cin:
            cursor = cin.execute(self.select_geometry)
            while features := cursor.fetchmany(FETCH_SIZE):
                if not (features := filter_features(features)):
                    continue
                _, geometries = to_shapely(
                    features, transformer=None, option=DimensionOption.TWO_D)
                geom = build_dissolved(
                    geometries, shape_type=shape_type,
                    grid_size=self._xy_tolerance)
                geoms.append(geom)
        if len(geoms) == 1:
            geom, = geoms
        else:
            geom = build_dissolved(
                asarray(geoms), shape_type=shape_type,
                grid_size=self._xy_tolerance)
        if not self.source.is_multi_part:
            shape_type = f'MULTI{shape_type}'
        fc = memory.create_feature_class(
            name=f'memory_{shape_type}_dissolved', overwrite=True,
            shape_type=shape_type, srs=self.source.spatial_reference_system)
        cls = FUDGEO_GEOMETRY_LOOKUP[shape_type][False, False]
        with fc.geopackage.connection as cout:
            srs_id = fc.spatial_reference_system.srs_id
            cout.executemany(f"""
                INSERT INTO {fc.escaped_name} ({fc.geometry_column_name}) 
                VALUES (?)
            """, [(cls.from_wkb(geom.wkb, srs_id=srs_id),)])
        return fc
    # End dissolved_geometries method

    def _resolve_overlaps(self, ordered: list[tuple[MultiPolygon, tuple]],
                          distances: list[float]) \
            -> list[tuple[MultiPolygon, tuple]]:
        """
        Resolve Overlaps
        """
        if len(ordered) <= 1:
            return ordered
        geoms, attributes = zip(*ordered)
        if self._only_outside:
            polygons = self._build_only_outside(geoms, distances)
        else:
            polygons = self._build_no_overlaps(geoms)
        if len(distances) != len([d for d in distances if d]):
            attributes = [attrs for attrs, d in zip(attributes, distances) if d]
            if self._distance_field:
                first = None,
            else:
                first = ()
            attributes = [first, *attributes]
        return list(zip(polygons, attributes))
    # End _resolve_overlaps method

    def _build_only_outside(self, geoms: list[MultiPolygon],
                            distances: list[float]) -> list[MultiPolygon]:
        """
        Build Non-Overlapping Polygons for Only Outside
        """
        negatives = []
        negs = [g for g, d in zip(geoms, distances) if d <= 0]
        for i, geom in enumerate(negs, 1):
            poly = geom.difference(GeometryCollection(negs[i:]),
                                   grid_size=self._xy_tolerance)
            negatives.append(poly)
        positives = []
        poss = [g for g, d in zip(geoms, distances) if d > 0][::-1]
        for i, geom in enumerate(poss, 1):
            poly = geom.difference(GeometryCollection(poss[i:]),
                                   grid_size=self._xy_tolerance)
            positives.append(poly)
        return [*negatives, *positives[::-1]]
    # End _build_only_outside method

    def _build_no_overlaps(self, geoms: list[MultiPolygon]) \
            -> list[MultiPolygon]:
        """
        Build No Overlaps
        """
        polygons = []
        for inner, outer in zip(geoms[:-1], geoms[1:]):
            poly = outer.difference(inner, grid_size=self._xy_tolerance)
            polygons.append(poly)
        return [geoms[0], *polygons]
    # End _build_no_overlaps method

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        elm = self.source
        name = self.source.primary_key_field.escaped_name
        fields = self._get_unique_fields()[1:]
        if self._distance_field:
            fields = fields[:-1]
        field_names = make_field_names(fields)
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
        distance = self._build_distance_field()
        return f"""
            SELECT {geom}{distance} 
            FROM {elm.escaped_name} {index_where}
        """
    # End select_geometry property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        if not self._overlapping:
            return super().insert
        elm = self.target
        fields = validate_fields(elm, fields=elm.fields)
        if self._field_name:
            fields = fields[:-1]
        insert_field_names = make_field_names(fields)
        geom = get_geometry_column_name(elm)
        insert_field_names = self._concatenate(geom, insert_field_names)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=len(fields) + 1)
    # End insert property

    def _from_field(self, sql: str, size: int, steps: int) \
            -> Generator[dict[int, MultiPolygon], None, None]:  # pragma: no cover
        """
        Overload
        """
        pass
    # End _from_field method

    def _from_distance(self, sql: str, size: int, steps: int) \
            -> Generator[dict[int, MultiPolygon], None, None]:  # pragma: no cover
        """
        Overload
        """
        pass
    # End _from_distance method

    @staticmethod
    def _get_side_option(source: 'FeatureClass',
                         only_outside: bool) -> SideOption:
        """
        Get Side Option, Only Outside applies to Polygons only
        """
        if not only_outside:
            return SideOption.FULL
        if ShapeType.polygon in source.shape_type:
            return SideOption.ONLY_OUTSIDE
        return SideOption.FULL
    # End _get_side_option method

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        distance_field = self._distance_field
        if not self._overlapping:
            if distance_field:
                return [distance_field]
            return []
        fields = add_orig_fid(self.source)
        if not distance_field:
            return fields
        distance_field = make_unique_fields(fields, [distance_field])
        return [*fields, *distance_field]
    # End _get_unique_fields meth
# End QueryMultipleBuffer class


if __name__ == '__main__':  # pragma: no cover
    pass
