# -*- coding: utf-8 -*-
"""
Queries for Sampling
"""


from abc import ABCMeta, abstractmethod
from functools import cache, cached_property
from typing import (
    Any, Callable, Generator, NamedTuple, Optional, TYPE_CHECKING, Type, Union)
from warnings import warn

from fudgeo.enumeration import ShapeType
from numpy import arange, array, cumsum, isfinite, isnan
from shapely.measurement import length as length_

from spyops.crs.unit import UNIT_CLASS_MAP, get_unit_name, unit_factory
from spyops.crs.util import crs_from_srs
from spyops.geometry.convert import GEOMETRY_AS_MULTILINE
from spyops.geometry.distance import (
    get_equidistant_details, interpolate_locations, make_points)
from spyops.geometry.util import (
    get_coords_and_slices, get_geoms, nada, to_shapely)
from spyops.query.base import AbstractSourceQuery
from spyops.query.mixin import UnitTypeMixin
from spyops.shared.constant import SEMI, SKIP_FILE_PREFIXES
from spyops.shared.enumeration import DistanceTypeOption
from spyops.shared.exception import DistanceCalculationWarning, UnitParseWarning
from spyops.shared.field import (
    ALONG, ORIG_FID, SEQ_NUM, get_geometry_column_name, make_field_names)
from spyops.shared.hint import FIELDS, PLACEMENT
from spyops.shared.util import safe_float


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from numpy import ndarray
    from pyproj import CRS
    from shapely import Point
    from shapely.geometry.base import BaseGeometry, GeometrySequence
    from spyops.crs.unit import LinearUnit, DecimalDegrees


class PlacementConfig(NamedTuple):
    """
    Placement Config
    """
    distance: PLACEMENT
    distance_type: DistanceTypeOption
    include_ends: bool
# End PlacementConfig class


class PlacementDetails(NamedTuple):
    """
    Placement Details
    """
    fid: int
    lines: list
    lengths: 'ndarray'
    distances: 'ndarray'
    coordinates: 'ndarray'
    ids: tuple[int, ...]
# End PlacementDetails class


