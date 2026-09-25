# -*- coding: utf-8 -*-
"""
Simplify Workaround
"""


from collections import Counter
from math import nan
from typing import Callable, Type

from fudgeo.enumeration import ShapeType
from numpy import arange, ndarray
from shapely import (
    MultiPoint, Point, from_wkb, get_rings, simplify as _simplify)

from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.util import get_coords_and_slices, get_geoms_iter, nada
from spyops.geometry.wa.util import ensure_iterable
from spyops.geometry.wa.uwa import USE_WORKAROUNDS
from spyops.shared.constant import SRS_ID_WKB


def simplify(geometry, tolerance, preserve_topology=True, **kwargs):
    """
    Simplify Workaround -- ensures measures are present
    """
    func = _simplify
    if USE_WORKAROUNDS.simplify:
        types = Point, MultiPoint
        if isinstance(geometry, (list, tuple, ndarray)):
            if not len(geometry):
                has_m = False
                is_point = True
            else:
                geoms = geometry[:(min(25, len(geometry)))]
                has_m = any(g.has_m for g in geoms)
                is_point = any(isinstance(g, types) for g in geoms)
        else:
            has_m = geometry.has_m
            is_point = isinstance(geometry, types)
        if not is_point and has_m:
            func = _simplify_with_measures
    # noinspection bad-argument-type
    return func(geometry, tolerance=tolerance,
                preserve_topology=preserve_topology, **kwargs)
# End simplify function


def _simplify_with_measures(geometry, *, tolerance: float,
                            preserve_topology: bool = True, **kwargs):
    """
    Simplify Workaround -- ensures measures are present
    """
    is_iterable, geometries = ensure_iterable(geometry)
    geoms = geometries[:(min(25, len(geometries)))]
    has_z = any(g.has_z for g in geoms)
    (geom_type, _), = Counter([g.geom_type for g in geoms]).most_common(1)
    shape_type = geom_type.upper()
    if shape_type not in GEOMETRY_SIMPLIFY:
        result = geometries
    else:
        func = GEOMETRY_SIMPLIFY[shape_type]
        result = func(
            geometries, tolerance=tolerance,
            preserve_topology=preserve_topology,
            has_z=has_z, **kwargs)
    if not is_iterable:
        return result[0]
    return result
# End _simplify_with_measures function


def _simplify_config(shape_type: str, has_z: bool) \
        -> tuple[tuple[float, ...], Type, Type]:
    """
    Common Config Steps for Simplify
    """
    if has_z:
        missing = nan, nan
    else:
        missing = nan,
    cls_idx = FUDGEO_GEOMETRY_LOOKUP[shape_type][True, False]
    cls_geom = FUDGEO_GEOMETRY_LOOKUP[shape_type][has_z, True]
    return missing, cls_geom, cls_idx
# End _simplify_config function


def _build_xy_and_lookup(geoms: list, has_z: bool, max_id: int,
                         getter: Callable) \
        -> tuple[tuple[int, ...], dict[float, 'ndarray'], 'ndarray']:
    """
    Build XY and Lookup, also return identifier indexes
    """
    coords, ids = get_coords_and_slices(
        getter(geoms), include_z=has_z, include_m=True)
    xy_index = coords[:, :3].copy()
    xy_index[:, 2] = arange(len(xy_index), dtype=float) + max_id
    lookup = dict(zip(xy_index[:, 2], coords[:, 2:]))
    return ids, lookup, xy_index
# End _build_xy_and_lookup function


def _rebuild_coordinates(geoms: 'ndarray', lookup: dict[float, 'ndarray'],
                         missing: tuple[float, ...], getter: Callable) \
        -> tuple[list, tuple[int, ...]]:
    """
    Rebuild Coordinates by using lookup to add back measures and z values
    """
    coords, ids = get_coords_and_slices(
        getter(geoms), include_z=True, include_m=False)
    coords = [(x, y, *lookup.get(idx, missing)) for x, y, idx in coords]
    return coords, ids
# End _rebuild_coordinates function


def _simplify_linestrings(geoms: list, *, tolerance: float,
                          preserve_topology: bool, has_z: bool,
                          **kwargs) -> 'ndarray':
    """
    Simplify LineStrings that have Measures
    """
    getter = nada
    missing, cls_geom, cls_idx = _simplify_config(ShapeType.linestring, has_z)
    ids, lookup, xy_index = _build_xy_and_lookup(
        geoms, has_z=has_z, max_id=0, getter=getter)
    wkb = [cls_idx(xy_index[b:e], srs_id=SRS_ID_WKB).wkb
           for b, e in zip(ids[:-1], ids[1:])]
    geoms = _simplify(from_wkb(wkb, on_invalid='fix'), tolerance=tolerance,
                      preserve_topology=preserve_topology, **kwargs)
    coords, ids = _rebuild_coordinates(
        geoms, lookup=lookup, missing=missing, getter=getter)
    wkb = [cls_geom(coords[b:e], srs_id=SRS_ID_WKB).wkb
           for b, e in zip(ids[:-1], ids[1:])]
    return from_wkb(wkb, on_invalid='fix')
