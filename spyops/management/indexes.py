# -*- coding: utf-8 -*-
"""
Data Management for Indexes
"""


from typing import TYPE_CHECKING

from spyops.shared.constant import SOURCE
from spyops.validation import validate_feature_class, validate_result


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['add_spatial_index']


@validate_result()
@validate_feature_class(SOURCE, has_content=False)
def add_spatial_index(source: 'FeatureClass') -> 'FeatureClass':
    """
    Add Spatial Index

    Creates a spatial index on the input feature class.  If a spatial index
    already exists, it is not recreated.
    """
    source.add_spatial_index()
    return source
# End add_spatial_index function


if __name__ == '__main__':  # pragma: no cover
    pass
