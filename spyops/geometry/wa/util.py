# -*- coding: utf-8 -*-
"""
Utility Functions in support of Workarounds
"""


from collections import Counter, defaultdict
from functools import cache
from math import nan
from operator import itemgetter
from typing import Callable, TYPE_CHECKING, TypeAlias, Union

from bottleneck import nanmean
from numpy import ndarray
from shapely import (
    LineString, LinearRing, MultiLineString, MultiPoint, Polygon,
    get_coordinates, get_rings)

from spyops.geometry.util import (
    get_coords_and_slices, get_geoms, get_geoms_iter)


if TYPE_CHECKING:  # pragma: no cover
    from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry


GEOM: TypeAlias = Union[ndarray, list['BaseGeometry'],
                        tuple['BaseGeometry', ...], 'BaseGeometry']


def ensure_iterable(geom: GEOM) -> tuple[bool, list]:
    """
    Ensure working with an iterable and not just a geometry
    """
    if not (is_iterable := isinstance(geom, (list, tuple, ndarray))):
        geom = [geom]
    # noinspection bad-return
    return is_iterable, geom
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
        return _build_linear(
            result, getter=getter, has_z=has_z, slicer=slicer, lookup=lookup)
    else:
        coords = []
        getter = get_rings
        # noinspection PyTypeChecker
        for part in get_geoms(result):
            coords.append(_build_linear(
                part, getter=getter, has_z=has_z, slicer=slicer, lookup=lookup))
        return coords
# End build_coordinates function


def _build_linear(geom: Polygon | MultiLineString | LinearRing,
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
# End _build_linear function


def linestring_measures_to_zs(geoms: Union[ndarray, list[LineString]]) \
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


def polygon_measures_to_zs(geoms: Union[ndarray, list[Polygon]]) \
        -> list[Polygon]:
    """
    Move the Measures of a Polygon to the Z axis, reducing to PolygonZ
    from PolygonZM or changing from PolygonM to PolygonZ.
    """
    polygons = []
    for geom in geoms:
        coords, ids = get_coords_and_slices(
            get_rings(geom), include_z=False, include_m=True)
        shell, *holes = [coords[b:e] for b, e in zip(ids[:-1], ids[1:])]
        # NOTE the current behaviour when passing triplets is for a PolygonZ
        #  to be generated, in this case the Z values are measures
        polygons.append(Polygon(shell=shell, holes=holes))
    return polygons
# End polygon_measures_to_zs function


def check_has_measure(geom: GEOM) -> bool:
    """
    Check if geometry or sequence of geometries has measures
    """
    if isinstance(geom, (list, tuple, ndarray)):
        if not len(geom):
            return False
        else:
            geoms = geom[:(min(25, len(geom)))]
            # noinspection unresolved-references
            return any(g.has_m for g in geoms)
    else:
        return geom.has_m
# End check_has_measure function


def get_shape_type_from_geom(geoms: list['BaseGeometry']) -> str:
    """
    Get Shape Type from Geometry
    """
    (geom_type, _), = Counter([g.geom_type for g in geoms]).most_common(1)
    return geom_type.upper()
# End get_shape_type_from_geom function


if __name__ == '__main__':  # pragma: no cover
    pass
