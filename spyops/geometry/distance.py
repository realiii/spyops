# -*- coding: utf-8 -*-
"""
Distance
"""


from bisect import bisect_left
from collections import defaultdict
from functools import lru_cache
from math import cos, radians, sin
from operator import itemgetter
from typing import Any, Callable, NamedTuple, TYPE_CHECKING

from fudgeo.enumeration import ShapeType
from numpy import arctan2, array, cos, degrees, diff, isfinite, radians, sin
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


class PointRecord(NamedTuple):
    """
    Point Record
    """
    coords: list
    orig_fid: int
    seq_num: int
    along: float
# End PointRecord class


class TransectRecord(NamedTuple):
    """
    Transect Record
    """
    coords: list
    orig_fid: int
    seq_num: int
    along: float
    angle: float
# End TransectRecord class


class LineRecord(NamedTuple):
    """
    Line Record (begin and end points)
    """
    begin: list
    end: list
    orig_fid: int
    seq_num: int
    along: float
    angle: float
# End LineRecord class


class CenterlineRecord(NamedTuple):
    """
    Centerline Record
    """
    begin: list
    end: list
    orig_fid: int
    seq_num: int
    begin_along: float
    end_along: float
    angle: float
# End CenterlineRecord class


class CenterlineExtendedRecord(NamedTuple):
    """
    Centerline Extended Record
    """
    begin: list
    end: list
    orig_fid: int
    seq_num: int
    begin_along: float
    end_along: float
    angle: float
    prev_num: int | None
    next_num: int | None
# End CenterlineExtendedRecord class


class RectangleRecord(NamedTuple):
    """
    Rectangle Record
    """
    pt1: list
    pt2: list
    pt3: list
    pt4: list
    orig_fid: int
    seq_num: int
    begin_along: float
    end_along: float
    angle: float
    prev_num: int
    next_num: int
# End RectangleRecord class


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
                          fid: int, include_ends: bool) -> list[PointRecord]:
    """
    Interpolate Locations
    """
    grouped = _group_by_line_index(lengths, distances=distances)
    records = _build_locations(
        grouped, coordinates=coordinates, ids=ids, lengths=lengths,
        offset=int(include_ends), fid=fid)
    if include_ends:
        _add_end_locations(coordinates, ids=ids, records=records, fid=fid,
                           total_length=max(lengths))
    return records
# End interpolate_locations method


def interpolate_transects(distances: 'ndarray', length: float, *,
                          lengths: 'ndarray', coordinates: 'ndarray',
                          ids: tuple[int, ...], fid: int,
                          include_ends: bool) -> list[LineRecord]:
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
            total_length=max(lengths))
    # noinspection argument-list
    return [LineRecord(*(*_transect_coordinates(length, rec.coords, rec.angle),
                         *rec[1:])) for rec in records]
# End interpolate_transects method


def interpolate_rectangles(distances: 'ndarray', length: float,
                           width: float, *, lengths: 'ndarray',
                           coordinates: 'ndarray', ids: tuple[int, ...],
                           fid: int, include_ends: bool) -> list[RectangleRecord]:
    """
    Interpolate Rectangles, Line Coordinates and Angles
    """
    grouped = _group_by_line_indexes(
        lengths, distances=distances, length=length, include_ends=include_ends)
    records = _build_loc_pairs_with_angles(
        grouped, coordinates=coordinates, ids=ids, lengths=lengths,
        length=length, fid=fid)
    # noinspection argument-list
    return [RectangleRecord(*(*_rectangle_coordinates(width, rec),
                              *rec[2:])) for rec in records]
# End interpolate_transects method


def _transect_coordinates(length: float, location: list,
                          angle: float) -> list[list]:
    """
    Calculate Transect Coordinates for Start and End
    """
    places = 9
    x, y, *zm = location
    dx = round(cos(radians(angle + 90)) * length / 2, places)
    dy = round(sin(radians(angle + 90)) * length / 2, places)
    return [[x - dx, y - dy, *zm], [x + dx, y + dy, *zm]]
# End _transect_coordinates function


