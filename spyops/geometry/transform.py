# -*- coding: utf-8 -*-
"""
Transform Geometry between Coordinate Systems including Z and M coordinates
and Datum Transformations.

By default, we expect grids to be local and do not attempt to drag grids from
the internet.  This can be changed / configured using the configure_grids
function in spyops.crs.util.
"""


from typing import Callable, Optional, TYPE_CHECKING

from fudgeo.enumeration import GeometryType
from numpy import isfinite
from shapely import get_rings
from shapely.coordinates import get_coordinates
from shapely.io import from_wkb

from spyops.geometry.constant import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.util import find_slice_indexes, get_geoms
from spyops.shared.constant import SRS_ID_WKB


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray
    from pyproj import Transformer
    from shapely import (
        LineString, MultiLineString, MultiPoint, MultiPolygon, Polygon, Point)


def transform_points(geoms: list['Point'], transformer: 'Transformer',
                     include_vertical: bool, has_z: bool,
                     has_m: bool) -> tuple[list[Optional['Point']], list[bool]]:
    """
    Transform shapely Points including Z and M values if present.
    """
    cls = FUDGEO_GEOMETRY_LOOKUP[GeometryType.point][has_z, has_m]
    coords = get_coordinates(geoms, include_z=has_z, include_m=has_m)
    validity = _transform_coords(
        coords, transformer=transformer, include_vertical=include_vertical)
    geoms = [from_wkb(cls.from_tuple(values, srs_id=SRS_ID_WKB).wkb,
                      on_invalid='fix') for values in coords]
    # noinspection PyTypeChecker
    return geoms, validity.tolist()
# End transform_points function


def transform_multi_points(geoms: list['MultiPoint'],
                           transformer: 'Transformer',
                           include_vertical: bool, has_z: bool, has_m: bool) \
        -> tuple[list[Optional['MultiPoint']], list[bool]]:
    """
    Transform shapely MultiPoints including Z and M values if present.
    """
    return _transform_linear(
        geoms, transformer=transformer, include_vertical=include_vertical,
        has_z=has_z, has_m=has_m, geom_type=GeometryType.multi_point)
# End transform_multi_points function


def transform_linestrings(geoms: list['LineString'], transformer: 'Transformer',
                          include_vertical: bool, has_z: bool, has_m: bool) \
        -> tuple[list[Optional['LineString']], list[bool]]:
    """
    Transform shapely LineStrings including Z and M values if present.
    """
    return _transform_linear(
        geoms, transformer=transformer, include_vertical=include_vertical,
        has_z=has_z, has_m=has_m, geom_type=GeometryType.linestring)
# End transform_linestrings function


def transform_multi_linestrings(geoms: list['MultiLineString'],
                                transformer: 'Transformer',
                                include_vertical: bool, has_z: bool,
                                has_m: bool) \
        -> tuple[list[Optional['MultiLineString']], list[bool]]:
    """
    Transform shapely MultiLineStrings including Z and M values if present.
    """
    return _transform_groups(
        geoms, transformer=transformer, include_vertical=include_vertical,
        has_z=has_z, has_m=has_m, getter=get_geoms,
        geom_type=GeometryType.multi_linestring)
# End transform_multi_linestrings function


def transform_polygons(geoms: list['Polygon'], transformer: 'Transformer',
                       include_vertical: bool, has_z: bool, has_m: bool) \
        -> tuple[list[Optional['Polygon']], list[bool]]:
    """
    Transform shapely Polygons including Z and M values if present.
    """
    return _transform_groups(
        geoms, transformer=transformer, include_vertical=include_vertical,
        has_z=has_z, has_m=has_m, getter=get_rings,
        geom_type=GeometryType.polygon)
# End transform_polygons function


