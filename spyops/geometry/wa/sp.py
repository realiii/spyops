# -*- coding: utf-8 -*-
"""
Set Precision Workaround
"""


from warnings import warn

from numpy import ndarray
from shapely import MultiPolygon, Polygon, set_precision as _set_precision

from spyops.geometry.wa.uwa import USE_WORKAROUNDS
from spyops.shared.constant import SKIP_FILE_PREFIXES
from spyops.shared.exception import ShapelyWarning


def set_precision(geometry, grid_size, mode='valid_output', **kwargs):
    """
    Set Precision Workaround -- just a warning
    """
    if USE_WORKAROUNDS.set_precision and grid_size > 0:
        types = Polygon, MultiPolygon
        if isinstance(geometry, (list, tuple, ndarray)):
            if not len(geometry):
                is_polygon = has_m = False
            else:
                geoms = geometry[:(min(25, len(geometry)))]
                is_polygon = any(isinstance(g, types) for g in geoms)
                has_m = any(g.has_m for g in geoms)
        else:
            is_polygon = isinstance(geometry, types)
            has_m = geometry.has_m
        if is_polygon and has_m:
            warn(f'Setting precision on measured polygons changes the '
                 f'measure value for the last point in the polygon. '
                 f'ref shapely/shapely#2402', category=ShapelyWarning,
                 skip_file_prefixes=SKIP_FILE_PREFIXES)
    # noinspection PyTypeChecker
    return _set_precision(geometry, grid_size=grid_size, mode=mode, **kwargs)
# End set_precision function


if __name__ == '__main__':  # pragma: no cover
    pass
