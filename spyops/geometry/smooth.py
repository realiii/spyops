# -*- coding: utf-8 -*-
"""
Smoothing
"""


from collections import Counter
from typing import Callable

from fudgeo.enumeration import ShapeType
from numpy import (
    array, asarray, clip, column_stack, exp, linspace, ndarray, ones_like,
    zeros_like)
from numpy.linalg import norm, solve
from shapely import get_rings
from shapely.coordinates import get_coordinates
from shapely.geometry.base import BaseGeometry
from shapely.io import from_wkb

from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.util import find_slice_indexes, get_geoms_iter
from spyops.shared.constant import EMPTY, SRS_ID_WKB


def smooth_bezier(geometry: ndarray | list | BaseGeometry,
                  density: int = 8, **kwargs) -> ndarray | BaseGeometry:
    """
    Smooth Polyline using cubic Bezier interpolation

    Fits a cubic Bezier curve through every original line segment.  Adjacent
    curves are joined smoothly at input vertices using Bessel tangents as
    described by Farin (1997), with chord-length parameterization.

    The resulting polyline passes through all input vertices, and the original
    start and end coordinates of each line part are retained exactly.
    """
    if density <= 0:
        # noinspection bad-return
        return geometry
    geometry, has_m, has_z, is_iterable, shape_type = _smooth_config(geometry)
    if shape_type in GEOMETRY_SMOOTH_BEZIER:
        func = GEOMETRY_SMOOTH_BEZIER[shape_type]
        geometry = func(geometry, density=density, has_z=has_z, has_m=has_m)
    if is_iterable:
        return asarray(geometry)
    return geometry[0]
# End smooth_bezier function


def smooth_paek(geometry: ndarray | list | BaseGeometry,
                tolerance: float, **kwargs) -> ndarray | BaseGeometry:
    """
    Smooth Polyline using Polynomial Approximation with Exponential Kernel

    Implements the PAEK technique described by Bodansky, Gribov, and Pilouk
    (2002), using an exponentially weighted local polynomial approximation over
    cumulative line distance.

    The smoothing tolerance controls the exponential kernel bandwidth and must
    be greater than 0.  The original start and end coordinates of each line part
    are retained exactly.
    """
    if tolerance <= 0:
        # noinspection bad-return
        return geometry
    geometry, has_m, has_z, is_iterable, shape_type = _smooth_config(geometry)
    if shape_type in GEOMETRY_SMOOTH_PAEK:
        func = GEOMETRY_SMOOTH_PAEK[shape_type]
        geometry = func(geometry, tolerance=tolerance, has_z=has_z, has_m=has_m)
    if is_iterable:
        return asarray(geometry)
    return geometry[0]
# End smooth_paek function


def _smooth_config(geometry: ndarray | list | BaseGeometry) \
        -> tuple[ndarray| list, bool, bool, bool, str]:
    """
    Shared Configuration
    """
    if not (is_iterable := isinstance(geometry, (list, tuple, ndarray))):
        geometry = [geometry]
    if not len(geometry):
        shape_type = EMPTY
        has_z = has_m = False
    else:
        geoms = geometry[:(min(25, len(geometry)))]
        has_z = any(g.has_z for g in geoms)
        has_m = any(g.has_m for g in geoms)
        (geom_type, _), = Counter([g.geom_type for g in geoms]).most_common(1)
        shape_type = geom_type.upper()
    return geometry, has_m, has_z, is_iterable, shape_type
# End _smooth_config function


def _smooth_bezier_linestring(geometry: ndarray | list, *, density: int,
                              has_z: bool, has_m: bool) -> ndarray:
    """
    Smooth LineString using Bezier curves
    """
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.linestring][has_z, has_m]
    coordinates = _smooth_bezier(
        geometry, density=density, has_z=has_z, has_m=has_m)
    wkb = [cls(coords, srs_id=SRS_ID_WKB).wkb for coords in coordinates]
    return from_wkb(wkb, on_invalid='fix')
# End _smooth_bezier_linestring function


