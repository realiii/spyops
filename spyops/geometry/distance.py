# -*- coding: utf-8 -*-
"""
Distance
"""


from bisect import bisect_left
from collections import defaultdict
from functools import lru_cache
from operator import itemgetter
from typing import Callable, TYPE_CHECKING, TypeAlias

from fudgeo.enumeration import ShapeType
from numpy import isfinite
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


def get_equidistant_details(geometries: 'ndarray', *, crs: 'CRS',
                            has_z: bool, has_m: bool) \
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
            crs, equidistant_crs=prj, has_z=has_z, has_m=has_m)
        to_eqd, from_eqd = transformers
        details.append((indexes, prj, to_eqd, from_eqd))
    return details
# End get_equidistant_details function


def interpolate_locations(values: 'ndarray', *, lengths: 'ndarray',
                          coordinates: 'ndarray', ids: tuple[int, ...],
                          fid: int, include_ends: bool) -> RECORDS:
    """
    Interpolate Locations
    """
    grouped = _group_by_line_index(lengths, values=values)
    records = _build_locations(
        grouped, coordinates=coordinates, ids=ids, lengths=lengths,
        offset=int(include_ends), fid=fid)
    if include_ends:
        _add_end_locations(coordinates, ids=ids, records=records, fid=fid,
                           total_length=lengths[-1])
    return records
# End interpolate_locations method


def _build_locations(grouped: defaultdict[int, list], coordinates: 'ndarray',
                     ids: tuple[int, ...], lengths: 'ndarray',
                     offset: int, fid: int) -> RECORDS:
    """
    Build Locations along Lines
    """
    records = []
    counter = offset
    for index, values in sorted(grouped.items()):
        try:
            coords = coordinates[ids[index]:ids[index + 1]]
        except IndexError:
            continue
        if not index:
            start_length = 0.
        else:
            start_length = lengths[index - 1]
        measured = MeasuredLine.from_coordinates_2d(coords, start_length)
        results = measured.interpolate(values, use_length=True)
        for pt, value in zip(results, values):
            x, y, *_ = pt
            if not isfinite((x, y)).all():
                continue
            counter += 1
            records.append((pt, fid, counter, value))
    return records
# End _build_locations method


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


def _group_by_line_index(lengths: 'ndarray', values: 'ndarray') \
        -> defaultdict[int, list]:
    """
    Group by Line Index, exclude end points and values outside the range.

    End points are defined as the first point on the first line and the last
    point on the last line, e.g. 0 length and max length.
    """
    values = [v for v in values if 0 < v < max(lengths)]
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
    indexes = 0, 1
    if has_z and has_m:
        indexes = *indexes, 2, 3
    elif has_z and not has_m:
        indexes = *indexes, 2
    elif not has_z and has_m:
        indexes = *indexes, 3
    getter = itemgetter(*indexes)
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.point][has_z, has_m]
    return from_wkb([cls.from_tuple(getter(coordinates), srs_id=SRS_ID_WKB).wkb
                     for coordinates, *_ in records])
# End make_points method


@lru_cache(maxsize=1000)
def _equidistant_transformers(crs: 'CRS', equidistant_crs: 'CRS',
                              has_z: bool, has_m: bool) \
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
        shape_type=ShapeType.point, has_z=has_z, has_m=has_m,
        transformer=from_equidistant_transformer)
    # noinspection PyTypeChecker
    return to_equidistant, from_equidistant
# End _equidistant_transformers function


if __name__ == '__main__':  # pragma: no cover
    pass
