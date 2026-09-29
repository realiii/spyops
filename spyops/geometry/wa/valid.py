# -*- coding: utf-8 -*-
"""
Make Valid Workaround
"""


from collections import defaultdict

from shapely import (
    from_wkb, get_coordinates, make_valid as _make_valid)
from shapely.geometry.base import BaseGeometry

from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.wa.util import build_coordinates, get_slicer
from spyops.geometry.wa.uwa import USE_WORKAROUNDS
from spyops.shared.constant import SRS_ID_WKB


def make_valid(geometry, *, method='linework', keep_collapsed=True, **kwargs):
    """
    Make Valid Workaround
    """
    # noinspection PyTypeChecker
    result: 'BaseGeometry' = _make_valid(
        geometry, method=method, keep_collapsed=keep_collapsed, **kwargs)
    has_m = geometry.has_m
    if not (USE_WORKAROUNDS.make_valid and has_m):
        return result
    if not has_m or result.is_empty:
        return result
    return _reapply_measures(geometry, result)
# End make_valid function


def make_valid_structure(geometry):
    """
    Make Valid Structure
    """
    return make_valid(geometry, method='structure', keep_collapsed=False)
# End make_valid_structure function


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
    slicer = get_slicer(has_z=has_z, has_m=has_m)
    coords = build_coordinates(
        result, has_z=has_z, slicer=slicer, lookup=lookup)
    cls = FUDGEO_GEOMETRY_LOOKUP[shape_type][has_z, has_m]
    return from_wkb(cls(coords, srs_id=SRS_ID_WKB).wkb)
# End _reapply_measures function


if __name__ == '__main__':  # pragma: no cover
    pass