def _smooth_bezier_multi_linestring(geometry: ndarray | list, *, density: int,
                                    has_z: bool, has_m: bool) -> ndarray:
    """
    Smooth MultiLineString using Bezier curves
    """
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.multi_linestring][has_z, has_m]
    # noinspection bad-argument-type
    wkb = [cls(_smooth_bezier(
        get_geoms_iter(geom), density=density, has_z=has_z, has_m=has_m),
        srs_id=SRS_ID_WKB).wkb for geom in geometry]
    return from_wkb(wkb, on_invalid='fix')
# End _smooth_bezier_multi_linestring function


def _smooth_bezier_polygon(geometry: ndarray | list, *, density: int,
                           has_z: bool, has_m: bool) -> ndarray:
    """
    Smooth Polygon using Bezier curves
    """
    wkb = []
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.polygon][has_z, has_m]
    for poly in geometry:
        coordinates = _smooth_bezier(
            get_rings(poly), density=density, has_z=has_z, has_m=has_m)
        wkb.append(cls(coordinates, srs_id=SRS_ID_WKB).wkb)
    return from_wkb(wkb, on_invalid='fix')
# End _smooth_bezier_polygon function


def _smooth_bezier_multi_polygon(geometry: ndarray | list, *, density: int,
                                 has_z: bool, has_m: bool) -> ndarray:
    """
    Smooth MultiPolygon using Bezier curves
    """
    wkb = []
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.multi_polygon][has_z, has_m]
    for geom in geometry:
        coordinates = [_smooth_bezier(
            get_rings(poly), density=density, has_z=has_z, has_m=has_m)
            for poly in get_geoms_iter(geom)]
        wkb.append(cls(coordinates, srs_id=SRS_ID_WKB).wkb)
    return from_wkb(wkb, on_invalid='fix')
# End _smooth_bezier_multi_polygon function


def _smooth_paek_linestring(geometry: ndarray | list, *, tolerance: float,
                            has_z: bool, has_m: bool) -> ndarray:
    """
    Smooth LineString using PAEK
    """
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.linestring][has_z, has_m]
    coordinates = _smooth_paek(
        geometry, tolerance=tolerance, has_z=has_z, has_m=has_m)
    wkb = [cls(coords, srs_id=SRS_ID_WKB).wkb for coords in coordinates]
    return from_wkb(wkb, on_invalid='fix')
# End _smooth_paek_linestring function


def _smooth_paek_multi_linestring(geometry: ndarray | list, *, tolerance: float,
                                  has_z: bool, has_m: bool) -> ndarray:
    """
    Smooth MultiLineString using PAEK
    """
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.multi_linestring][has_z, has_m]
    # noinspection bad-argument-type
    wkb = [cls(_smooth_paek(
        get_geoms_iter(geom), tolerance=tolerance, has_z=has_z, has_m=has_m),
        srs_id=SRS_ID_WKB).wkb for geom in geometry]
    return from_wkb(wkb, on_invalid='fix')
# End _smooth_paek_multi_linestring function


def _smooth_paek_polygon(geometry: ndarray | list, *, tolerance: float,
                         has_z: bool, has_m: bool) -> ndarray:
    """
    Smooth Polygon using PAEK
    """
    wkb = []
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.polygon][has_z, has_m]
    for poly in geometry:
        coordinates = _smooth_paek(
            get_rings(poly), tolerance=tolerance, has_z=has_z, has_m=has_m)
        wkb.append(cls(coordinates, srs_id=SRS_ID_WKB).wkb)
    return from_wkb(wkb, on_invalid='fix')
# End _smooth_paek_polygon function


def _smooth_paek_multi_polygon(geometry: ndarray | list, *, tolerance: float,
                               has_z: bool, has_m: bool) -> ndarray:
    """
    Smooth MultiPolygon using PAEK
    """
    wkb = []
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.multi_polygon][has_z, has_m]
    for geom in geometry:
        coordinates = [_smooth_paek(
            get_rings(poly), tolerance=tolerance, has_z=has_z, has_m=has_m)
            for poly in get_geoms_iter(geom)]
        wkb.append(cls(coordinates, srs_id=SRS_ID_WKB).wkb)
    return from_wkb(wkb, on_invalid='fix')
