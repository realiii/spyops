# -*- coding: utf-8 -*-
"""
Queries for Sampling
"""


from abc import abstractmethod
from functools import cache, cached_property
from typing import Any, Callable, NamedTuple, TYPE_CHECKING, Union
from warnings import warn

from fudgeo.enumeration import ShapeType
from numpy import arange, array, cumsum, isfinite, isnan
from shapely import Point
from shapely.measurement import length

from spyops.crs.util import crs_from_srs
from spyops.geometry.convert import GEOMETRY_AS_MULTILINE
from spyops.geometry.distance import (
    get_equidistant_details, interpolate_locations, make_points)
from spyops.geometry.util import (
    get_coords_and_slices, get_geoms, nada,
    to_shapely)
from spyops.query.base import AbstractSourceQuery
from spyops.query.mixin import UnitTypeMixin
from spyops.shared.constant import SKIP_FILE_PREFIXES
from spyops.shared.enumeration import DistanceTypeOption
from spyops.shared.exception import DistanceCalculationWarning, UnitParseWarning
from spyops.shared.field import (
    ALONG, ORIG_FID, SEQ_NUM, get_geometry_column_name, make_field_names)
from spyops.shared.hint import FIELDS, PLACEMENT


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from numpy import ndarray
    from pyproj import CRS
    from shapely.geometry.base import GeometrySequence


class PlacementConfig(NamedTuple):
    """
    Placement Config
    """
    distance: PLACEMENT
    distance_type: DistanceTypeOption
    include_end_points: bool
# End PlacementConfig class


class AbstractQueryGeneratePointsAlongLines(AbstractSourceQuery, UnitTypeMixin):
    """
    Abstract Query Generate Points Along Lines
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass',
                 placement: PLACEMENT, include_end_points: bool,
                 where_clause: str, distance_type: DistanceTypeOption) -> None:
        """
        Initialize the AbstractQueryGeneratePointsAlongLines class
        """
        super().__init__(source, target=target, where_clause=where_clause)
        self._config: PlacementConfig = PlacementConfig(
            distance=placement, distance_type=distance_type,
            include_end_points=include_end_points)
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

    @property
    @abstractmethod
    def distance_type(self) -> DistanceTypeOption:
        """
        Distance Type
        """
        pass
    # End distance_type property

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

    def generate_points(self, features: list[tuple]) -> list[tuple]:
        """
        Generate Points
        """
        features, geometries = to_shapely(
            features, transformer=self.source_transformer)
        crs = crs_from_srs(self.spatial_reference_system)
        getter = GEOMETRY_AS_MULTILINE[self.source.shape_type]
        kwargs = dict(features=features, geometries=geometries,
                      crs=crs, getter=getter)
        if self.distance_type == DistanceTypeOption.PLANAR:
            return self._place_points_planar(**kwargs)
        return self._place_points_geodesic(**kwargs)
    # End generate_points method

    @abstractmethod
    def _get_values(self, geoms: Union[list, 'GeometrySequence'],
                    total_length: float, crs: 'CRS',
                    distance: Any) -> 'ndarray':  # pragma: no cover
        """
        Get Values
        """
        pass
    # End _get_values method

    def _place_points_planar(self, features: list[tuple],
                             geometries: 'ndarray', crs: 'CRS',
                             getter: Callable) -> list[tuple[Point, tuple]]:
        """
        Place Points Planar
        """
        records = []
        for (_, fid, distance), geom in zip(features, geometries):
            lines = get_geoms(getter(geom))
            # noinspection PyTypeChecker
            lengths = length(lines)
            mask = isfinite(lengths)
            if not mask.any():  # pragma: no cover
                continue
            lengths = cumsum(lengths[mask])
            total_length = lengths[-1]
            values = self._get_values(
                lines, total_length=total_length, crs=crs, distance=distance)
            coordinates, ids = get_coords_and_slices(
                lines, include_z=True, include_m=True)
            results = interpolate_locations(
                values, lengths=lengths, coordinates=coordinates, ids=ids,
                fid=fid, include_ends=self._config.include_end_points)
            records.extend(results)
        points = make_points(
            records, has_z=self.source.has_z, has_m=self.source.has_m)
        return [(pt, attrs) for pt, (_, *attrs) in zip(points, records)]
    # End _place_points_planar method

    def _place_points_geodesic(self, features: list[tuple],
                               geometries: 'ndarray', crs: 'CRS',
                               getter: Callable) -> list[tuple[Point, tuple]]:
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
                records.extend(self._place_points_planar(
                    feats, geometries=geoms, crs=crs, getter=getter))
                continue
            else:
                geoms = [getter(geom) for geom in geoms]
                results = self._place_points_planar(
                    feats, geometries=to_eqd(geoms), crs=prj, getter=nada)
                if not results:  # pragma: no cover
                    continue
                points, attributes = zip(*results)
                records.extend([(pt, attrs) for pt, attrs in
                                zip(from_eqd(points), attributes)])
        return records
    # End _place_points_geodesic method
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
        crs = crs_from_srs(self.spatial_reference_system)
        if not crs.is_projected:
            return DistanceTypeOption.GEODESIC
        return self._config.distance_type
    # End distance_type property

    def _get_values(self, geoms: Union[list, 'GeometrySequence'],
                    total_length: float, crs: 'CRS',
                    distance: Any) -> 'ndarray':  # pragma: no cover
        """
        Get Values
        """
        # noinspection bad-assignment
        percent: float = self._config.distance
        if isnan(percent) or percent <= 0 or percent >= 100:
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
    @cached_property
    def distance_type(self) -> DistanceTypeOption:
        """
        Distance Type
        """
        crs = crs_from_srs(self.spatial_reference_system)
        if not crs.is_projected:
            return DistanceTypeOption.GEODESIC
        has_linear, _ = self._unit_types
        if not has_linear:
            return DistanceTypeOption.GEODESIC
        return self._config.distance_type
    # End distance_type property

    def _get_values(self, geoms: Union[list, 'GeometrySequence'],
                    total_length: float, crs: 'CRS',
                    distance: Any) -> 'ndarray':  # pragma: no cover
        """
        Get Values
        """
        unit = self._config.distance
        is_geodesic = self.distance_type == DistanceTypeOption.GEODESIC
        # noinspection bad-assignment
        distance: float = self._convert_unit(
            is_geodesic, crs=crs, geoms=geoms, unit=unit, broadcast=False)
        if isnan(distance) or distance <= 0 or distance >= total_length:
            self._counter += 1
            return array([], dtype=float)
        return arange(distance, total_length, distance)
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
        return [primary, self._config.distance]
    # End _get_select_fields method
# End QueryGeneratePointsAlongLinesField class


if __name__ == '__main__':  # pragma: no cover
    pass
