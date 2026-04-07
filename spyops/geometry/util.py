# -*- coding: utf-8 -*-
"""
Utility Functions
"""


from typing import Any, Callable, Optional, TYPE_CHECKING, Union

from bottleneck import nansum
from numpy import cross, diff, isfinite, ndarray, nonzero, ones, sqrt, zeros_like
from numpy.linalg import norm
from numpy.ma.core import array, mean
from shapely import force_2d, force_3d
from shapely.coordinates import get_coordinates
from shapely.io import from_wkb
from shapely.predicates import is_empty, is_valid

from spyops.geometry.enumeration import DimensionOption
from spyops.shared.keywords import GEOMS_ATTR


if TYPE_CHECKING:  # pragma: no cover
    from shapely import LinearRing, Polygon
    from shapely.geometry.base import (
        BaseMultipartGeometry, BaseGeometry, GeometrySequence)


def nada(value: Any) -> Any:
    """
    Nada
    """
    return value
# End nada function


def get_geoms(geom: 'BaseMultipartGeometry') -> 'GeometrySequence':
    """
    Get Geometries
    """
    return getattr(geom, GEOMS_ATTR)
# End get_geoms function


def get_geoms_iter(geom: Union['BaseGeometry', 'BaseMultipartGeometry']) \
        -> Union['GeometrySequence', list['BaseGeometry']]:
    """
    Get Geometries for Iteration
    """
    return getattr(geom, GEOMS_ATTR, [geom])
# End get_geoms_iter function


def filter_features(features: list[tuple]) -> list[tuple]:
    """
    Filter Features, removing empty
    """
    return [feature for feature in features if not feature[0].is_empty]
# End filter_features function


def find_slice_indexes(indexes: 'ndarray') -> tuple[int, ...]:
    """
    Find Slice Indexes, include the final index to allow for easier striding
    """
    if not len(indexes):
        return ()
    ids, = nonzero(diff(indexes))
    ids += 1
    return 0, *[int(i) for i in ids], len(indexes)
# End find_slice_indexes function


def to_shapely(features: list[tuple], transformer: Callable | None,
               *, option: DimensionOption = DimensionOption.SAME,
               on_invalid: str = 'raise', extent: Optional['Polygon'] = None) \
        -> tuple[list[tuple], 'ndarray']:
    """
    Convert to Shapely Geometry from Fudgeo Geometry, optionally changing
    geometry dimension by forcing to 2D or 3D and/or transforming.

    When a transformer is provided, the geometries are transformed, validity
    checked, and valid geometries (and corresponding features) are returned.

    When an extent is provided, it is used to retain the geometries (and
    features) with which it intersects.  The extent must be in the same
    coordinate reference system as the geometries e.g., the coordinate system
    prior to transformation.
    """
    # noinspection PyTypeChecker
    geometries: 'ndarray' = from_wkb(
        [g.wkb for g, *_ in features], on_invalid=on_invalid)
    if extent:
        mask = extent.intersects(geometries)
        geometries = geometries[mask]
        features = [feature for feature, v in zip(features, mask) if v]
    if transformer:
        geometries = transformer(geometries)
        validity = get_validity(geometries, transformer=transformer)
        features = [feature for feature, v in zip(features, validity) if v]
    if option == DimensionOption.TWO_D:
        geometries = force_2d(geometries)
    elif option == DimensionOption.THREE_D:
        geometries = force_3d(geometries)
    return features, geometries
# End to_shapely function


def get_validity(geoms: 'ndarray', transformer: Callable | None) -> 'ndarray':
    """
    Get Validity, True if geometry is valid and not empty and not None
    """
    if transformer is None:
        return ones(len(geoms), dtype=bool)
    mask_none = make_none_mask(geoms)
    mask_empty = is_empty(geoms)
    mask_invalid = ~is_valid(geoms)
    return ~(mask_none | mask_empty | mask_invalid)
# End get_validity function


def make_none_mask(values: 'ndarray') -> 'ndarray':
    """
    Create a mask of None values for the given array.
    """
    # NOTE this is the way
    return values == None
# End make_none_mask function


def fan_area_and_centroid(ring: 'LinearRing', has_z: bool, has_m: bool,
                          use_xy_length: bool) -> tuple[float, 'ndarray']:
    """
    Use triangular fan approach to compute area and centroid of a
    polygon ring.
    """
    sign = 1 if ring.is_ccw else -1
    coords = get_coordinates(ring, include_z=True, include_m=has_m)
    if use_xy_length or (has_z and not isfinite(coords[:, 2]).all()):
        coords[:, 2] = 0
    if not (coords[0] == coords[-1]).all():
        coords = array([*coords, coords[0]], dtype=float)

    # Use the first vertex as a fan origin
    p0 = coords[0]

    total_area = 0.0
    weighted_centroid = array([0.0, 0.0, 0.0], dtype=float)

    # Triangulate fan: (p0, p1, p2), (p0, p2, p3), ...
    for i in range(1, len(coords) - 2):
        p1 = coords[i]
        p2 = coords[i + 1]

        # Triangle area in 3D from cross product magnitude
        v1 = p1 - p0
        v2 = p2 - p0
        tri_cross = cross(v1, v2)
        tri_area = 0.5 * norm(tri_cross)

        if tri_area == 0:
            continue

        # Triangle centroid
        tri_centroid = (p0 + p1 + p2) / 3.0

        weighted_centroid += tri_centroid * tri_area
        total_area += tri_area

    if total_area == 0:
        # Degenerate polygon: fall back to simple average
        return 0., mean(coords[:-1], axis=0)

    centroid = weighted_centroid / total_area
    mask = [True, True, has_z]
    if has_m:
        mask = [*mask, has_m]
    return sign * total_area, centroid[mask]



def shoelace_area(coords: 'ndarray', use_xy: bool = True) -> float:
    """
    Shoelace Area, area will be signed
    """
    xs = coords[:, 0]
    ys = coords[:, 1]
    _, dim = coords.shape
    if use_xy or dim < 3:
        return 0.5 * (nansum(xs[:-1] * ys[1:]) - nansum(xs[1:] * ys[:-1]))
    zs = coords[:, 2]
    if not isfinite(zs).all():
        zs = zeros_like(xs, dtype=float)
    dx = xs[1:] - xs[:-1]
    dy = ys[1:] - ys[:-1]
    dz = zs[1:] - zs[:-1]
    cross_x = ys[:-1] * dz - zs[:-1] * dy
    cross_y = zs[:-1] * dx - xs[:-1] * dz
    cross_z = xs[:-1] * dy - ys[:-1] * dx
    return 0.5 * nansum(sqrt(cross_x ** 2 + cross_y ** 2 + cross_z ** 2))
# End shoelace_area function


if __name__ == '__main__':  # pragma: no cover
    pass