def _rectangle_coordinates(width: float,
                           rec: CenterlineExtendedRecord) -> list[list]:
    """
    Calculate Rectangle Coordinates from Start and End Locations and a Width
    """
    first, second = _transect_coordinates(
        width, location=rec.begin, angle=rec.angle)
    fourth, third = _transect_coordinates(
        width, location=rec.end, angle=rec.angle)
    return [first, second, third, fourth]
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
                     offset: int, fid: int) -> list[PointRecord]:
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
            records.append(PointRecord(
                coords=pt, orig_fid=fid, seq_num=counter, along=value))
    return records
# End _build_locations method


def _build_locs_with_angles(grouped: defaultdict[int, list],
                            coordinates: 'ndarray', ids: tuple[int, ...],
                            lengths: 'ndarray', offset: int,
                            fid: int) -> list[TransectRecord]:
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
            records.append(TransectRecord(
                coords=pt, orig_fid=fid, seq_num=counter,
                along=value, angle=angle))
    return records
# End _build_locs_with_angles method


def _build_loc_pairs_with_angles(
        grouped: defaultdict[tuple[int, int], list[tuple[float, float]]],
        coordinates: 'ndarray', ids: tuple[int, ...], lengths: 'ndarray',
        length: float, fid: int) -> list[CenterlineExtendedRecord]:
    """
    Build Location Pairs along Lines, Find the Direction of the line that
    passes through the location pair.
    """
    counter = 0
    records = []
    measured_lines = {}
    line_count = len(lengths)
    for (start_index, end_index), values in sorted(grouped.items()):
        starts, ends = zip(*values)
        start_pts = _interpolate_values(
            start_index, values=starts, coordinates=coordinates, ids=ids,
            lengths=lengths, measured_lines=measured_lines,
            line_count=line_count)
        end_pts = _interpolate_values(
            end_index, values=ends, coordinates=coordinates, ids=ids,
            lengths=lengths, measured_lines=measured_lines,
            line_count=line_count)
        for start_pt, end_pt, (start, end) in zip(start_pts, end_pts, values):
            start_x, start_y, *_ = start_pt
            end_x, end_y, *end_zm = end_pt
            if not isfinite((start_x, start_y, end_x, end_y)).all():
                continue
            angle = degrees(arctan2(end_y - start_y, end_x - start_x))
            if end_index >= line_count:
                rads = radians(angle)
                end_x = start_x + (length * cos(rads))
                end_y = start_y + (length * sin(rads))
                end_pt = end_x, end_y, *end_zm
                end = max(lengths)
            counter += 1
            records.append(CenterlineRecord(
                begin=start_pt, end=list(end_pt), orig_fid=fid, seq_num=counter,
                begin_along=start, end_along=end, angle=angle))
    return _add_previous_and_next(counter, records)
# End _build_loc_pairs_with_angles method


def _add_previous_and_next(counter: int, records: list[CenterlineRecord]) \
        -> list[CenterlineExtendedRecord]:
    """
    Add Previous and Next Sequence Numbers to Records
    """
    extended = []
    for start_pt, end_pt, fid, seq, start, end, angle in records:
        if seq == 1:
            prev_ = None
            if counter > 1:
                next_ = 2
            else:
                next_ = None
        elif seq == counter:
            next_ = None
            if counter > 1:
                prev_ = counter - 1
            else:
                prev_ = None
        else:
            prev_ = seq - 1
            next_ = seq + 1
        extended.append(
            CenterlineExtendedRecord(
                begin=start_pt, end=end_pt, orig_fid=fid, seq_num=seq,
                begin_along=start, end_along=end, angle=angle,
                prev_num=prev_, next_num=next_))
    return extended
# End _add_previous_and_next method


def _interpolate_values(index: int, values: list[float], coordinates: 'ndarray',
                        ids: tuple[int, ...], lengths: 'ndarray',
                        measured_lines: dict[Any, Any],
                        line_count: int) -> 'ndarray':
    """
    Interpolate Values along a Measured Line
    """
    if index >= line_count:
        return array([coordinates[-1]] * len(values), dtype=float)
    if not (line := measured_lines.get(index)):
        line = _make_measured_line(
            index, coordinates=coordinates, ids=ids, lengths=lengths)
        measured_lines[index] = line
    return line.interpolate(values, use_length=True)
# End _interpolate_values method


