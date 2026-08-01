# -*- coding: utf-8 -*-
"""
Vertices from Geometries
"""


from collections import defaultdict
from functools import partial
from operator import itemgetter
from typing import Callable, TYPE_CHECKING

from fudgeo.enumeration import ShapeType
from shapely import LineString, get_z
from shapely.coordinates import get_coordinates
from shapely.linear import line_interpolate_point

from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.util import find_slice_indexes, to_shapely
from spyops.shared.hint import POINT


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray


def _vertices_points(features: list[tuple], **kwargs) \
        -> defaultdict[int, list[POINT]]:
    """
    Vertices from Points
    """
    vertices = defaultdict(list)
    for pt, fid in features:
        if pt.is_empty:
            continue
        vertices[fid].append(pt)
    return vertices
# End _vertices_point function


def _vertices_multi_points(features: list[tuple], getter: itemgetter) \
        -> defaultdict[int, list[POINT]]:
    """
    Vertices from MultiPoints
    """
    vertices = defaultdict(list)
    for multi, fid in features:
        if multi.is_empty:
            continue
        vertices[fid].extend(getter(multi.points))
    return vertices
# End _vertices_multi_points function


def _vertices_linestrings(features: list[tuple], getter: itemgetter) \
        -> defaultdict[int, list[POINT]]:
    """
    Vertices from LineStrings
    """
    vertices = defaultdict(list)
    for line, fid in features:
        if line.is_empty:
            continue
        vertices[fid].extend(getter(line.points))
    return vertices
# End _vertices_linestrings function


def _vertices_multi_linestrings(features: list[tuple], getter: itemgetter) \
        -> defaultdict[int, list[POINT]]:
    """
    Vertices from MultiLineStrings
    """
    vertices = defaultdict(list)
    for multi, fid in features:
        if multi.is_empty:
            continue
        for line in multi:
            if line.is_empty:
                continue
            vertices[fid].extend(getter(line.points))
    return vertices
# End _vertices_multi_linestrings function


def _vertices_polygons(features: list[tuple], getter: itemgetter) \
        -> defaultdict[int, list[POINT]]:
    """
    Vertices from Polygons
    """
    vertices = defaultdict(list)
    for poly, fid in features:
        if poly.is_empty:
            continue
        for ring in poly:
            if ring.is_empty:
                continue
            vertices[fid].extend(getter(ring.points))
    return vertices
# End _vertices_polygons function


def _vertices_multi_polygons(features: list[tuple], getter: itemgetter) \
        -> defaultdict[int, list[POINT]]:
    """
    Vertices from MultiPolygons
    """
    vertices = defaultdict(list)
    for multi, fid in features:
        if multi.is_empty:
            continue
        for poly in multi:
            if poly.is_empty:
                continue
            for ring in poly:
                if ring.is_empty:
                    continue
                vertices[fid].extend(getter(ring.points))
    return vertices
# End _vertices_multi_polygons function


def _middle_linear(features: list[tuple], *, has_z: bool, has_m: bool,
                   srs_id: int, is_ring: bool) -> defaultdict[int, list[POINT]]:
    """
    Middle for Point Collection that could be treated as a LineString
    """
    if not has_m:
        func = _middle_sans_measures
    else:
        func = _middle_with_measures
    return func(features, has_z=has_z, srs_id=srs_id, is_ring=is_ring)
# End _middle_linear function


def _middle_multi_linear(features: list[tuple], *, has_z: bool, has_m: bool,
                         srs_id: int, is_ring: bool) \
        -> defaultdict[int, list[POINT]]:
    """
    Middle for Each LineString in a MultiLineString or LinearRing in a Polygon
    """
    middles = defaultdict(list)
    for geom, fid in features:
        if geom.is_empty:
            continue
        data = [(line, fid) for line in geom if not line.is_empty]
        results = _middle_linear(
            data, has_z=has_z, has_m=has_m, srs_id=srs_id, is_ring=is_ring)
        for i, pts in results.items():
            middles[i].extend(pts)
    return middles
# End _middle_multi_linear function


def middle_multi_points(features: list[tuple], *, has_z: bool, has_m: bool,
                        srs_id: int) -> defaultdict[int, list[POINT]]:
    """
    Middle of a MultiPoint (treated as a connected LineString)
    """
    lines = []
    points = {}
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.linestring][has_z, has_m]
    for multi, fid in features:
        if multi.is_empty:
            continue
        if len(multi.coordinates) < 2:
            points[fid] = multi.points[:1]
            continue
        lines.append((cls(multi.coordinates, srs_id=srs_id), fid))
    middles = _middle_linear(
        lines, has_z=has_z, has_m=has_m, srs_id=srs_id, is_ring=False)
    middles.update(points)
    return middles