def transform_multi_polygons(geoms: list['MultiPolygon'],
                             transformer: 'Transformer', include_vertical: bool,
                             has_z: bool, has_m: bool) \
        -> tuple[list[Optional['MultiPolygon']], list[bool]]:
    """
    Transform shapely MultiPolygons including Z and M values if present.
    """
    valid = []
    converted = []
    cls = FUDGEO_GEOMETRY_LOOKUP[GeometryType.multi_polygon][has_z, has_m]
    for geom in geoms:
        poly_valid = []
        poly_coords = []
        for part in get_geoms(geom):
            coords, indexes = get_coordinates(
                get_rings(part), include_z=has_z, include_m=has_m,
                return_index=True)
            validity = _transform_coords(
                coords, transformer=transformer,
                include_vertical=include_vertical)
            ids = find_slice_indexes(indexes)
            poly_valid.append(validity.any())
            poly_coords.append([coords[b:e] for b, e in zip(ids[:-1], ids[1:])])
        # NOTE not requiring all parts to be valid
        valid.append(any(poly_valid))
        converted.append(from_wkb(
            cls(poly_coords, srs_id=SRS_ID_WKB).wkb, on_invalid='fix'))
    return converted, valid
# End transform_multi_polygons function


def _transform_linear(geoms: list['MultiPoint'] | list['LineString'],
                      transformer: 'Transformer', include_vertical: bool,
                      has_z: bool, has_m: bool, geom_type: str) \
        -> tuple[list[Optional['MultiPoint']] | list[Optional['LineString']], list[bool]]:
    """
    Transform Linear Geometry
    """
    cls = FUDGEO_GEOMETRY_LOOKUP[geom_type][has_z, has_m]
    coords, indexes = get_coordinates(
        geoms, include_z=has_z, include_m=has_m, return_index=True)
    validity = _transform_coords(
        coords, transformer=transformer, include_vertical=include_vertical)
    ids = find_slice_indexes(indexes)
    converted = [from_wkb(cls(coords[b:e], srs_id=SRS_ID_WKB).wkb,
                          on_invalid='fix')
                 for b, e in zip(ids[:-1], ids[1:])]
    valid = [validity[b:e].any() for b, e in zip(ids[:-1], ids[1:])]
    return converted, valid
# End _transform_linear function


def _transform_groups(geoms: list['MultiLineString'] | list['Polygon'],
                      transformer: 'Transformer', include_vertical: bool,
                      has_z: bool, has_m: bool, geom_type: str,
                      getter: Callable) \
        -> tuple[list[Optional['MultiLineString']] | list[Optional['Polygon']], list[bool]]:
    """
    Transform Groups of Geometries
    """
    valid = []
    converted = []
    cls = FUDGEO_GEOMETRY_LOOKUP[geom_type][has_z, has_m]
    for geom in geoms:
        coords, indexes = get_coordinates(
            getter(geom), include_z=has_z, include_m=has_m, return_index=True)
        validity = _transform_coords(
            coords, transformer=transformer, include_vertical=include_vertical)
        ids = find_slice_indexes(indexes)
        converted.append(from_wkb(cls([
            coords[b:e] for b, e in zip(ids[:-1], ids[1:])],
            srs_id=SRS_ID_WKB).wkb, on_invalid='fix'))
        valid.append(validity.any())
    return converted, valid
# End _transform_groups function


def _transform_coords(coords: 'ndarray', transformer: 'Transformer',
                      include_vertical: bool) -> 'ndarray':
    """
    Transforms Coordinates and puts them back into the coordinate array.
    Return value is an array of coordinate validity based on XY
    """
    if include_vertical:
        xs, ys, zs = transformer.transform(
            xx=coords[:, 0], yy=coords[:, 1], zz=coords[:, 2])
        coords[:, 2] = zs
    else:
        xs, ys = transformer.transform(xx=coords[:, 0], yy=coords[:, 1])
    coords[:, 0] = xs
    coords[:, 1] = ys
    return isfinite(xs) & isfinite(ys)
# End _transform_coords function


GEOMETRY_TRANSFORM: dict[str, Callable] = {
    GeometryType.point: transform_points,
    GeometryType.multi_point: transform_multi_points,
    GeometryType.linestring: transform_linestrings,
    GeometryType.multi_linestring: transform_multi_linestrings,
    GeometryType.polygon: transform_polygons,
    GeometryType.multi_polygon: transform_multi_polygons,
}


if __name__ == '__main__':  # pragma: no cover
    pass
