# -*- coding: utf-8 -*-
"""
Workarounds for Shapely / GEOS
"""


from collections import defaultdict
from functools import cache, cached_property
from operator import itemgetter
from typing import Callable, TYPE_CHECKING, Union
from warnings import warn
from math import nan

from bottleneck import nanmean
from fudgeo.enumeration import ShapeType
from numpy import isnan, ndarray
from pyproj import CRS
from shapely import (
    GeometryCollection, LineString, LinearRing, MultiLineString, MultiPolygon,
    Polygon, coverage_simplify, get_rings, set_precision as _set_precision)
from shapely.constructive import (
    make_valid as _make_valid, polygonize as _polygonize)
from shapely.coordinates import get_coordinates
from shapely.io import from_wkb, from_wkt
from shapely.linear import line_merge
from shapely.ops import transform

from spyops.crs.transform import get_transforms
from spyops.geometry.constant import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.util import find_slice_indexes, get_geoms, get_geoms_iter
from spyops.shared.constant import SRS_ID_WKB
from spyops.shared.exception import ShapelyWarning

if TYPE_CHECKING:  # pragma: no cover
    from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry


def polygonize(geometries, **kwargs) -> GeometryCollection:
    """
    Polygonize Workaround -- ensures measures are present
    """
    collections = _polygonize(geometries, **kwargs)
    if not USE_WORKAROUNDS.polygonize:
        return collections
    if collections.is_empty:
        return collections
    has_z = any(geometries.has_z for geometries in geometries)
    has_m = any(geometries.has_m for geometries in geometries)
    if not has_z and not has_m:
        return collections
    lookup = defaultdict(list)
    for geometry in geometries:
        for geom in get_geoms_iter(geometry):
            for *key, m in get_coordinates(
                    geom, include_z=has_z, include_m=True):
                lookup[tuple(key)].append(m)
    if isinstance(collections, GeometryCollection):
        collections = [collections]
    wkb = []
    slicer = _get_slicer(has_z=has_z, has_m=has_m)
    for collections in collections:
        for geom in get_geoms_iter(collections):
            coords = _build_coordinates(
                geom, has_z=has_z, slicer=slicer, lookup=lookup)
            shape_type = geom.geom_type.upper()
            cls = FUDGEO_GEOMETRY_LOOKUP[shape_type][has_z, has_m]
            wkb.append(cls(_adjust_coords(coords, shape_type=shape_type),
                           srs_id=SRS_ID_WKB).wkb)
    return GeometryCollection(from_wkb(wkb))
# End polygonize function


def set_precision(geometry, grid_size, mode='valid_output', **kwargs):
    """
    Set Precision Workaround -- just a warning
    """
    if USE_WORKAROUNDS.set_precision and grid_size > 0:
        if isinstance(geometry, (list, tuple, ndarray)):
            if not len(geometry):
                is_polygon = has_m = False
            else:
                sniff = min(25, len(geometry))
                is_polygon = any(isinstance(g, (Polygon, MultiPolygon))
                                 for g in geometry[:sniff])
                has_m = any(g.has_m for g in geometry[:sniff])
        else:
            is_polygon = isinstance(geometry, (Polygon, MultiPolygon))
            has_m = geometry.has_m
        if is_polygon and has_m:
            warn(f'Setting precision on measured polygons changes the measure '
                 f'value for the last point in the polygon. '
                 f'ref shapely/shapely#2402', category=ShapelyWarning)
    # noinspection PyTypeChecker
    return _set_precision(geometry, grid_size=grid_size, mode=mode, **kwargs)
# End set_precision function


def make_valid(geometry, *, method='linework', keep_collapsed=True, **kwargs):
    """
    Make Valid Workaround
    """
    # noinspection PyTypeChecker
    result = _make_valid(
        geometry, method=method, keep_collapsed=keep_collapsed, **kwargs)
    has_m = geometry.has_m
    if not (USE_WORKAROUNDS.make_valid and has_m):
        return result
    if not has_m or result.is_empty:
        return result
    return _reapply_measures(geometry, result)
# End make_valid function


@cache
def _get_slicer(*, has_z: bool, has_m: bool) -> itemgetter:
    """
    Get Slicer
    """
    return itemgetter(*range(2 + has_z + has_m))
# End _get_slicer function


