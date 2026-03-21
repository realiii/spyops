# -*- coding: utf-8 -*-
"""
Buffers
"""


from collections import defaultdict
from functools import lru_cache
from typing import Callable, TYPE_CHECKING

from fudgeo.enumeration import ShapeType
from numpy import array, full_like
from shapely import GeometryCollection, MultiPolygon, Polygon
from shapely.constructive import buffer, centroid, normalize
from shapely.coordinates import get_coordinates
from shapely.set_operations import difference, union_all

from spyops.crs.transform import (
    get_transform_best_guess, make_transformer_function)
from spyops.crs.util import get_equidistant_projections
from spyops.shared.enumeration import EndOption, SideOption
from spyops.shared.hint import XY_TOL


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray
    from pyproj import CRS


def planar_buffer(geometries: 'ndarray', distances: 'ndarray', *,
                  side_option: SideOption, end_option: EndOption,
                  resolution: int, xy_tolerance: XY_TOL, **kwargs) -> 'ndarray':
    """
    Planar Buffer

    Distances must be in the same units as the geometries.

    XY tolerance needs to be in units of the geometries which, in the buffer
    usage case, will be the Source CRS units.
    """
    factor, single_sided = _get_side_settings(side_option)
    kwargs = dict(quad_segs=resolution, single_sided=single_sided,
                  cap_style=str(end_option).casefold())
    polygons = buffer(geometries, distance=distances * factor, **kwargs)
    polygons = _outside_only(
        geometries, polygons=polygons, distances=distances,
        side_option=side_option, xy_tolerance=xy_tolerance)
    return _dissolve_polygons(polygons, xy_tolerance=xy_tolerance)
# End planar_buffer function


def geodesic_buffer(geometries: 'ndarray', distances: 'ndarray', *,
                    shape_type: str, crs: 'CRS', side_option: SideOption,
                    end_option: EndOption, resolution: int,
                    xy_tolerance: XY_TOL) -> 'ndarray':
    """
    Geodesic Buffer

    Distances must be in meters.

    XY tolerance needs to be in units of the geometries which, in the buffer
    usage case, will be the Source CRS units.
    """
    coords = get_coordinates(centroid(geometries))
    projections = get_equidistant_projections(crs, coordinates=coords)
    grouped = defaultdict(list)
    for i, prj in enumerate(projections):
        grouped[prj].append(i)
    factor, single_sided = _get_side_settings(side_option)
    kwargs = dict(quad_segs=resolution, single_sided=single_sided,
                  cap_style=str(end_option).casefold())
    polygons = full_like(geometries, fill_value=None, dtype=object)
    for prj, indexes in grouped.items():
        if prj is None:
            continue
        geoms = geometries[indexes]
        dists = distances[indexes] * factor
        transformers = _equidistant_transformers(
            crs, equidistant_crs=prj, shape_type=shape_type)
        if None in transformers:
            polygons[indexes] = buffer(geoms, distance=dists, **kwargs)
            continue
        to_eqd, from_eqd = transformers
        polygons[indexes] = from_eqd(_to_multi(buffer(
            to_eqd(geoms), distance=dists, **kwargs)))
    polygons = _outside_only(
        geometries, polygons=polygons, distances=distances,
        side_option=side_option, xy_tolerance=xy_tolerance)
    return _dissolve_polygons(polygons, xy_tolerance=xy_tolerance)
# End geodesic_buffer function


def _outside_only(geometries: 'ndarray', polygons: 'ndarray',
                  distances: 'ndarray', side_option: SideOption,
                  xy_tolerance: XY_TOL) -> 'ndarray':
    """
    Handle the Outside Only option.  This option only applies to polygon input
    geometries Polygons.  The process is to erase the original geometry
    from the buffered geometry.

    Address the situation where distances are negative (interior buffer) by
    flipping the geometries and polygons, that is, subtract the buffered
    geometry from the original geometry.

    Ignore the case where the distance is zero since this would result in
    an empty geometry.
    """
    if side_option != SideOption.ONLY_OUTSIDE:
        return polygons
    is_positive = distances > 0
    polygons[is_positive] = difference(
        polygons[is_positive], geometries[is_positive], grid_size=xy_tolerance)
    is_negative = distances < 0
    polygons[is_negative] = difference(
        geometries[is_negative], polygons[is_negative], grid_size=xy_tolerance)
    return polygons
# End _outside_only function


def _dissolve_polygons(polygons: 'ndarray', xy_tolerance: XY_TOL) -> 'ndarray':
    """
    Dissolve Polygons and Enforce MultiPolygon
    """
    return _to_multi(union_all(
        normalize(polygons).reshape(-1, 1), grid_size=xy_tolerance, axis=1))
# End _dissolve_polygons function


def _to_multi(polygons: 'ndarray') -> 'ndarray':
    """
    Ensure working with all MultiPolygons
    """
    is_poly = array([isinstance(g, Polygon) for g in polygons], dtype=bool)
    if is_poly.any():
        polygons[is_poly] = [MultiPolygon([g]) for g in polygons[is_poly]]
    is_coll = array([isinstance(g, GeometryCollection)
                     for g in polygons], dtype=bool)
    if is_coll.any():
        polygons[is_coll] = [MultiPolygon(g) for g in polygons[is_coll]]
    return polygons
# End _to_multi function


@lru_cache(maxsize=1000)
def _equidistant_transformers(crs: 'CRS', equidistant_crs: 'CRS',
                              shape_type: str) \
        -> tuple[Callable, Callable] | tuple[None, None]:
    """
    Equidistant Transformers
    """
    to_equidistant_transformer = get_transform_best_guess(
        crs, target_crs=equidistant_crs, suppress=True)
    if not to_equidistant_transformer:
        return None, None
    to_equidistant = make_transformer_function(
        shape_type=shape_type, has_z=False, has_m=False,
        transformer=to_equidistant_transformer)
    from_equidistant_transformer = get_transform_best_guess(
        equidistant_crs, target_crs=crs, suppress=True)
    if not from_equidistant_transformer:
        return None, None
    from_equidistant = make_transformer_function(
        shape_type=ShapeType.multi_polygon, has_z=False, has_m=False,
        transformer=from_equidistant_transformer)
    return to_equidistant, from_equidistant
# End _equidistant_transformers function


def _get_side_settings(side_option: SideOption) -> tuple[int, bool]:
    """
    Get Side Settings
    """
    single_sided = side_option in (SideOption.LEFT, SideOption.RIGHT)
    if side_option == SideOption.RIGHT:
        factor = -1
    else:
        factor = 1
    return factor, single_sided
# End _get_side_settings function


if __name__ == '__main__':  # pragma: no cover
    pass
