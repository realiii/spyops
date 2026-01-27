# -*- coding: utf-8 -*-
"""
Coordinate Reference System and Geographic Transformation Settings
"""


from typing import Any, TYPE_CHECKING

from spyops.crs.util import get_crs_from_source


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, SpatialReferenceSystem
    from pyproj import CRS


class _Coordinates:
    """
    Coordinates
    """
    def __init__(self) -> None:
        """
        Initialize the _Coordinates class
        """
        super().__init__()
        self._output: CRS | None = None
    # End init built-in

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
# End _Coordinates class


if __name__ == '__main__':  # pragma: no cover
    pass