def _reapply_measures(geometry: 'BaseGeometry',
                      result: 'BaseGeometry') -> 'BaseGeometry':
    """
    Reapply Measures
    """
    has_z = geometry.has_z
    has_m = geometry.has_m
    # NOTE use result because we could change from single to multi part
    shape_type = result.geom_type.upper()
    lookup = defaultdict(list)
    for *key, m in get_coordinates(geometry, include_z=has_z, include_m=has_m):
        lookup[tuple(key)].append(m)
    slicer = _get_slicer(has_z=has_z, has_m=has_m)
    coords = _build_coordinates(
        result, has_z=has_z, slicer=slicer, lookup=lookup)
    cls = FUDGEO_GEOMETRY_LOOKUP[shape_type][has_z, has_m]
    return from_wkb(cls(coords, srs_id=SRS_ID_WKB).wkb)
# End _reapply_measures function


def _build_coordinates(result: Union['BaseGeometry', 'BaseMultipartGeometry'],
                       has_z: bool, slicer: itemgetter,
                       lookup: defaultdict[tuple[float, ...], list[float]]) -> list:
    """
    Build Coordinates
    """
    if isinstance(result, LineString):
        coordinates = get_coordinates(result, include_z=has_z)
        return [slicer((*key, nanmean(lookup.get(tuple(key), [nan]))))
                for key in coordinates]
    elif isinstance(result, (Polygon, MultiLineString)):
        if isinstance(result, Polygon):
            getter = get_rings
        else:
            getter = get_geoms_iter
        return _build_linear_coordinates(
            result, getter=getter, has_z=has_z, slicer=slicer, lookup=lookup)
    else:
        coords = []
        getter = get_rings
        for part in get_geoms(result):
            coords.append(_build_linear_coordinates(
                part, getter=getter, has_z=has_z, slicer=slicer, lookup=lookup))
        return coords
# End _build_coordinates function


def _build_linear_coordinates(geom: Polygon | MultiLineString | LinearRing,
                              getter: Callable, has_z: bool, slicer: itemgetter,
                              lookup: defaultdict[tuple[float, ...], list[float]]) -> list:
    """
    Build Coordinates for Linear Geometry
    """
    coords = []
    coordinates, indexes = get_coordinates(
        getter(geom), include_z=has_z, return_index=True)
    ids = find_slice_indexes(indexes)
    for begin, end in zip(ids[:-1], ids[1:]):
        coords.append([slicer((*key, nanmean(lookup.get(tuple(key), [nan]))))
                       for key in coordinates[begin:end]])
    return coords
# End _build_linear_coordinates function


def _adjust_coords(coords: list, shape_type: str) -> list:
    """
    Adjust Coordinates List based on Shape Type
    """
    if shape_type == ShapeType.linestring:
        coords, = coords
    elif shape_type == ShapeType.multi_polygon:
        coords = [coords]
    return coords
# End _adjust_coords function