# End middle_multi_points function


def middle_linestrings(features: list[tuple], *, has_z: bool, has_m: bool,
                       srs_id: int) -> defaultdict[int, list[POINT]]:
    """
    Middle of a LineString (or LinearRing)
    """
    return _middle_linear(
        features, has_z=has_z, has_m=has_m, srs_id=srs_id, is_ring=False)
# End middle_linestrings function


def middle_multi_linestrings(features: list[tuple], *, has_z: bool, has_m: bool,
                             srs_id: int) -> defaultdict[int, list[POINT]]:
    """
    Middle of Each LineString in a MultiLineString
    """
    return _middle_multi_linear(
        features=features, has_z=has_z, has_m=has_m,
        srs_id=srs_id, is_ring=False)
# End middle_multi_linestrings function


def middle_polygons_rings(features: list[tuple], *, has_z: bool, has_m: bool,
                          srs_id: int) -> defaultdict[int, list[POINT]]:
    """
    Middle of Each Ring in a Polygon
    """
    return _middle_multi_linear(
        features, has_z=has_z, has_m=has_m, srs_id=srs_id, is_ring=True)
# End middle_polygons_rings function


def middle_multi_polygons_rings(features: list[tuple], *, has_z: bool,
                                has_m: bool, srs_id: int) \
        -> defaultdict[int, list[POINT]]:
    """
    Middle of Each Ring in a Polygon in a MultiPolygon
    """
    middles = defaultdict(list)
    for geom, fid in features:
        if geom.is_empty:
            continue
        data = [(poly, fid) for poly in geom if not poly.is_empty]
        middles.update(_middle_multi_linear(
            data, has_z=has_z, has_m=has_m, srs_id=srs_id, is_ring=True))
    return middles
# End middle_multi_polygons_rings function


def _middle_sans_measures(features: list[tuple], *, has_z: bool, srs_id: int,
                          is_ring: bool) -> defaultdict[int, list[POINT]]:
    """
    Middle without measures
    """
    middles = defaultdict(list)
    if not features:
        return middles
    has_m = False
    if is_ring:
        features = _rings_to_lines(
            features, has_z=has_z, has_m=has_m, srs_id=srs_id)
    features, geometries = to_shapely(features, transformer=None)
    points = line_interpolate_point(geometries, distance=0.5, normalize=True)
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.point][has_z, has_m]
    for geom, (_, fid) in zip(points, features):
        middles[fid].append(cls.from_wkb(geom.wkb, srs_id=srs_id))
    return middles
# End _middle_sans_measures function


def _rings_to_lines(features: list[tuple], has_z: bool, has_m: bool,
                    srs_id: int) -> list[tuple]:
    """
    Convert Rings to Lines
    """
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.linestring][has_z, has_m]
    return [(cls(g.coordinates, srs_id=srs_id), fid) for g, fid in features]
# End _rings_to_lines function


def _middle_with_measures(features: list[tuple], *, has_z: bool, srs_id: int,
                          is_ring: bool) -> defaultdict[int, list[POINT]]:
    """
    Middle with measures
    """
    middles = defaultdict(list)
    if not features:
        return middles
    has_m = True
    if is_ring:
        features = _rings_to_lines(
            features, has_z=has_z, has_m=has_m, srs_id=srs_id)
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.point][has_z, has_m]
    features, geometries = to_shapely(features, transformer=None)
    if not has_z:
        # NOTE measures are stored in Z because of LineString construction
        coordinates = get_coordinates(
            _interpolate_measures(geometries), include_z=True)
    else:
        points = line_interpolate_point(
            geometries, distance=0.5, normalize=True)
        coordinates = get_coordinates(points, include_z=has_z, include_m=has_m)
        # NOTE use get_z since measures in Z via LineString creation
        coordinates[:, -1] = get_z(_interpolate_measures(geometries))
    for coords, (_, fid) in zip(coordinates, features):
        middles[fid].append(cls.from_tuple(coords, srs_id=srs_id))
    return middles
# End _middle_with_measures function


def _interpolate_measures(geoms: 'ndarray') -> 'ndarray':
    """
    Interplate Measures
    """
    coordinates, indexes = get_coordinates(
        geoms, include_m=True, return_index=True)
    ids = find_slice_indexes(indexes)
    # NOTE the current behaviour when passing triplets is for a LineStringZ
    #  to be generated, in this case the Z values are measures
    lines = [LineString(coordinates[b:e]) for b, e in zip(ids[:-1], ids[1:])]
    return line_interpolate_point(lines, distance=0.5, normalize=True)
# End _interpolate_measures function


