# -*- coding: utf-8 -*-
"""
Centroid for Geometries with handling for Z and M
"""


from typing import Callable, TYPE_CHECKING

from bottleneck import anynan, move_mean, nanmean, nansum
from fudgeo.enumeration import ShapeType
from numpy import array, diff, hypot, ones_like
from shapely import get_rings
from shapely.coordinates import get_coordinates
from shapely.measurement import area, length

from spyops.geometry.util import find_slice_indexes, get_geoms


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray


def centroid_points(geoms: 'ndarray', *, has_z: bool, has_m: bool,
                    **kwargs) -> list:
    """
    Centroids for Points
    """
    return get_coordinates(geoms, include_z=has_z, include_m=has_m).tolist()
# End centroid_points function


def centroid_multi_points(geoms: 'ndarray', *, has_z: bool, has_m: bool,
                          **kwargs) -> list:
    """
    Centroids for MultiPoints
    """
    coords, indexes = get_coordinates(
        geoms, include_z=has_z, include_m=has_m, return_index=True)
    ids = find_slice_indexes(indexes)
    return [nanmean(coords[b:e], axis=0) for b, e in zip(ids[:-1], ids[1:])]
# End centroid_multi_points function


def centroid_linestrings(geoms: 'ndarray', has_z: bool, has_m: bool,
                         use_xy_length: bool) -> list:
    """
    Centroids for LineStrings
    """
    return _get_geometric_centers(
        geoms, has_z=has_z, has_m=has_m, use_xy_length=use_xy_length)
# End centroid_linestrings function


def centroid_multi_linestrings(geoms: 'ndarray', has_z: bool, has_m: bool,
                               use_xy_length: bool) -> list:
    """
    Centroids for MultiLineStrings, length weighting combines individual
    LineString centroids.
    """
    return _weighted_centroids(
        geoms, has_z=has_z, has_m=has_m, getter=get_geoms, weighter=length,
        use_xy_length=use_xy_length)
# End centroid_multi_linestrings function


def centroid_polygons(geoms: 'ndarray', has_z: bool, has_m: bool,
                      use_xy_length: bool) -> list:
    """
    Centroid for Polygons
    """
    return _weighted_centroids(
        geoms, has_z=has_z, has_m=has_m, getter=get_rings,
        weighter=_unit_weight, use_xy_length=use_xy_length)
# End centroid_polygons function


def centroid_multi_polygons(geoms: 'ndarray', has_z: bool, has_m: bool,
                            use_xy_length: bool) -> list:
    """
    Centroid for MultiPolygons, area weighting combines individual
    Polygon centroids.
    """
    centroids = []
    for geom in geoms:
        parts = get_geoms(geom)
        # noinspection PyTypeChecker
        weights = area(parts)
        # noinspection PyTypeChecker
        centers = array(_weighted_centroids(
            parts, has_z=has_z, has_m=has_m,
            getter=get_rings, weighter=_unit_weight,
            use_xy_length=use_xy_length), dtype=float).T
        centroids.append(nansum((weights * centers), axis=1) / nansum(weights))
    return centroids
# End centroid_multi_polygons function


def _get_geometric_centers(geoms: 'ndarray', has_z: bool, has_m: bool,
                           use_xy_length: bool) -> list:
    """
    Get Geometric Centers
    """
    centers = []
    coords, indexes = get_coordinates(
        geoms, include_z=has_z, include_m=has_m, return_index=True)
    ids = find_slice_indexes(indexes)
    for begin, end in zip(ids[:-1], ids[1:]):
        coordinates = coords[begin:end]
        middles = move_mean(coordinates, window=2, min_count=1, axis=0)[1:]
        deltas = diff(coordinates, axis=0)
        lengths = hypot(deltas[:, 0], deltas[:, 1])
        if not use_xy_length and has_z:
            zs = deltas[:, 2]
            if not anynan(zs):
                lengths = hypot(lengths, zs)
        if not (total_length := nansum(lengths)):
            lengths = ones_like(lengths, dtype=float)
            total_length = nansum(lengths)
        centers.append(nansum(lengths * middles.T, axis=1) / total_length)
    return centers
# End _get_geometric_centers function


def _weighted_centroids(geoms: 'ndarray', has_z: bool, has_m: bool,
                        getter: Callable, weighter: Callable,
                        use_xy_length: bool) -> list:
    """
    Weighted Centroids
    """
    centroids = []
    for geom in geoms:
        parts = getter(geom)
        weights = weighter(parts)
        centers = array(_get_geometric_centers(
            parts, has_z=has_z, has_m=has_m,
            use_xy_length=use_xy_length), dtype=float).T
        centroids.append(nansum((weights * centers), axis=1) / nansum(weights))
    return centroids
# End _weighted_centroids function


def _unit_weight(geoms: list) -> 'ndarray':
    """
    Unit Weight
    """
    return ones_like(geoms, dtype=float)
# End _unit_weight function


GEOMETRY_CENTROID: dict[str, Callable] = {
    ShapeType.point: centroid_points,
    ShapeType.multi_point: centroid_multi_points,
    ShapeType.linestring: centroid_linestrings,
    ShapeType.multi_linestring: centroid_multi_linestrings,
    ShapeType.polygon: centroid_polygons,
    ShapeType.multi_polygon: centroid_multi_polygons,
}


if __name__ == '__main__':  # pragma: no cover
    pass