class _UseWorkarounds:
    """
    Use Workarounds for Shapely / GEOS
    """
    @cached_property
    def transform(self) -> bool:
        """
        Use workaround for transform (does not support Z and M because
        set_coordinates does not support Z and M)
        """
        a = from_wkt('Point (0 0 0 0)')
        _, best, _ = get_transforms(source_crs=CRS(4326), target_crs=CRS(3857))
        try:
            transform(best.transform, a)
            return False
        except ValueError:
            return True
    # End transform property

    @cached_property
    def make_valid(self) -> bool:
        """
        Use workaround for make_valid?
        """
        a = from_wkt('Polygon ((0 0 0 0, 1 1 1 1, 0 1 2 3, 1 0 4 5, 0 0 0 0))')
        result = _make_valid(a)
        return not result.has_m
    # End make_valid property

    @cached_property
    def line_merge(self) -> bool:
        """
        Use workaround for line_merge?
        """
        a = from_wkt('LINESTRING (0 0 0 0, 1 1 1 1)')
        b = from_wkt('LINESTRING (1 1 1 1, 2 2 2 2)')
        # noinspection PyTypeChecker
        result = line_merge(MultiLineString([a, b]))
        # noinspection PyUnresolvedReferences
        return not result.has_m
    # End line_merge property

    @cached_property
    def simplify(self) -> bool:
        """
        Use workaround for simplify?
        """
        a = from_wkt('LINESTRING (0 0 0 0, 0 2 2 2, 0 1 1 1)')
        result = a.simplify(0)
        return not result.has_m
    # End simplify property

    @cached_property
    def coverage_simplify(self) -> bool:
        """
        Use workaround for coverage_simplify?
        """
        a = from_wkt('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7))')
        # noinspection PyTypeChecker
        result = coverage_simplify(a, tolerance=0.001)
        return not result.has_m
    # End coverage_simplify property

    @cached_property
    def set_precision(self) -> bool:
        """
        Use workaround for set_precision?
        """
        a = from_wkt('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7))')
        result = _set_precision(a, grid_size=0.001)
        coords = get_coordinates(result, include_m=True)
        return bool(isnan(coords[:, 2]).any())
    # End set_precision property

    @cached_property
    def polygonize_drop_m(self) -> bool:
        """
        Use workaround for polygonize when it drops M values?
        """
        a = from_wkt('LINESTRING (0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7)')
        result = _polygonize([a])
        return not result.has_m
    # End polygonize_drop_m property

    @cached_property
    def polygonize_drop_z_nan(self) -> bool:
        """
        Use workaround for polygonize when it drops Z values if all nan?
        """
        a = from_wkt('LINESTRING (0 0 NaN, 0 1 NaN, 1 1 NaN, 1 0 NaN, 0 0 NaN)')
        result = _polygonize([a])
        return not result.has_z
    # End polygonize_drop_z_nan property

    @property
    def polygonize(self) -> bool:
        """
        Use workaround for any polygonize issue?
        """
        return any((self.polygonize_drop_m, self.polygonize_drop_z_nan))
    # End polygonize property

    @cached_property
    def point_intersection(self) -> bool:
        """
        Use workaround for Point / Point Z not getting M during intersect?
        """
        a = from_wkt('LineString (0 0 100 200, 10 0 300 400)')
        p = from_wkt('Point (2 0)')
        return not p.intersection(a).has_m
    # End point_intersection property

    @cached_property
    def point_interpolation(self) -> bool:
        """
        Use workaround for Point getting bad Z value during intersect?
        """
        a = from_wkt('LineString (0 0 100 200, 10 0 300 400)')
        b = from_wkt('Point (2 0)')
        # noinspection PyUnresolvedReferences
        return a.intersection(b).z != 140
    # End point_interpolation property

    @cached_property
    def geometry_order_interpolation(self) -> bool:
        """
        Use workaround for Geometry Order affecting ZM interpolation?
        """
        a = from_wkt('LineString (0 0 100 200, 10 0 300 400)')
        b = from_wkt('LineString (2 0, 5 0, 8 0)')
        result = b.intersection(a)
        coords = get_coordinates(result, include_m=True)
        return bool(isnan(coords[:, 2]).any())
    # End geometry_order_interpolation property

    @cached_property
    def inconsistent_zm_source(self) -> bool:
        """
        Use workaround for ZM values sourced from both inputs?
        """
        a = from_wkt('LineString (2 0 1111 2222, 5 0 3333 4444, 8 0 5555 6666)')
        b = from_wkt('LineString (0 0 1 2, 3 0 3 4, 6 0 5 6, 8 0 7 8)')
        bad = from_wkt('LineString (2 0 1111 2222, 3 0 3 4)')
        result = a.intersection(b)
        # noinspection PyTypeChecker
        return bad in set(get_geoms(result))
    # End inconsistent_zm_source property

    @cached_property
    def dropped_nan_measures(self) -> bool:
        """
        Use workaround for NaN measures completely dropped when intersecting
        LineString and MultiLineString with ZM values
        """
        line_a = from_wkt('LineString (0 0 0 NaN, 10 0 123 NaN)')
        line_b = from_wkt('LineString (4 -5 999 NaN, 5 5 456 NaN, 6 -6 678 NaN)')
        # noinspection PyTypeChecker
        line_b = MultiLineString([line_b])
        result = line_a.intersection(line_b)
        return not result.has_m
    # End dropped_nan_measures property
# End _UseWorkarounds class


USE_WORKAROUNDS: _UseWorkarounds = _UseWorkarounds()


if __name__ == '__main__':  # pragma: no cover
    pass