# End _smooth_paek_multi_polygon function


def _smooth_bezier(geometry: ndarray | list, *, density: int,
                   has_z: bool, has_m: bool) -> list[ndarray]:
    """
    Smooth Linear Geometry Coordinates using cubic Bezier interpolation
    """
    coords, indexes = get_coordinates(
        geometry, include_z=has_z, include_m=has_m, return_index=True)
    ids = find_slice_indexes(indexes)
    smoothed_coords = []
    for begin, end in zip(ids[:-1], ids[1:]):
        subset = coords[begin:end]
        if len(subset) <= 2:
            smoothed_coords.append(subset)
            continue
        distances = _cumulative_distances(subset[:, :2])
        if distances[-1] == 0:
            smoothed_coords.append(subset)
            continue
        tangents = _bessel_tangents(subset, distances=distances)
        smoothed = _bezier_coordinates(
            subset, distances=distances, tangents=tangents,
            density=density)
        smoothed[0] = subset[0]
        smoothed[-1] = subset[-1]
        smoothed_coords.append(smoothed)
    return smoothed_coords
# End _smooth_bezier function


def _bessel_tangents(coordinates: ndarray, distances: ndarray) -> ndarray:
    """
    Calculate Bessel tangents for cubic Bezier interpolation

    Interior tangents are computed from the derivative of the local quadratic
    interpolant through three consecutive vertices using chord-length
    parameterization.  This gives smooth joins between adjacent Bezier segments.

    End tangents use one-sided chord derivatives so the first and last Bezier
    segments retain the original endpoints.
    """
    tangents = zeros_like(coordinates, dtype=float)
    lengths = distances[1:] - distances[:-1]
    if lengths[0] > 0:
        tangents[0] = (coordinates[1] - coordinates[0]) / lengths[0]
    if lengths[-1] > 0:
        tangents[-1] = (coordinates[-1] - coordinates[-2]) / lengths[-1]
    for idx in range(1, len(lengths)):
        prev_len = lengths[idx - 1]
        next_len = lengths[idx]
        if prev_len <= 0 and next_len <= 0:
            continue
        if prev_len <= 0:
            tangents[idx] = (coordinates[idx + 1] - coordinates[idx]) / next_len
            continue
        if next_len <= 0:
            tangents[idx] = (coordinates[idx] - coordinates[idx - 1]) / prev_len
            continue
        prev_slope = (coordinates[idx] - coordinates[idx - 1]) / prev_len
        next_slope = (coordinates[idx + 1] - coordinates[idx]) / next_len
        tangents[idx] = ((next_len * prev_slope) + (
                prev_len * next_slope)) / (prev_len + next_len)
    return tangents
# End _bessel_tangents function


def _bezier_coordinates(coordinates: ndarray, distances: ndarray, *,
                        tangents: ndarray, density: int) -> ndarray:
    """
    Evaluate cubic Bezier segments between consecutive input vertices
    """
    smoothed = [coordinates[0]]
    for idx in range(len(coordinates) - 1):
        if (length := distances[idx + 1] - distances[idx]) <= 0:
            continue
        start = coordinates[idx]
        end = coordinates[idx + 1]
        control_1 = start + (length * tangents[idx] / 3)
        control_2 = end - (length * tangents[idx + 1] / 3)
        steps = linspace(start=0, stop=1, num=density + 2, dtype=float)
        smoothed.extend(_cubic_bezier_points(
            steps[1:], start=start, control_1=control_1,
            control_2=control_2, end=end))
    return array(smoothed, dtype=float)
# End _bezier_coordinates function


def _cubic_bezier_points(steps: ndarray, *, start: ndarray,
                         control_1: ndarray, control_2: ndarray,
                         end: ndarray) -> list:
    """
    Evaluate cubic Bezier points
    """
    points = []
    for step in steps:
        inverse = 1 - step
        points.append(
            (inverse ** 3) * start +
            (3 * inverse ** 2 * step) * control_1 +
            (3 * inverse * step ** 2) * control_2 +
            (step ** 3) * end)
    return points
