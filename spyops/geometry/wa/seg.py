# -*- coding: utf-8 -*-
"""
Segmentize Workaround
"""


from typing import Callable, TYPE_CHECKING

from fudgeo.enumeration import ShapeType
from numpy import asarray
from shapely import (
    MultiLineString, from_wkb, get_rings, segmentize as _segmentize)
from shapely.geometry.multipolygon import MultiPolygon

from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.util import get_coords_and_slices, get_geoms_iter
from spyops.geometry.wa.util import (
    check_has_measure, ensure_iterable,
    get_shape_type_from_geom, linestring_measures_to_zs, polygon_measures_to_zs)

from spyops.geometry.wa.uwa import USE_WORKAROUNDS
from spyops.shared.constant import EMPTY, MULTI, SRS_ID_WKB
from spyops.shared.hint import LINE_TYPE, POLY_TYPE


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray


def segmentize(geometry, max_segment_length, **kwargs):
    """
    Segmentize Workaround -- ensures measures are present
    """
    if USE_WORKAROUNDS.segmentize and check_has_measure(geometry):
        func = _segmentize_with_measures
    else:
        func = _segmentize
    # noinspection bad-argument-type
    return func(geometry, max_segment_length=max_segment_length, **kwargs)
# End segmentize function


def _segmentize_with_measures(geometry, max_segment_length, **kwargs):
    """
    Segmentize Workaround -- ensures measures are present
    """
    is_iterable, geometries = ensure_iterable(geometry)
    if not len(geometries):  # pragma: no cover
        return geometry
    geoms = geometries[:(min(25, len(geometries)))]
    shape_type = get_shape_type_from_geom(geoms)
    if shape_type not in GEOMETRY_SEGMENTIZE:  # pragma: no cover
        return geometry
    has_m = True
    has_z = any(g.has_z for g in geoms)
    cls = FUDGEO_GEOMETRY_LOOKUP[shape_type.replace(MULTI, EMPTY)][has_z, has_m]
    func = GEOMETRY_SEGMENTIZE[shape_type]
    result = func(geometries, max_segment_length=max_segment_length,
                  has_z=has_z, has_m=has_m, geom_cls=cls, **kwargs)
    if not is_iterable:  # pragma: no cover
        return result[0]
    return result
# End _segmentize_with_measures function


def _segmentize_linestrings(geometries, *, max_segment_length: float,
                            has_z: bool, has_m: bool,
                            geom_cls: LINE_TYPE, **kwargs) -> 'ndarray':
    """
    Segmentize for LineStrings
    """
    lines = _segmentize(
        linestring_measures_to_zs(geometries),
        max_segment_length=max_segment_length, **kwargs)
    coordinates, ids = get_coords_and_slices(
        lines, include_z=True, include_m=False)
    if has_z:
        lines = _segmentize(
            geometries, max_segment_length=max_segment_length, **kwargs)
        coords, _ = get_coords_and_slices(
            lines, include_z=has_z, include_m=has_m)
        coords[:, -1] = coordinates[:, -1]
        coordinates = coords
    # noinspection bad-argument-type
    return from_wkb([geom_cls(coordinates[b:e], srs_id=SRS_ID_WKB).wkb
                     for b, e in zip(ids[:-1], ids[1:])])
# End _segmentize_linestrings function


def _segmentize_multi_linestrings(geometries, *, max_segment_length: float,
                                  has_z: bool, has_m: bool,
                                  geom_cls: LINE_TYPE, **kwargs) -> 'ndarray':
    """
    Segmentize for MultiLineStrings
    """
    geoms = []
    for geometry in geometries:
        lines = _segmentize_linestrings(
            get_geoms_iter(geometry), max_segment_length=max_segment_length,
            has_z=has_z, has_m=has_m, geom_cls=geom_cls, **kwargs)
        geoms.append(MultiLineString(lines))
    return asarray(geoms, dtype=object)
# End _segmentize_multi_linestrings function


def _segmentize_polygons(geometries, *, max_segment_length: float,
                         has_z: bool, has_m: bool,
                         geom_cls: POLY_TYPE, **kwargs) -> 'ndarray':
    """
    Segmentize for Polygons
    """
    polygons = []
    polys_zs = _segmentize(
        polygon_measures_to_zs(geometries),
        max_segment_length=max_segment_length, **kwargs)
    if has_z:
        polys = _segmentize(
            geometries, max_segment_length=max_segment_length, **kwargs)
        for poly, poly_z in zip(polys, polys_zs):
            coords, ids = get_coords_and_slices(
                get_rings(poly), include_z=has_z, include_m=has_m)
            coords_z, _ = get_coords_and_slices(
                get_rings(poly_z), include_z=has_z, include_m=False)
            coords[:, -1] = coords_z[:, -1]
            polygons.append(geom_cls(
                [coords[b:e] for b, e in zip(ids[:-1], ids[1:])],
                srs_id=SRS_ID_WKB).wkb)
    else:
        for poly_z in polys_zs:
            coords, ids = get_coords_and_slices(
                get_rings(poly_z), include_z=True, include_m=False)
            polygons.append(geom_cls(
                [coords[b:e] for b, e in zip(ids[:-1], ids[1:])],
                srs_id=SRS_ID_WKB).wkb)
    # noinspection bad-argument-type
    return from_wkb(polygons)
# End _segmentize_polygons function


def _segmentize_multi_polygons(geometries, *, max_segment_length: float,
                               has_z: bool, has_m: bool,
                               geom_cls: POLY_TYPE, **kwargs) -> 'ndarray':
    """
    Segmentize for Multi Polygons
    """
    geoms = []
    for geometry in geometries:
        polys = _segmentize_polygons(
            get_geoms_iter(geometry), max_segment_length=max_segment_length,
            has_z=has_z, has_m=has_m, geom_cls=geom_cls, **kwargs)
        geoms.append(MultiPolygon(polys))
    return asarray(geoms, dtype=object)
# End _segmentize_multi_polygons function


GEOMETRY_SEGMENTIZE: dict[str, Callable] = {
    ShapeType.linestring: _segmentize_linestrings,
    ShapeType.multi_linestring: _segmentize_multi_linestrings,
    ShapeType.polygon: _segmentize_polygons,
    ShapeType.multi_polygon: _segmentize_multi_polygons,
}


if __name__ == '__main__':  # pragma: no cover
    pass
