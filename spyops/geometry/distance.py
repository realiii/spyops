# -*- coding: utf-8 -*-
"""
Distance
"""


from bisect import bisect_left
from collections import defaultdict
from functools import lru_cache
from math import cos, radians, sin
from operator import itemgetter
from typing import Callable, TYPE_CHECKING, TypeAlias

from fudgeo.enumeration import ShapeType
from numpy import arctan2, degrees, diff, isfinite
from numpy import cos, radians, sin
from shapely.constructive import centroid
from shapely.coordinates import get_coordinates
from shapely.io import from_wkb

from spyops.crs.transform import (
    get_transform_best_guess, make_transformer_function)
from spyops.crs.util import get_equidistant_projections
from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.measured import MeasuredLine
from spyops.shared.constant import SRS_ID_WKB


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray
    from pyproj import CRS


RECORDS: TypeAlias = list[tuple[list, int, int, float]]
RECORDS_AND_ANGLES: TypeAlias = list[tuple[list, int, int, float, float]]


def get_equidistant_details(geometries: 'ndarray', *, crs: 'CRS',
                            target_shape_type: str, has_z: bool, has_m: bool) \
        -> list[tuple[list[int], 'CRS', Callable | None, Callable | None]]:
    """
    Get Equidistant Projections and Transformers
    """
    coords = get_coordinates(centroid(geometries))
    projections = get_equidistant_projections(crs, coordinates=coords)
    grouped = defaultdict(list)
    for i, prj in enumerate(projections):
        grouped[prj].append(i)
    details = []
    for prj, indexes in grouped.items():
        if prj is None:
            continue
        transformers = _equidistant_transformers(
            crs, equidistant_crs=prj, target_shape_type=target_shape_type,
            has_z=has_z, has_m=has_m)
        to_eqd, from_eqd = transformers
        details.append((indexes, prj, to_eqd, from_eqd))
    return details
# End get_equidistant_details function


def interpolate_locations(distances: 'ndarray', *, lengths: 'ndarray',
                          coordinates: 'ndarray', ids: tuple[int, ...],
                          fid: int, include_ends: bool) -> RECORDS:
    """
    Interpolate Locations
    """
    grouped = _group_by_line_index(lengths, distances=distances)
    records = _build_locations(
        grouped, coordinates=coordinates, ids=ids, lengths=lengths,
        offset=int(include_ends), fid=fid)
    if include_ends:
        _add_end_locations(coordinates, ids=ids, records=records, fid=fid,
                           total_length=lengths[-1])
    return records
# End interpolate_locations method


def interpolate_transects(distances: 'ndarray', length: float, *,
                          lengths: 'ndarray', coordinates: 'ndarray',
                          ids: tuple[int, ...], fid: int,
                          include_ends: bool) -> RECORDS_AND_ANGLES:
    """
    Interpolate Transects, Line Coordinates and Angles
    """
    grouped = _group_by_line_index(lengths, distances=distances)
    records = _build_locs_with_angles(
        grouped, coordinates=coordinates, ids=ids, lengths=lengths,
        offset=int(include_ends), fid=fid)
    if include_ends:
        _add_end_locs_with_angles(
            coordinates, ids=ids, records=records, fid=fid,
            total_length=lengths[-1])
    # noinspection bad-return
    return [(_transect_coordinates(length, loc, attrs), *attrs)
            for loc, *attrs in records]
# End interpolate_transects method


def _transect_coordinates(length: float, location: list,
                          attributes: list) -> list[list]:
    """
    Calculate Transect Coordinates for Start and End
    """
    places = 9
    *_, angle = attributes
    x, y, *zm = location
    dx = round(cos(radians(angle + 90)) * length / 2, places)
    dy = round(sin(radians(angle + 90)) * length / 2, places)
    return [[x - dx, y - dy, *zm], [x + dx, y + dy, *zm]]
# End _transect_coordinates function


def _make_measured_line(index: int, coordinates: 'ndarray',
                        ids: tuple[int, ...], lengths: 'ndarray') \
        -> MeasuredLine | None:
    """
    Make Measured Line
    """
    try:
        coords = coordinates[ids[index]:ids[index + 1]]
    except IndexError:
        return None
    if not index:
        start_length = 0.
    else:
        start_length = lengths[index - 1]
    return MeasuredLine.from_coordinates_2d(coords, start_length=start_length)
# End _make_measured_line function


def _build_locations(grouped: defaultdict[int, list], coordinates: 'ndarray',
                     ids: tuple[int, ...], lengths: 'ndarray',
                     offset: int, fid: int) -> RECORDS:
    """
    Build Locations along Lines
    """
    records = []
    counter = offset
    for index, values in sorted(grouped.items()):
        if not (measured := _make_measured_line(
                index, coordinates=coordinates, ids=ids, lengths=lengths)):
            continue
        results = measured.interpolate(values, use_length=True)
        for pt, value in zip(results, values):
            x, y, *_ = pt
            if not isfinite((x, y)).all():
                continue
            counter += 1
            records.append((pt, fid, counter, value))
    return records
# End _build_locations method