# End _cubic_bezier_points function


def _smooth_paek(geometry: ndarray | list, *, tolerance: float,
                 has_z: bool, has_m: bool) -> list[ndarray]:
    """
    Smooth Linear Geometry Coordinates using PAEK
    """
    coords, indexes = get_coordinates(
        geometry, include_z=has_z, include_m=has_m, return_index=True)
    ids = find_slice_indexes(indexes)
    smoothed_coords = []
    for begin, end in zip(ids[:-1], ids[1:]):
        subset = coords[begin:end]
        if len(subset) <= 2:
            smoothed_coords.append(subset)
            continue
        distances = _cumulative_distances(subset[:, :2])
        if distances[-1] == 0:
            smoothed_coords.append(subset)
            continue
        smoothed = _paek_coordinates(
            subset, distances=distances, tolerance=tolerance)
        smoothed[0] = subset[0]
        smoothed[-1] = subset[-1]
        smoothed_coords.append(smoothed)
    return smoothed_coords
# End _smooth_paek function


def _cumulative_distances(coordinates: ndarray) -> ndarray:
    """
    Calculate cumulative 2D distances along coordinates
    """
    deltas = coordinates[1:] - coordinates[:-1]
    segment_lengths = norm(deltas, axis=1)
    distances = zeros_like(coordinates[:, 0], dtype=float)
    distances[1:] = segment_lengths.cumsum()
    return distances
# End _cumulative_distances function


def _paek_coordinates(coordinates: ndarray, *, distances: ndarray,
                      tolerance: float) -> ndarray:
    """
    Smooth coordinates with local polynomial approximation and exponential
    kernel weighting
    """
    smoothed = coordinates.copy()
    polynomial_order = min(2, len(coordinates) - 1)
    for idx, distance in enumerate(distances):
        relative_distances = distances - distance
        weights = exp(-abs(relative_distances) / tolerance)
        # Center and scale distances for better numerical conditioning.
        scaled_distances = relative_distances / tolerance
        design = _polynomial_design_matrix(
            scaled_distances, order=polynomial_order)
        coefficients = _weighted_polynomial_fit(
            design=design, values=coordinates, weights=weights)
        # At the target vertex, scaled distance is 0, so the fitted coordinate
        # is the polynomial intercept for each coordinate dimension.
        smoothed[idx] = coefficients[0]
    return smoothed
# End _paek_coordinates function


def _polynomial_design_matrix(values: ndarray, *, order: int) -> ndarray:
    """
    Build polynomial design matrix
    """
    columns = [ones_like(values, dtype=float)]
    columns.extend(values ** power for power in range(1, order + 1))
    return column_stack(columns)
# End _polynomial_design_matrix function


def _weighted_polynomial_fit(design: ndarray, values: ndarray,
                             weights: ndarray) -> ndarray:
    """
    Fit weighted polynomial coefficients
    """
    weights = clip(asarray(weights, dtype=float), 1e-12, None)
    weighted_design = design * weights[:, None]
    weighted_values = values * weights[:, None]
    return solve(weighted_design.T @ weighted_design,
                 weighted_design.T @ weighted_values)
# End _weighted_polynomial_fit function


GEOMETRY_SMOOTH_BEZIER: dict[str, Callable] = {
    ShapeType.linestring: _smooth_bezier_linestring,
    ShapeType.multi_linestring: _smooth_bezier_multi_linestring,
    ShapeType.polygon: _smooth_bezier_polygon,
    ShapeType.multi_polygon: _smooth_bezier_multi_polygon,
}

GEOMETRY_SMOOTH_PAEK: dict[str, Callable] = {
    ShapeType.linestring: _smooth_paek_linestring,
    ShapeType.multi_linestring: _smooth_paek_multi_linestring,
    ShapeType.polygon: _smooth_paek_polygon,
    ShapeType.multi_polygon: _smooth_paek_multi_polygon,
}


if __name__ == '__main__':  # pragma: no cover
    pass
