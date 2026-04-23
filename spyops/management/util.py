# -*- coding: utf-8 -*-
"""
Internal Functions for Management Module
"""


from typing import TYPE_CHECKING

from fudgeo.geometry import LineString
from numpy import array, linspace, outer
from pyproj import Transformer

from spyops.crs.util import make_geodetic_transformer
from spyops.shared.enumeration import LineTypeOption


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray
    from pyproj import CRS


def _build_lines_factory(coords: list[tuple[float, float, float, float]], *,
                         srs_id: int, crs: 'CRS', line_type: LineTypeOption,
                         point_count: int) -> list[LineString]:
    """
    Build Lines Factory Function
    """
    if not coords:
        return []
    if line_type == LineTypeOption.PLANAR or not point_count:
        func = _build_planar_lines
    elif line_type == LineTypeOption.GEODESIC:
        func = _build_geodesic_lines
    else:
        return []
    coordinates = array(coords, dtype=float)
    return func(coordinates, srs_id=srs_id, crs=crs, point_count=point_count)
# End _build_lines_factory function


def _build_planar_lines(coordinates: 'ndarray', *, srs_id: int,
                        point_count: int, **kwargs) -> list[LineString]:
    """
    Build Planar Lines
    """
    # noinspection PyTypeChecker
    return [LineString(_interpolate_coordinates(point_count, values),
                       srs_id=srs_id) for values in coordinates]
# End _build_planar_lines function


def _build_geodesic_lines(coordinates: 'ndarray', *, srs_id: int, crs: 'CRS',
                          point_count: int) -> list[LineString]:
    """
    Build Geodesic Lines
    """
    lines = []
    if not (geod := crs.get_geod()):
        raise ValueError('Cannot build geodesic lines without a Geod')
    npts = point_count + 2
    coordinates = _prepare_coordinates(coordinates, crs=crs)
    for values in coordinates:
        coords = array(geod.npts(
            *values, npts=npts, initial_idx=0, terminus_idx=0), dtype=float)
        coords = _prepare_intermediates(coords, crs=crs)
        # noinspection PyTypeChecker
        lines.append(LineString(coords, srs_id=srs_id))
    return lines
# End _build_geodesic_lines function


def _interpolate_coordinates(point_count: int, values: 'ndarray') -> 'ndarray':
    """
    Interpolate Coordinates
    """
    values = values.reshape(2, 2)
    if not point_count:
        return values
    steps = linspace(start=0, stop=1, num=point_count + 2)
    return values[0] + outer(steps, (values[1] - values[0]))
# End _interpolate_coordinates function


def _prepare_coordinates(coordinates: 'ndarray', crs: 'CRS') -> 'ndarray':
    """
    Prepare Coordinates, from projected to geodetic
    """
    if not crs.is_projected:
        return coordinates
    transformer = make_geodetic_transformer(crs)
    start_x, start_y = transformer.transform(
        coordinates[:, 0], coordinates[:, 1])
    end_x, end_y = transformer.transform(
        coordinates[:, 2], coordinates[:, 3])
    for i, values in enumerate((start_x, start_y, end_x, end_y)):
        coordinates[:, i] = values
    return coordinates
# End _prepare_coordinates function


def _prepare_intermediates(coordinates: 'ndarray', crs: 'CRS') -> 'ndarray':
    """
    Prepare Intermediate Coordinates, from geodetic to projected
    """
    if not crs.is_projected:
        return coordinates
    transformer = Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True)
    xs, ys = transformer.transform(coordinates[:, 0], coordinates[:, 1])
    for i, values in enumerate((xs, ys)):
        coordinates[:, i] = values
    return coordinates
# End _prepare_intermediates function


if __name__ == '__main__':  # pragma: no cover
    pass
