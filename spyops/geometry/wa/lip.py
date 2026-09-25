# -*- coding: utf-8 -*-
"""
Line Interpolate Point Workaround
"""


from fudgeo.enumeration import ShapeType
from numpy import ndarray
from shapely import (
    from_wkb, get_coordinates, get_z,
    line_interpolate_point as _line_interpolate_point)

from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.wa.util import ensure_iterable, linestring_measures_to_zs

from spyops.geometry.wa.uwa import USE_WORKAROUNDS
from spyops.shared.constant import SRS_ID_WKB


def line_interpolate_point(line, distance, normalized=False, **kwargs):
    """
    Line Interpolate Point Workaround -- ensures measures are present
    """
    func = _line_interpolate_point
    if USE_WORKAROUNDS.line_interpolate_point:
        if isinstance(line, (list, tuple, ndarray)):
            if not len(line):
                has_m = False
            else:
                geoms = line[:(min(25, len(line)))]
                # noinspection unresolved-references
                has_m = any(g.has_m for g in geoms)
        else:
            has_m = line.has_m
        if has_m:
            func = _line_interpolate_point_with_measures
    # noinspection bad-argument-type
    return func(line, distance=distance, normalized=normalized, **kwargs)
# End line_interpolate_point function


def _line_interpolate_point_with_measures(line, distance, normalized=False,
                                          **kwargs):
    """
    Line Interpolate Point Workaround -- ensures measures are present
    """
    has_m = True
    is_iterable, lines = ensure_iterable(line)
    geoms = lines[:(min(25, len(lines)))]
    has_z = any(g.has_z for g in geoms)
    cls = FUDGEO_GEOMETRY_LOOKUP[ShapeType.point][has_z, has_m]
    if not has_z:
        # NOTE measures are stored in Z because of LineString construction
        coordinates = get_coordinates(_line_interpolate_point(
            linestring_measures_to_zs(lines), distance=distance,
            normalized=normalized, **kwargs), include_z=True)
    else:
        points = _line_interpolate_point(
            lines, distance=distance, normalized=normalized, **kwargs)
        coordinates = get_coordinates(points, include_z=has_z, include_m=has_m)
        # NOTE use get_z since measures in Z via LineString creation
        coordinates[:, -1] = get_z(_line_interpolate_point(
            linestring_measures_to_zs(lines), distance=distance,
            normalized=normalized, **kwargs))
    result = from_wkb([cls.from_tuple(coords, srs_id=SRS_ID_WKB).wkb
                       for coords in coordinates])
    if not is_iterable:
        return result[0]
    return result
# End _line_interpolate_point_with_measures function


if __name__ == '__main__':  # pragma: no cover
    pass
