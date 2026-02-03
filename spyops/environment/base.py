# -*- coding: utf-8 -*-
"""
Base Classes for Environment
"""


from typing import Self, TYPE_CHECKING

from numpy import isnan
from shapely import Polygon
from shapely.creation import box
from shapely.lib import force_2d

from spyops.crs.util import get_crs_from_source
from spyops.geometry.extent import extent_from_feature_class
from spyops.geometry.wa import make_valid

if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from pyproj import CRS


class Extent:
    """
    Processing Extent
    """
    def __init__(self, polygon: Polygon | None, crs: 'CRS') -> None:
        """
        Initialize the Extent class
        """
        super().__init__()
        self._polygon: Polygon = self._check_polygon(polygon)
        self._crs: 'CRS' = crs
    # End init built-in

    def __bool__(self) -> bool:
        """
        Boolean Value
        """
        return not self.polygon.is_empty and self.polygon.is_valid
    # End bool built-in

    def __eq__(self, other: Self) -> bool:
        """
        Equality
        """
        if not isinstance(other, Extent):
            return NotImplemented
        return self.polygon == other.polygon and self.crs == other.crs
    # End eq built-in

    @staticmethod
    def _check_polygon(polygon: Polygon | None) -> Polygon:
        """
        Check Polygon
        """
        if polygon is None:
            return Polygon()
        if not isinstance(polygon, Polygon):
            raise TypeError(f'Expected Polygon, got {type(polygon).__name__}')
        if not polygon.is_valid:
            polygon = make_valid(polygon)
        return force_2d(polygon)
    # End _check_polygon method

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """
        Bounds
        """
        return self.polygon.bounds
    # End bounds property

    @property
    def coordinate_reference_system(self) -> 'CRS':
        """
        Coordinate Reference System
        """
        return self._crs
    # End coordinate_reference_system property
    crs = coordinate_reference_system

    @property
    def polygon(self) -> Polygon:
        """
        Polygon
        """
        return self._polygon
    # End polygon property

    @classmethod
    def from_bounds(cls, x_min: float, y_min: float, x_max: float,
                    y_max: float, crs: 'CRS') -> Self:
        """
        Create an Extent from XY Bounds
        """
        if isnan((x_min, y_min, x_max, y_max)).any():
            return cls(None, crs=crs)
        return cls(box(xmin=x_min, ymin=y_min, xmax=x_max,
                       ymax=y_max, ccw=False), crs=crs)
    # End from_bounds method

    @classmethod
    def from_feature_class(cls, feature_class: 'FeatureClass') -> Self:
        """
        Create an Extent from a Feature Class
        """
        crs = get_crs_from_source(feature_class)
        extent = extent_from_feature_class(feature_class)
        if isnan(extent).all():
            return cls(None, crs=crs)
        return cls(box(*extent, ccw=False), crs=crs)
    # End from_feature_class method
# End Extent class


if __name__ == '__main__':  # pragma: no cover
    pass