# End _simplify_linestrings function


def _simplify_multi_linestrings(geoms: list, *, tolerance: float,
                                preserve_topology: bool, has_z: bool,
                                **kwargs) -> 'ndarray':
    """
    Simplify MultiLineStrings that have Measures
    """
    return _simplify_groups(
        geoms, tolerance=tolerance, preserve_topology=preserve_topology,
        shape_type=ShapeType.multi_linestring, has_z=has_z,
        getter=get_geoms_iter, **kwargs)
# End _simplify_multi_linestrings function


def _simplify_polygons(geoms: list, *, tolerance: float,
                       preserve_topology: bool, has_z: bool,
                       **kwargs) -> 'ndarray':
    """
    Simplify Polygons that have Measures
    """
    return _simplify_groups(
        geoms, tolerance=tolerance, preserve_topology=preserve_topology,
        shape_type=ShapeType.polygon, has_z=has_z, getter=get_rings,
        **kwargs)
# End _simplify_polygons function


def _simplify_multi_polygons(geoms: list, *, tolerance: float,
                             preserve_topology: bool, has_z: bool,
                             **kwargs) -> 'ndarray':
    """
    Simplify MultiPolygons that have Measures
    """
    wkb = []
    max_id = 0
    lookup = {}
    poly_coords = []
    getter = get_rings
    missing, cls_geom, cls_idx = _simplify_config(
        ShapeType.multi_polygon, has_z)
    for geom in geoms:
        for poly in get_geoms_iter(geom):
            ids, lut, xy_index = _build_xy_and_lookup(
                poly, has_z=has_z, max_id=max_id, getter=getter)
            lookup.update(lut)
            max_id += max(ids)
            poly_coords.append(
                [xy_index[b:e] for b, e in zip(ids[:-1], ids[1:])])
        wkb.append(cls_idx(poly_coords, srs_id=SRS_ID_WKB).wkb)
        poly_coords.clear()
    geoms = _simplify(from_wkb(wkb, on_invalid='fix'), tolerance=tolerance,
                      preserve_topology=preserve_topology, **kwargs)
    wkb = []
    for geom in geoms:
        for poly in get_geoms_iter(geom):
            coords, ids = _rebuild_coordinates(
                poly, lookup=lookup, missing=missing, getter=getter)
            poly_coords.append(
                [coords[b:e] for b, e in zip(ids[:-1], ids[1:])])
        wkb.append(cls_geom(poly_coords, srs_id=SRS_ID_WKB).wkb)
        poly_coords.clear()
    return from_wkb(wkb, on_invalid='fix')
# End _simplify_multi_polygons function


def _simplify_groups(geoms: list, *, tolerance: float,
                     preserve_topology: bool, shape_type: str,
                     has_z: bool, getter: Callable, **kwargs) -> 'ndarray':
    """
    Simplify Groups (Multi LineStrings and Polygons) that have Measures
    """
    wkb = []
    max_id = 0
    lookup = {}
    missing, cls_geom, cls_idx = _simplify_config(shape_type, has_z)
    for geom in geoms:
        ids, lut, xy_index = _build_xy_and_lookup(
            geom, has_z=has_z, max_id=max_id, getter=getter)
        lookup.update(lut)
        max_id += max(ids)
        wkb.append(cls_idx([xy_index[b:e] for b, e in
                            zip(ids[:-1], ids[1:])], srs_id=SRS_ID_WKB).wkb)
    geoms = _simplify(from_wkb(wkb, on_invalid='fix'), tolerance=tolerance,
                      preserve_topology=preserve_topology, **kwargs)
    wkb = []
    for geom in geoms:
        coords, ids = _rebuild_coordinates(
            geom, lookup=lookup, missing=missing, getter=getter)
        wkb.append(cls_geom([coords[b:e] for b, e in zip(ids[:-1], ids[1:])],
                            srs_id=SRS_ID_WKB).wkb)
    return from_wkb(wkb, on_invalid='fix')
# End _simplify_groups function


GEOMETRY_SIMPLIFY: dict[str, Callable] = {
    ShapeType.linestring: _simplify_linestrings,
    ShapeType.multi_linestring: _simplify_multi_linestrings,
    ShapeType.polygon: _simplify_polygons,
    ShapeType.multi_polygon: _simplify_multi_polygons,
}


if __name__ == '__main__':  # pragma: no cover
    pass
