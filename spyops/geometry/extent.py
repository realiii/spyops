# -*- coding: utf-8 -*-
"""
Extent functions
"""


from math import nan
from typing import TYPE_CHECKING

from fudgeo.util import get_extent
from numpy import isfinite

from spyops.shared.exception import BadExtentError
from spyops.shared.hint import EXTENT


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


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
    extent = _extent_from_index_or_geometry(feature_class)
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


def _extent_from_index_or_geometry(feature_class: 'FeatureClass') -> EXTENT:
    """
    Get the Extent from the Spatial Index, fail over to the extent derived
    from geometries.
    """
    extent = _extent_from_spatial_index(feature_class)
    if isfinite(extent).all():
        return extent
    else:  # pragma: no cover
        return get_extent(feature_class)
# End _extent_from_index_or_geometry function


if __name__ == '__main__':  # pragma: no cover
    pass
