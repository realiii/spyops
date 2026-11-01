# -*- coding: utf-8 -*-
"""
Base Classes for Environment
"""


from typing import NamedTuple, Self, TYPE_CHECKING

from shapely import Polygon, force_2d
from shapely.creation import box
from shapely.coordinates import transform
from shapely.measurement import total_bounds

from spyops.crs.transform import get_transform_best_guess
from spyops.crs.util import get_crs_from_source
from spyops.environment.util import get_geographic_transformation
from spyops.geometry.extent import extent_from_feature_class, is_degenerate
from spyops.geometry.wa.valid import make_valid_structure
from spyops.shared.exception import BadExtentError
from spyops.shared.hint import FEATURE_CLASSES


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, SpatialReferenceSystem
    from pyproj import CRS
    from pyproj.transformer import Transformer


class FeatureClassProxy(NamedTuple):
    """
    Feature Class Proxy
    """
    extent: tuple[float, float, float, float]
    spatial_reference_system: 'SpatialReferenceSystem'
# End FeatureClassProxy class


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
        Equals Override
        """
        if not isinstance(other, Extent):  # pragma: no cover
            return NotImplemented
        return self.polygon == other.polygon and self.crs == other.crs
    # End eq built-in

    def is_degenerate(self) -> bool:
        """
        Is Degenerate
        """
        return is_degenerate(self.bounds)
    # End is_degenerate method

    @staticmethod
    def _check_polygon(polygon: Polygon | None) -> Polygon:
        """
        Check Polygon
        """
        if polygon is None:
            return Polygon()
        if not isinstance(polygon, Polygon):
            raise TypeError(f'Expected Polygon, got {type(polygon).__name__}')
        return make_valid_structure(force_2d(polygon))
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
        if is_degenerate((x_min, y_min, x_max, y_max)):
            return cls(None, crs=crs)
        x_min, x_max = min(x_min, x_max), max(x_min, x_max)
        y_min, y_max = min(y_min, y_max), max(y_min, y_max)
        return cls(box(xmin=x_min, ymin=y_min, xmax=x_max, ymax=y_max), crs=crs)
    # End from_bounds method

    @classmethod
    def from_feature_class(cls, feature_class: 'FeatureClass') -> Self:
        """
        Create an Extent from a Feature Class
        """
        crs = get_crs_from_source(feature_class)
        try:
            extent = extent_from_feature_class(feature_class)
        except BadExtentError:
            return cls(None, crs=crs)
        # noinspection bad-argument-type
        return cls(box(*extent), crs=crs)
    # End from_feature_class method

    @classmethod
    def from_feature_classes(cls, feature_classes: FEATURE_CLASSES,
                             transformations: list['Transformer']) -> Self:
        """
        Create an Extent from a Feature Class
        """
        extents = [cls.from_feature_class(fc) for fc in feature_classes]
        extents = [e for e in extents if e]
        if not extents:
            source, *_ = feature_classes
            return cls(None, crs=get_crs_from_source(source))
        target, *others = extents
        if len(extents) == 1:
            return target
        target_crs = target.coordinate_reference_system
        polygons = [target.polygon]
        for other in others:
            if not (transformer := get_geographic_transformation(
                    source_crs=other.crs, target_crs=target_crs,
                    transformations=transformations)):
                transformer = get_transform_best_guess(other.crs, target_crs)
            polygon = other.polygon
            if transformer:
                # noinspection bad-argument-type
                polygon = transform(
                    polygon, transformation=transformer.transform,
                    interleaved=False)
            polygons.append(polygon)
        bounds = total_bounds(polygons)
        # noinspection bad-argument-type
        if is_degenerate(bounds):
            return cls(None, crs=target_crs)
        return cls.from_bounds(*bounds, crs=target_crs)
    # End from_feature_classes method
# End Extent class


if __name__ == '__main__':  # pragma: no cover
    pass
