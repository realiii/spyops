# -*- coding: utf-8 -*-
"""
Polygonize Workaround
"""


from collections import defaultdict

from fudgeo.enumeration import ShapeType
from shapely import (
    GeometryCollection, from_wkb, get_coordinates, polygonize as _polygonize)

from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.util import get_geoms_iter
from spyops.geometry.wa.util import build_coordinates, get_slicer
from spyops.geometry.wa.uwa import USE_WORKAROUNDS
from spyops.shared.constant import SRS_ID_WKB


def polygonize(geometries, **kwargs) -> GeometryCollection:
    """
    Polygonize Workaround -- ensures measures are present
    """
    # noinspection PyTypeChecker
    collections: GeometryCollection = _polygonize(geometries, **kwargs)
    if not USE_WORKAROUNDS.polygonize:  # pragma: no cover
        return collections
    if collections.is_empty:  # pragma: no cover
        return collections
    has_z = any(geometry.has_z for geometry in geometries)
    has_m = any(geometry.has_m for geometry in geometries)
    if not has_z and not has_m:
        return collections
    lookup = defaultdict(list)
    for geometry in geometries:
        for geom in get_geoms_iter(geometry):
            for *key, m in get_coordinates(
                    geom, include_z=has_z, include_m=True):
                lookup[tuple(key)].append(m)
    if isinstance(collections, GeometryCollection):
        # noinspection PyTypeChecker
        collections = [collections]
    wkb = []
    slicer = get_slicer(has_z=has_z, has_m=has_m)
    # noinspection PyTypeChecker
    for collections in collections:
        for geom in get_geoms_iter(collections):
            coords = build_coordinates(
                geom, has_z=has_z, slicer=slicer, lookup=lookup)
            # noinspection unresolved-references
            shape_type = geom.geom_type.upper()
            cls = FUDGEO_GEOMETRY_LOOKUP[shape_type][has_z, has_m]
            wkb.append(cls(_adjust_coords(coords, shape_type=shape_type),
                           srs_id=SRS_ID_WKB).wkb)
    return GeometryCollection(from_wkb(wkb))
# End polygonize function


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


if __name__ == '__main__':  # pragma: no cover
    pass
