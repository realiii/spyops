# -*- coding: utf-8 -*-
"""
Extent functions
"""


from math import nan
from typing import Callable, TYPE_CHECKING

from bottleneck import nanmax, nanmin
from fudgeo.util import get_extent
from numpy import isfinite
from shapely.coordinates import get_coordinates

from spyops.geometry.util import find_slice_indexes
from spyops.shared.exception import BadExtentError
from spyops.shared.hint import EXTENT


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from numpy import ndarray


def set_extent(feature_class: 'FeatureClass') -> None:
    """
    Set Extent on a Feature Class using existing, spatial index, or
    geometry extents.
    """
    try:
        feature_class.extent = extent_from_feature_class(feature_class)
    except BadExtentError:  # pragma: no cover
        return
# End set_extent function


def extent_from_feature_class(feature_class: 'FeatureClass') -> EXTENT:
    """
    Returns the extent from a feature class, use the extent if it has
    been set, if not check the spatial index extent, failing over to
    brute force check of all features.
    """
    extent = feature_class.extent
    if isfinite(extent).all():
        return extent
    extent = extent_from_index_or_geometry(feature_class)
    if isfinite(extent).all():
        return extent
    else:  # pragma: no cover
        raise BadExtentError(
            f'{feature_class.name} is empty or only contains empty geometries')
# End extent_from_feature_class function


def _extent_from_spatial_index(feature_class: 'FeatureClass') -> EXTENT:
    """
    Extent from Spatial Index
    """
    empty = nan, nan, nan, nan
    if not feature_class.has_spatial_index:  # pragma: no cover
        return empty
    with feature_class.geopackage.connection as cin:
        cursor = cin.execute(f"""
            SELECT MIN(minx) AS MIN_X, MIN(miny) AS MIN_Y, 
                   MAX(maxx) AS MAX_X, MAX(maxy) AS MAX_Y
            FROM {feature_class.spatial_index_name}""")
    extent = cursor.fetchone()
    if not extent:  # pragma: no cover
        return empty
    if None in extent:  # pragma: no cover
        return empty
    return extent
# End _extent_from_spatial_index function


def extent_from_index_or_geometry(feature_class: 'FeatureClass') -> EXTENT:
    """
    Get the Extent from the Spatial Index, fail over to the extent derived
    from geometries.
    """
    extent = _extent_from_spatial_index(feature_class)
    if isfinite(extent).all():
        return extent
    else:  # pragma: no cover
        return get_extent(feature_class)
# End extent_from_index_or_geometry function


def extent_minimum(geoms: 'ndarray', *, has_z: bool, has_m: bool) -> list:
    """
    Extent Minimums for Non-Point Geometries
    """
    return _get_partial_extent(geoms, has_z=has_z, has_m=has_m, func=nanmin)
# End extent_minimum function


def extent_maximum(geoms: 'ndarray', *, has_z: bool, has_m: bool) -> list:
    """
    Extent Maximums for Non-Point Geometries
    """
    return _get_partial_extent(geoms, has_z=has_z, has_m=has_m, func=nanmax)
# End extent_maximum function


def _get_partial_extent(geoms: 'ndarray', *, has_z: bool, has_m: bool,
                        func: Callable) -> list:
    """
    Get Partial Extent
    """
    coords, indexes = get_coordinates(
        geoms, include_z=has_z, include_m=has_m, return_index=True)
    ids = find_slice_indexes(indexes)
    return [func(coords[b:e], axis=0) for b, e in zip(ids[:-1], ids[1:])]
# End _get_partial_extent function


if __name__ == '__main__':  # pragma: no cover
    pass
