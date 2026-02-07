# -*- coding: utf-8 -*-
"""
Data Management for Feature Classes
"""


from typing import TYPE_CHECKING

from numpy import isfinite

from spyops.geometry.extent import extent_from_index_or_geometry
from spyops.shared.constant import SOURCE
from spyops.validation import validate_feature_class


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


@validate_feature_class(SOURCE)
def recalculate_feature_class_extent(source: 'FeatureClass') -> 'FeatureClass':
    """
    Recalculate Extent of Feature Class

    Recalculates the extent of a feature class and stores the results in the
    GeoPackage internal tables.
    """
    extent = extent_from_index_or_geometry(source)
    if isfinite(extent).all():
        source.extent = extent
    return source
# End recalculate_feature_class_extent function


if __name__ == '__main__':  # pragma: no cover
    pass
