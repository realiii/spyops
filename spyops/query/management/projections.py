# -*- coding: utf-8 -*-
"""
Queries for Projections and Transformations
"""
from functools import cached_property
from typing import TYPE_CHECKING

from fudgeo import SpatialReferenceSystem
from pyproj import CRS

from spyops.crs.util import srs_from_crs
from spyops.query.base import BaseQuerySelect


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


class QueryProject(BaseQuerySelect):
    """
    Query for Project
    """
# End QueryProject class


class QueryDefineProjection(BaseQuerySelect):
    """
    Query for Define Projection
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass',
                 coordinate_system: CRS | SpatialReferenceSystem) -> None:
        """
        Initialize the QueryDefineProjection class
        """
        super().__init__(source, target=target)
        self._crs: CRS | SpatialReferenceSystem = coordinate_system
    # End init built-in

    @cached_property
    def spatial_reference_system(self) -> SpatialReferenceSystem:
        """
        Spatial Reference System, this will be the output coordinate
        system specified in the function.
        """
        if isinstance(self._crs, CRS):
            return srs_from_crs(self._crs)
        return self._crs
    # End spatial_reference_system property

    @property
    def source_transformer(self) -> None:
        """
        Source Transformer, overloaded since we do not want to transform.
        """
        return None
    # End source_transformer property
# End QueryDefineProjection class


if __name__ == '__main__':  # pragma: no cover
    pass