class AbstractQueryGenerateAlongLines(AbstractSourceQuery, UnitTypeMixin):
    """
    Abstract Query Generate Along Lines
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass',
                 placement: PLACEMENT, include_ends: bool,
                 where_clause: str, distance_type: DistanceTypeOption) -> None:
        """
        Initialize the AbstractQueryGenerateAlongLines class
        """
        super().__init__(source, target=target, where_clause=where_clause)
        self._config: PlacementConfig = PlacementConfig(
            distance=placement, distance_type=distance_type,
            include_ends=include_ends)
        self._counter: int = 0
    # End init built-in

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        return ORIG_FID, SEQ_NUM, ALONG
    # End _get_unique_fields method

    def _get_select_fields(self, element: 'FeatureClass') -> FIELDS:
        """
        Get Select Fields
        """
        primary = element.primary_key_field
        # noinspection bad-return
        return [primary, primary]
    # End _get_select_fields method

    @cache
    def _field_names_and_count(self, element: 'FeatureClass') -> tuple[int, str, str]:
        """
        Field Names for Select and Insert + Derive Field Count
        """
        select_names = make_field_names(self._get_select_fields(element))
        select_names = self._concatenate(
            get_geometry_column_name(element, include_geom_type=True),
            select_names)
        fields = self._get_unique_fields()
        insert_names = self._concatenate(
            get_geometry_column_name(element), make_field_names(fields))
        return len(fields) + 1, insert_names, select_names
    # End _field_names_and_count method

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
    def distance_type(self) -> DistanceTypeOption:
        """
        Distance Type
        """
        dist_type = self._crs_distance_type_check()
        if dist_type == DistanceTypeOption.GEODESIC:
            return dist_type
        return self._unit_distance_type_check(dist_type)
    # End distance_type property

    def _crs_distance_type_check(self) -> DistanceTypeOption:
        """
        Distance Type Check based on CRS
        """
        if not self.target_crs.is_projected:
            return DistanceTypeOption.GEODESIC
        return self._config.distance_type
    # End _crs_distance_type_check method

    def _unit_distance_type_check(self, dist_type: DistanceTypeOption) \
            -> DistanceTypeOption:
        """
        Distance Type Check based on Unit Types
        """
        _, has_angular = self._unit_types
        if has_angular:
            return DistanceTypeOption.GEODESIC
        return dist_type
    # End _unit_distance_type_check method

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.point
    # End _get_target_shape_type method

    def show_warning(self) -> None:
        """
        Show Warning
        """
        if not (counter := self._counter):
            return
        distance = self._config.distance
        if self._is_distance_from_field:
            category = UnitParseWarning
            # noinspection PyUnresolvedReferences
            msg = (f'Unable to parse {counter} distance(s) '
                   f'from {distance.name}')
        else:
            category = DistanceCalculationWarning
            msg = (f'Unable to calculate {counter} distance(s) '
                   f'from {distance !r}')
        warn(msg, category=category, skip_file_prefixes=SKIP_FILE_PREFIXES)
    # End show_warning method

    def generate_features(self, features: list[tuple]) -> list[tuple]:
        """
        Generate Points
        """
        features, geometries = to_shapely(
            features, transformer=self.source_transformer)
        getter = GEOMETRY_AS_MULTILINE[self.source.shape_type]
        kwargs = dict(features=features, geometries=geometries,
                      crs=self.target_crs, getter=getter)
        if self.distance_type == DistanceTypeOption.PLANAR:
            return self._along_planar(**kwargs)
        return self._along_geodesic(**kwargs)
    # End generate_features method

    @property
    def target_crs(self) -> CRS:
        """
        Target CRS
        """
        # noinspection bad-argument-type
        return crs_from_srs(self.spatial_reference_system)
    # End target_crs property

    @abstractmethod
    def _get_values(self, geoms: Union[list, 'GeometrySequence'],
                    total_length: float, crs: 'CRS',
                    distance: Any) -> 'ndarray':  # pragma: no cover
        """
        Get Values
        """
        pass
    # End _get_values method

    @abstractmethod
    def _along_planar(self, features: list[tuple],
                      geometries: 'ndarray', crs: 'CRS',
                      getter: Callable) -> list[tuple['BaseGeometry', tuple]]:
        """
        Place Geometries Planar
        """
        pass
    # End _along_planar method

    @abstractmethod
    def _along_geodesic(self, features: list[tuple],
                        geometries: 'ndarray', crs: 'CRS',
                        getter: Callable) -> list[tuple['BaseGeometry', tuple]]:
        """
        Place Geometries Geodesic
        """
        pass
    # End _along_geodesic method

    def _build_range(self, geoms: Union[list, 'GeometrySequence'],
                     total_length: float, crs: 'CRS',
                     unit: Optional[Union['LinearUnit', 'DecimalDegrees']]) \
            -> 'ndarray':
        """
        Build Range of Distances from unit
        """
        if unit is None:
            self._counter += 1
            return array([], dtype=float)
        distance = self._to_distance(geoms, crs=crs, unit=unit)
        if (distance is None or isnan(distance) or
                distance <= 0 or distance >= total_length):
            self._counter += 1
            return array([], dtype=float)
        return arange(distance, total_length, distance)
    # End _build_range method

    def _to_distance(self, geoms: Union[list, 'GeometrySequence'], crs: 'CRS',
                     unit: Union['LinearUnit', 'DecimalDegrees']) -> float:
        """
        Convert unit to distance
        """
        # noinspection bad-return,bad-argument-type
        return self._convert_unit(
            self.distance_type == DistanceTypeOption.GEODESIC, crs=crs,
            geoms=geoms, unit=unit, broadcast=False)
    # End _to_distance method

    @cached_property
    def _source_unit_cls(self) -> Type['LinearUnit'] | Type['DecimalDegrees']:
        """
        Source Unit Class
        """
        # noinspection bad-index
        return UNIT_CLASS_MAP[get_unit_name(self.source_crs)]
    # End _source_unit_cls method

    def _build_multi_values(self, geoms: Union[list, 'GeometrySequence'],
                            total_length: float, crs: 'CRS',
                            distance: str) -> 'ndarray':
        """
        Build Multi Values
        """
        units = self._get_units_from_distances(distance)
        count = len(units)
        if not (units := [unit for unit in units if unit is not None]):
            self._counter += count
            return array([], dtype=float)
        distances = [self._to_distance(geoms, crs=crs, unit=unit)
                     for unit in units]
        bads = [isnan(d) or d <= 0 or d >= total_length for d in distances]
        if all(bads):
            self._counter += sum(bads)
            return array([], dtype=float)
        if any(bads):
            self._counter += sum(bads)
        distances = [d for d, bad in zip(distances, bads) if not bad]
        return array(distances, dtype=float)
    # End _build_multi_values method

    def _get_units_from_distances(self, distance: str) \
            -> list[Optional[Union['LinearUnit', 'DecimalDegrees']]]:
        """
        Get Units from Distances
        """
        units = []
        for dist in distance.split(SEMI):
            if unit := unit_factory(dist):
                units.append(unit)
                continue
            if dist := safe_float(dist):
                unit = self._source_unit_cls(dist)
            else:
                unit = None
            units.append(unit)
        return units
    # End _get_units_from_distances method

    def _get_placement_details(self, features: list[tuple],
                               geometries: 'ndarray', crs: 'CRS',
                               getter: Callable) \
            -> Generator[PlacementDetails]:
        """
        Get Placement Details
        """
        for (_, fid, distance), geom in zip(features, geometries):
            lines = get_geoms(getter(geom))
            # noinspection PyTypeChecker
            lengths = length_(lines)
            mask = isfinite(lengths)
            if not mask.any():  # pragma: no cover
                continue
            lengths = cumsum(lengths[mask])
            lines = [line for line, truth in zip(lines, mask) if truth]
            distances = self._get_values(
                lines, total_length=lengths[-1], crs=crs, distance=distance)
            coordinates, ids = get_coords_and_slices(
                lines, include_z=True, include_m=True)
            results = interpolate_locations(
                values, lengths=lengths, coordinates=coordinates, ids=ids,
                fid=fid, include_ends=self._config.include_ends)
            records.extend(results)
        points = make_points(
            yield PlacementDetails(
                fid=fid, lines=lines, lengths=lengths, distances=distances,
                coordinates=coordinates, ids=ids)
    # End _get_placement_details method
# End AbstractQueryGenerateAlongLines class
            records, has_z=self.source.has_z, has_m=self.source.has_m)
        return [(pt, attrs) for pt, (_, *attrs) in zip(points, records)]
    # End _along_planar method

    def _along_geodesic(self, features: list[tuple],
                        geometries: 'ndarray', crs: 'CRS',
                        getter: Callable) -> list[tuple['Point', tuple]]:
        """
        Place Points Geodesic
        """
        records = []
        details = get_equidistant_details(
            geometries, crs=crs, has_z=self.source.has_z,
            has_m=self.source.has_m)
        for indexes, prj, to_eqd, from_eqd in details:
            feats = [features[i] for i in indexes]
            geoms = geometries[indexes]
            if None in (to_eqd, from_eqd):
                records.extend(self._along_planar(
                    feats, geometries=geoms, crs=crs, getter=getter))
                continue
            else:
                geoms = [getter(geom) for geom in geoms]
                results = self._along_planar(
                    feats, geometries=to_eqd(geoms), crs=prj, getter=nada)
                if not results:  # pragma: no cover
                    continue
                points, attributes = zip(*results)
                records.extend([(pt, attrs) for pt, attrs in
                                zip(from_eqd(points), attributes)])
        return records
    # End _along_geodesic method
# End AbstractQueryGeneratePointsAlongLines class


class QueryGeneratePointsAlongLinesPercentage(
        AbstractQueryGeneratePointsAlongLines):
    """
    Query for Generate Points Along Lines using Percentage Placement
    """
    @cached_property
    def distance_type(self) -> DistanceTypeOption:
        """
        Distance Type
        """
        return self._crs_distance_type_check()
    # End distance_type property

    def _get_values(self, geoms: Union[list, 'GeometrySequence'],
                    total_length: float, crs: 'CRS',
                    distance: Any) -> 'ndarray':
        """
        Get Values
        """
        # noinspection bad-assignment
        percent: float = self._config.distance
        if percent is None or isnan(percent) or percent <= 0 or percent >= 100:
            self._counter += 1
            return array([], dtype=float)
        return arange(percent, 100, percent) * total_length / 100
    # End _get_values method
# End QueryGeneratePointsAlongLinesPercentage class


class QueryGeneratePointsAlongLinesDistance(
        AbstractQueryGeneratePointsAlongLines):
    """
    Query for Generate Points Along Lines using Distance Placement
    """
    def _get_values(self, geoms: Union[list, 'GeometrySequence'],
                    total_length: float, crs: 'CRS',
                    distance: Any) -> 'ndarray':
        """
        Get Values
        """
        # noinspection bad-argument-type
        return self._build_range(
            geoms, total_length=total_length, crs=crs,
            unit=self._config.distance)
    # End _get_values method
# End QueryGeneratePointsAlongLinesDistance class


class QueryGeneratePointsAlongLinesField(
        AbstractQueryGeneratePointsAlongLines):
    """
    Query for Generate Points Along Lines using Field Placement
    """
    def _get_select_fields(self, element: 'FeatureClass') -> FIELDS:
        """
        Get Select Fields
        """
        primary = element.primary_key_field
        # noinspection bad-return
        return [primary, self._config.distance]
    # End _get_select_fields method

    def _get_values(self, geoms: Union[list, 'GeometrySequence'],
                    total_length: float, crs: 'CRS',
                    distance: Any) -> 'ndarray':
        """
        Get Values
        """
        if distance is None:
            self._counter += 1
            return array([], dtype=float)
        if self._is_numeric_field:
            unit = self._source_unit_cls(distance)
            return self._build_range(
                geoms, total_length=total_length, crs=crs, unit=unit)
        if SEMI not in distance:
            unit = unit_factory(distance)
            return self._build_range(
                geoms, total_length=total_length, crs=crs, unit=unit)
        return self._build_multi_values(geoms, total_length, crs, distance)
    # End _get_values method
# End QueryGeneratePointsAlongLinesField class


if __name__ == '__main__':  # pragma: no cover
    pass