def _build_locs_with_angles(grouped: defaultdict[int, list],
                            coordinates: 'ndarray', ids: tuple[int, ...],
                            lengths: 'ndarray', offset: int, fid: int) \
        -> RECORDS_AND_ANGLES:
    """
    Build Locations along Lines and Find the Direction for Each Location
    """
    records = []
    counter = offset
    for index, values in sorted(grouped.items()):
        if not (measured := _make_measured_line(
                index, coordinates=coordinates, ids=ids, lengths=lengths)):
            continue
        results = measured.interpolate(values, use_length=True)
        angles = measured.find_directions(values, use_length=True)
        for pt, value, angle in zip(results, values, angles):
            x, y, *_ = pt
            if not isfinite((x, y)).all():
                continue
            counter += 1
            records.append((pt, fid, counter, value, angle))
    return records
# End _build_locs_with_angles method


def _add_end_locations(coordinates: 'ndarray', ids: tuple[int, ...],
                       records: RECORDS, fid: int, total_length: float) -> None:
    """
    Add end locations

    End points are defined as the first point on the first line and the last
    point on the last line.
    """
    pt = coordinates[ids[0]:ids[1]][0]
    records.insert(0, (pt, fid, 1, 0.))
    pt = coordinates[ids[-2]:ids[-1]][-1]
    records.append((pt, fid, len(records) + 1, total_length))
# End _add_end_locations method


def _add_end_locs_with_angles(coordinates: 'ndarray', ids: tuple[int, ...],
                              records: RECORDS_AND_ANGLES, fid: int,
                              total_length: float) -> None:
    """
    Add end locations with angles

    End points are defined as the first point on the first line and the last
    point on the last line.  Calculate the angles.
    """

    coords = coordinates[ids[0]:ids[1]]
    angles = degrees(arctan2(diff(coords[:, 1]), diff(coords[:, 0])))
    records.insert(0, (coords[0], fid, 1, 0., angles[0]))
    coords = coordinates[ids[-2]:ids[-1]]
    angles = degrees(arctan2(diff(coords[:, 1]), diff(coords[:, 0])))
    records.append((coords[-1], fid, len(records) + 1, total_length, angles[-1]))
# End _add_end_locs_with_angles method


def _group_by_line_index(lengths: 'ndarray', distances: 'ndarray') \
        -> defaultdict[int, list]:
    """
    Group by Line Index, exclude end points and values outside the range.

    End points are defined as the first point on the first line and the last
    point on the last line, e.g. 0 length and max length.
    """
    values = [d for d in distances if 0 < d < max(lengths)]
    indexes = [bisect_left(lengths, value) for value in values]
    grouped = defaultdict(list)
    for index, value in zip(indexes, values):
        grouped[index].append(value)
    return grouped
# End _group_by_line_index function


def make_points(records: RECORDS, has_z: bool, has_m: bool) -> 'ndarray':
    """
    Make Points from Coordinate Lists
    """
    getter = itemgetter(*_get_dimension_indexes(has_z=has_z, has_m=has_m))
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.point][has_z, has_m]
    return from_wkb([cls.from_tuple(getter(coordinates), srs_id=SRS_ID_WKB).wkb
                     for coordinates, *_ in records])
# End make_points method


def make_lines(records: RECORDS, has_z: bool, has_m: bool) -> 'ndarray':
    """
    Make Lines from Coordinate Lists
    """
    getter = itemgetter(*_get_dimension_indexes(has_z=has_z, has_m=has_m))
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.linestring][has_z, has_m]
    return from_wkb([cls([getter(begin), getter(end)], srs_id=SRS_ID_WKB).wkb
                     for (begin, end), *_ in records])
# End make_lines method


def _get_dimension_indexes(has_z: bool, has_m: bool) -> tuple[int, ...]:
    indexes = 0, 1
    if has_z and has_m:
        indexes = *indexes, 2, 3
    elif has_z and not has_m:
        indexes = *indexes, 2
    elif not has_z and has_m:
        indexes = *indexes, 3
    return indexes
# End _get_dimension_indexes method


@lru_cache(maxsize=1000)
def _equidistant_transformers(crs: 'CRS', equidistant_crs: 'CRS',
                              target_shape_type: str, has_z: bool,
                              has_m: bool) \
        -> tuple[Callable, Callable] | tuple[None, None]:
    """
    Equidistant Transformers for Along Lines
    """
    to_equidistant_transformer = get_transform_best_guess(
        crs, target_crs=equidistant_crs, suppress=True)
    if not to_equidistant_transformer:
        return None, None
    to_equidistant = make_transformer_function(
        shape_type=ShapeType.multi_linestring, has_z=has_z, has_m=has_m,
        transformer=to_equidistant_transformer)
    from_equidistant_transformer = get_transform_best_guess(
        equidistant_crs, target_crs=crs, suppress=True)
    if not from_equidistant_transformer:
        return None, None
    from_equidistant = make_transformer_function(
        shape_type=target_shape_type, has_z=has_z, has_m=has_m,
        transformer=from_equidistant_transformer)
    # noinspection PyTypeChecker
    return to_equidistant, from_equidistant
# End _equidistant_transformers function


if __name__ == '__main__':  # pragma: no cover
    pass