_ALL_GETTER = itemgetter(slice(None))
all_vertices_multi_points = partial(
    _vertices_multi_points, getter=_ALL_GETTER)
all_vertices_linestrings = partial(
    _vertices_linestrings, getter=_ALL_GETTER)
all_vertices_multi_linestrings = partial(
    _vertices_multi_linestrings, getter=_ALL_GETTER)
all_vertices_polygons = partial(
    _vertices_polygons, getter=_ALL_GETTER)
all_vertices_multi_polygons = partial(
    _vertices_multi_polygons, getter=_ALL_GETTER)

GEOMETRY_VERTICES_ALL: dict[str, Callable] = {
    ShapeType.point: _vertices_points,
    ShapeType.multi_point: all_vertices_multi_points,
    ShapeType.linestring: all_vertices_linestrings,
    ShapeType.multi_linestring: all_vertices_multi_linestrings,
    ShapeType.polygon: all_vertices_polygons,
    ShapeType.multi_polygon: all_vertices_multi_polygons,
}

_START_GETTER = itemgetter(slice(0, 1))
start_vertices_multi_points = partial(
    _vertices_multi_points, getter=_START_GETTER)
start_vertices_linestrings = partial(
    _vertices_linestrings, getter=_START_GETTER)
start_vertices_multi_linestrings = partial(
    _vertices_multi_linestrings, getter=_START_GETTER)
start_vertices_polygons = partial(
    _vertices_polygons, getter=_START_GETTER)
start_vertices_multi_polygons = partial(
    _vertices_multi_polygons, getter=_START_GETTER)

GEOMETRY_VERTICES_START: dict[str, Callable] = {
    ShapeType.point: _vertices_points,
    ShapeType.multi_point: start_vertices_multi_points,
    ShapeType.linestring: start_vertices_linestrings,
    ShapeType.multi_linestring: start_vertices_multi_linestrings,
    ShapeType.polygon: start_vertices_polygons,
    ShapeType.multi_polygon: start_vertices_multi_polygons,
}

_END_GETTER = itemgetter(slice(-1, None))
end_vertices_multi_points = partial(
    _vertices_multi_points, getter=_END_GETTER)
end_vertices_linestrings = partial(
    _vertices_linestrings, getter=_END_GETTER)
end_vertices_multi_linestrings = partial(
    _vertices_multi_linestrings, getter=_END_GETTER)
end_vertices_polygons = partial(
    _vertices_polygons, getter=_END_GETTER)
end_vertices_multi_polygons = partial(
    _vertices_multi_polygons, getter=_END_GETTER)

GEOMETRY_VERTICES_END: dict[str, Callable] = {
    ShapeType.point: _vertices_points,
    ShapeType.multi_point: end_vertices_multi_points,
    ShapeType.linestring: end_vertices_linestrings,
    ShapeType.multi_linestring: end_vertices_multi_linestrings,
    ShapeType.polygon: end_vertices_polygons,
    ShapeType.multi_polygon: end_vertices_multi_polygons,
}

# noinspection PyTypeChecker
_BOTH_ENDS_GETTER = itemgetter(0, -1)
both_ends_vertices_multi_points = partial(
    _vertices_multi_points, getter=_BOTH_ENDS_GETTER)
both_ends_vertices_linestrings = partial(
    _vertices_linestrings, getter=_BOTH_ENDS_GETTER)
both_ends_vertices_multi_linestrings = partial(
    _vertices_multi_linestrings, getter=_BOTH_ENDS_GETTER)
both_ends_vertices_polygons = partial(
    _vertices_polygons, getter=_BOTH_ENDS_GETTER)
both_ends_vertices_multi_polygons = partial(
    _vertices_multi_polygons, getter=_BOTH_ENDS_GETTER)

GEOMETRY_VERTICES_BOTH_ENDS: dict[str, Callable] = {
    ShapeType.point: _vertices_points,
    ShapeType.multi_point: both_ends_vertices_multi_points,
    ShapeType.linestring: both_ends_vertices_linestrings,
    ShapeType.multi_linestring: both_ends_vertices_multi_linestrings,
    ShapeType.polygon: both_ends_vertices_polygons,
    ShapeType.multi_polygon: both_ends_vertices_multi_polygons,
}

GEOMETRY_VERTICES_MIDDLE: dict[str, Callable] = {
    ShapeType.point: _vertices_points,
    ShapeType.multi_point: middle_multi_points,
    ShapeType.linestring: middle_linestrings,
    ShapeType.multi_linestring: middle_multi_linestrings,
    ShapeType.polygon: middle_polygons_rings,
    ShapeType.multi_polygon: middle_multi_polygons_rings,
}


if __name__ == '__main__':  # pragma: no cover
    pass
