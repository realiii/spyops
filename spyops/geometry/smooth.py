# -*- coding: utf-8 -*-
"""
Smoothing
"""


from collections import Counter
from typing import Callable

from fudgeo.enumeration import ShapeType
from numpy import (
    array, asarray, clip, column_stack, exp, linspace, ndarray, 
    ones_like, zeros_like)
from numpy.linalg import lstsq, norm
from shapely.coordinates import get_coordinates
from shapely.geometry import LineString as ShapelyLineString, MultiLineString as ShapelyMultiLineString
from shapely.geometry.base import BaseGeometry

from spyops.shared.constant import EMPTY

# TODO add support for LineString and LinearRing, Polygon and MultiPolygon

def smooth_bezier(geometry: ndarray | list | BaseGeometry,
                  density: int = 8) -> ndarray | BaseGeometry:
    """
    Smooth Polyline using cubic Bezier interpolation

    Fits a cubic Bezier curve through every original line segment.  Adjacent
    curves are joined smoothly at input vertices using Bessel tangents as
    described by Farin (1997), with chord-length parameterization.

    The resulting polyline passes through all input vertices, and the original
    start and end coordinates of each line part are retained exactly.
    """
    if density <= 0:
        return geometry


def _smooth_bezier_linestring(geometry: ndarray | list, *, density: int,
                              has_z: bool, has_m: bool) -> list:
    """
    Smooth LineString using Bezier curves
    """
    coordinates = _smooth_bezier(
        geometry, density=density, has_z=has_z, has_m=has_m)
    return [ShapelyLineString(coords) for coords in coordinates]
# End _smooth_bezier_linestring function


def _smooth_bezier_multi_linestring(geometry: ndarray | list, *, density: int,
                                    has_z: bool, has_m: bool) -> list:
    """
    Smooth MultiLineString using Bezier curves
    """
    return [ShapelyMultiLineString(_smooth_bezier(
        get_geoms_iter(geom), density=density, has_z=has_z, has_m=has_m))
        for geom in geometry]
# End _smooth_bezier_multi_linestring function


def smooth_paek(geometry: 'BaseGeometry',
                tolerance: float) -> 'BaseGeometry':
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
        raise ValueError('tolerance must be greater than 0')

    if geometry.is_empty:
        return geometry

    if isinstance(geometry, ShapelyLineString):
        return _smooth_paek(
            geometry, tolerance=tolerance)

    if isinstance(geometry, ShapelyMultiLineString):
        return ShapelyMultiLineString([
            _smooth_paek(
                line, tolerance=tolerance)
            for line in geometry.geoms
        ])

    raise TypeError(
        f'PAEK smoothing requires LineString or MultiLineString geometry, '
        f'not {geometry.geom_type}')
# End smooth_paek function


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
    Calculate Bessel tangents for cubic Bezier interpolation.

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
    for idx in range(1, len(coordinates) - 1):
        prev_length = lengths[idx - 1]
        next_length = lengths[idx]
        if prev_length <= 0 and next_length <= 0:
            tangents[idx] = 0
            continue
        if prev_length <= 0:
            tangents[idx] = (coordinates[idx + 1] - coordinates[idx]) / next_length
            continue
        if next_length <= 0:
            tangents[idx] = (coordinates[idx] - coordinates[idx - 1]) / prev_length
            continue
        previous_slope = (coordinates[idx] - coordinates[idx - 1]) / prev_length
        next_slope = (coordinates[idx + 1] - coordinates[idx]) / next_length
        tangents[idx] = ((next_length * previous_slope) + (
                prev_length * next_slope)) / (prev_length + next_length)
    return tangents
# End _bessel_tangents function


def _bezier_coordinates(coordinates: ndarray, distances: ndarray, *,
                        tangents: ndarray, density: int) -> ndarray:
    """
    Evaluate cubic Bezier segments between consecutive input vertices
    """
    smoothed = [coordinates[0]]
    for idx in range(len(coordinates) - 1):
        segment_length = distances[idx + 1] - distances[idx]
        if segment_length <= 0:
            continue
        start = coordinates[idx]
        end = coordinates[idx + 1]
        control_1 = start + (segment_length * tangents[idx] / 3.0)
        control_2 = end - (segment_length * tangents[idx + 1] / 3.0)
        steps = linspace(start=0.0, stop=1.0, num=points_per_segment + 2)[1:]

        # TODO vectorize this
        for step in steps:
            smoothed.append(_cubic_bezier_point(
                step, start=start, control_1=control_1,
                control_2=control_2, end=end))
    return array(smoothed, dtype=float)
# End _bezier_coordinates function


def _cubic_bezier_point(step: float, *, start: 'ndarray',
                        control_1: 'ndarray', control_2: 'ndarray',
                        end: 'ndarray') -> 'ndarray':
    """
    Evaluate cubic Bezier points
    """
    inverse = 1.0 - step
    return (
        (inverse ** 3) * start +
        (3.0 * inverse ** 2 * step) * control_1 +
        (3.0 * inverse * step ** 2) * control_2 +
        (step ** 3) * end
    )
# End _cubic_bezier_point function


def _smooth_paek(geom: ShapelyLineString, *,
                 tolerance: float) -> ShapelyLineString:
    """
    Smooth Linear Geometry Coordinates using PAEK
    """
    # TODO vectorize this
    coords = get_coordinates(
        geom, include_z=geom.has_z, include_m=geom.has_m)

    if len(coords) <= 2:
        return geom

    distances = _cumulative_distances(coords[:, :2])
    if distances[-1] == 0:
        return geom

    smoothed = _paek_coordinates(
        coordinates=coords,
        distances=distances,
        tolerance=tolerance)

    smoothed[0] = coords[0]
    smoothed[-1] = coords[-1]
    return ShapelyLineString(smoothed)
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


def _paek_coordinates(coordinates: ndarray, distances: ndarray, *,
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
    coefficients, *_ = lstsq(weighted_design, weighted_values, rcond=None)
    return coefficients
# End _weighted_polynomial_fit function


GEOMETRY_SMOOTH_BEZIER: dict[str, Callable] = {
    ShapeType.linestring: _smooth_bezier_linestring,
    ShapeType.multi_linestring: _smooth_bezier_multi_linestring,
}


if __name__ == '__main__':  # pragma: no cover
    pass