def _add_end_locations(coordinates: 'ndarray', ids: tuple[int, ...],
                       records: list[PointRecord], fid: int, total_length: float) -> None:
    """
    Add end locations

    End points are defined as the first point on the first line and the last
    point on the last line.
    """
    pt = coordinates[ids[0]:ids[1]][0]
    records.insert(0, PointRecord(coords=pt, orig_fid=fid, seq_num=1, along=0.))
    pt = coordinates[ids[-2]:ids[-1]][-1]
    records.append(PointRecord(
        coords=pt, orig_fid=fid, seq_num=len(records) + 1, along=total_length))
# End _add_end_locations method


def _add_end_locs_with_angles(coordinates: 'ndarray', ids: tuple[int, ...],
                              records: list[TransectRecord], fid: int,
                              total_length: float) -> None:
    """
    Add end locations with angles

    End points are defined as the first point on the first line and the last
    point on the last line.  Calculate the angles.
    """
    coords = coordinates[ids[0]:ids[1]]
    angles = degrees(arctan2(diff(coords[:, 1]), diff(coords[:, 0])))
    records.insert(0, TransectRecord(
        coords=coords[0], orig_fid=fid, seq_num=1, along=0., angle=angles[0]))
    coords = coordinates[ids[-2]:ids[-1]]
    angles = degrees(arctan2(diff(coords[:, 1]), diff(coords[:, 0])))
    records.append(TransectRecord(
        coords=coords[-1], orig_fid=fid, seq_num=len(records) + 1,
        along=total_length, angle=angles[-1]))
# End _add_end_locs_with_angles method


def _group_by_line_index(lengths: 'ndarray', distances: 'ndarray') \
        -> defaultdict[int, list]:
    """
    Group by Line Index, exclude distances outside the length range.

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


def _group_by_line_indexes(lengths: 'ndarray', distances: 'ndarray',
                           length: float, include_ends: bool) \
        -> defaultdict[tuple[int, int], list[tuple[float, float]]]:
    """
    Group by Line Indexes, exclude start and end distances outside the range
    when include_ends is False.

    End points are defined as the first point on the first line and the last
    point on the last line, e.g. 0 length and max length.
    """
    max_len = max(lengths)
    if not include_ends:
        values = [d for d in distances
                  if (0 < d < max_len) and (0 < (d + length) < max_len)]
    else:
        values = [0, *[d for d in distances if d < max_len]]
    starts = [bisect_left(lengths, value) for value in values]
    ends = [bisect_left(lengths, value + length) for value in values]
    grouped = defaultdict(list)
    for start, end, value in zip(starts, ends, values):
        grouped[start, end].append((value, value + length))
    return grouped
# End _group_by_line_indexes function


def make_points(records: list[PointRecord], *,
                has_z: bool, has_m: bool) -> 'ndarray':
    """
    Make Points from Coordinate Lists
    """
    getter = itemgetter(*_get_dimension_indexes(has_z=has_z, has_m=has_m))
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.point][has_z, has_m]
    return from_wkb([cls.from_tuple(getter(coordinates), srs_id=SRS_ID_WKB).wkb
                     for coordinates, *_ in records])
# End make_points method


def make_lines(records: list[LineRecord], *,
               has_z: bool, has_m: bool) -> 'ndarray':
    """
    Make Lines from Coordinate Lists
    """
    getter = itemgetter(*_get_dimension_indexes(has_z=has_z, has_m=has_m))
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.linestring][has_z, has_m]
    return from_wkb([cls([getter(rec.begin), getter(rec.end)],
                         srs_id=SRS_ID_WKB).wkb for rec in records])
# End make_lines method


def make_rectangles(records: list[RectangleRecord], *,
                    has_z: bool, has_m: bool) -> 'ndarray':
    """
    Make Rectangles from Coordinate Lists
    """
    getter = itemgetter(*_get_dimension_indexes(has_z=has_z, has_m=has_m))
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.polygon][has_z, has_m]
    return from_wkb([cls([[getter(rec.pt1), getter(rec.pt2), getter(rec.pt3),
                           getter(rec.pt4), getter(rec.pt1)]],
                         srs_id=SRS_ID_WKB).wkb for rec in records])
# End make_rectangles method


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
