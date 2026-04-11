# -*- coding: utf-8 -*-
"""
Coordinate Reference System and Geographic Transformation Settings
"""


from typing import Any

from fudgeo import FeatureClass, SpatialReferenceSystem
from pyproj import CRS
from pyproj.transformer import Transformer

from spyops.crs.util import get_crs_from_source
from spyops.environment.base import Extent


class _Coordinates:
    """
    Coordinates
    """
    def __init__(self) -> None:
        """
        Initialize the _Coordinates class
        """
        super().__init__()
        self._extent: Extent | None = None
        self._output: CRS | None = None
        self._transformations: list[Transformer] = []
    # End init built-in

    @property
    def extent(self) -> Extent | None:
        """
        Processing Extent
        """
        return self._extent

    @extent.setter
    def extent(self, value: Extent | None) -> None:
        self._extent = value
    # End extent property

    @property
    def output(self) -> CRS | None:
        """
        Output Coordinate Reference System
        """
        return self._output

    @output.setter
    def output(self, value: CRS | SpatialReferenceSystem | FeatureClass | None) -> None:
        self._output = self._check_coordinates(value)
    # End current property

    @staticmethod
    def _check_coordinates(value: Any) -> CRS | None:
        """
        Check Coordinates
        """
        if value is None:
            return None
        return get_crs_from_source(value)
    # End _check_coordinates method

    @property
    def transformations(self) -> list[Transformer]:
        """
        Geographic Transformations
        """
        return self._transformations

    @transformations.setter
    def transformations(self, value: Transformer | list[Transformer]) -> None:
        self._transformations.clear()
        if isinstance(value, Transformer):
            self._transformations.append(value)
        elif isinstance(value, (list, tuple)):
            values = [v for v in value if isinstance(v, Transformer)]
            self._transformations.extend(values)
    # End transformations property
# End _Coordinates class


if __name__ == '__main__':  # pragma: no cover
    pass
