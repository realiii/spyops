# -*- coding: utf-8 -*-
"""
Utility Functions in support of Workarounds
"""


from collections import defaultdict
from functools import cache
from math import nan
from operator import itemgetter
from typing import Any, Callable, Union

from bottleneck import nanmean
from numpy import ndarray
from shapely import (
    LineString, LinearRing, MultiLineString, MultiPoint, Polygon,
    get_coordinates, get_rings)
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry

from spyops.geometry.util import (
    get_coords_and_slices, get_geoms, get_geoms_iter)


def ensure_iterable(geometry: Any) -> tuple[bool, list]:
    """
    Ensure working with an iterable and not just a geometry
    """
    if not (is_iterable := isinstance(geometry, (list, tuple, ndarray))):
        geometry = [geometry]
    return is_iterable, geometry
# End ensure_iterable function


@cache
def get_slicer(*, has_z: bool, has_m: bool) -> itemgetter:
    """
    Get Slicer
    """
    return itemgetter(*range(2 + has_z + has_m))
# End get_slicer function


def build_coordinates(result: Union['BaseGeometry', 'BaseMultipartGeometry'],
                      has_z: bool, slicer: itemgetter,
                      lookup: defaultdict[tuple[float, ...], list[float]]) -> list:
    """
    Build Coordinates
    """
    if isinstance(result, (LineString, MultiPoint)):
        coordinates = get_coordinates(result, include_z=has_z)
        return [slicer((*key, nanmean(lookup.get(tuple(key), [nan]))))
                for key in coordinates]
    elif isinstance(result, (Polygon, MultiLineString)):
        if isinstance(result, Polygon):
            getter = get_rings
        else:
            getter = get_geoms_iter
        return build_linear_coordinates(
            result, getter=getter, has_z=has_z, slicer=slicer, lookup=lookup)
    else:
        coords = []
        getter = get_rings
        # noinspection PyTypeChecker
        for part in get_geoms(result):
            coords.append(build_linear_coordinates(
                part, getter=getter, has_z=has_z, slicer=slicer, lookup=lookup))
        return coords
# End build_coordinates function


def build_linear_coordinates(geom: Polygon | MultiLineString | LinearRing,
                             getter: Callable, has_z: bool, slicer: itemgetter,
                             lookup: defaultdict[tuple[float, ...], list[float]]) -> list:
    """
    Build Coordinates for Linear Geometry
    """
    coords = []
    coordinates, ids = get_coords_and_slices(
        getter(geom), include_z=has_z, include_m=False)
    for begin, end in zip(ids[:-1], ids[1:]):
        coords.append([slicer((*key, nanmean(lookup.get(tuple(key), [nan]))))
                       for key in coordinates[begin:end]])
    return coords
# End build_linear_coordinates function


def linestring_measures_to_zs(geoms: Union['ndarray', list[LineString]]) \
        -> list[LineString]:
    """
    Move the Measures of a LineString to the Z axis, reducing to LineStringZ
    from LineStringZM or changing from LineStringM to LineStringZ.
    """
    coords, ids = get_coords_and_slices(
        geoms, include_z=False, include_m=True)
    # NOTE the current behaviour when passing triplets is for a LineStringZ
    #  to be generated, in this case the Z values are measures
    return [LineString(coords[b:e]) for b, e in zip(ids[:-1], ids[1:])]
# End linestring_measures_to_zs function


def check_has_measure(geom) -> bool:
    """
    Check if geometry or sequence of geometries has measures
    """
    if isinstance(geom, (list, tuple, ndarray)):
        if not len(geom):
            has_m = False
        else:
            geoms = geom[:(min(25, len(geom)))]
            # noinspection unresolved-references
            has_m = any(g.has_m for g in geoms)
    else:
        has_m = geom.has_m
    return has_m
# End check_has_measure function


if __name__ == '__main__':  # pragma: no cover
    pass
