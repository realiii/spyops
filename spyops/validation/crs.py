# -*- coding: utf-8 -*-
"""
Validation for Coordinate Reference Systems
"""


from functools import wraps
from typing import Any, Callable
from warnings import warn

from pyproj import CRS

from spyops.crs.util import check_same_crs, get_crs_from_source
from spyops.shared.exception import (
    CoordinateSystemNotSupportedError, CoordinateSystemNotSupportedWarning)
from spyops.shared.hint import NAMES
from spyops.validation.base import AbstractValidate


class ValidateCRS(AbstractValidate):
    """
    Validate that feature classes have a Spatial Reference System that can
    be understood as a Coordinate Reference System.  Optionally check that
    the CRSs are the same.
    """
    def __init__(self, *names: str, same: bool = False) -> None:
        """
        Initialize the ValidateCRS class
        """
        super().__init__()
        self._names: NAMES = names
        self._same: bool = same
    # End init built-in

    def __call__(self, func: Callable) -> Callable:
        """
        Make the class callable
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Handler for the arguments and keyword arguments.
            """
            kwargs = self._get_arguments(
                func=func, args=args, kwargs=kwargs)
            first, *others = self._check_spatial_reference(kwargs)
            self._check_same_crs(first, others)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _check_same_crs(self, first: CRS, others: list[CRS]) -> None:
        """
        Check Same CRS
        """
        if not self._same:
            return
        for other in others:
            check_same_crs(first, other)
    # End _check_same_crs method

    def _check_spatial_reference(self, kwargs: dict[str, Any]) -> list[CRS]:
        """
        Check Spatial Reference System for each feature class ensuring that
        it can be understood as a Coordinate Reference System.
        """
        crs = []
        valid = True
        for name in self._names:
            feature_class = kwargs[name]
            try:
                crs.append(get_crs_from_source(feature_class))
            except CoordinateSystemNotSupportedError as err:
                valid = False
                warn(f'{feature_class.name} has an unsupported CRS\n{err}',
                     category=CoordinateSystemNotSupportedWarning)
        if not valid:
            raise CoordinateSystemNotSupportedError(
                'One or more feature classes have an unsupported '
                'Spatial Reference System, check warnings for details')
        return crs
    # End _check_spatial_reference method
# End ValidateCRS class


if __name__ == '__main__':  # pragma: no cover
    pass
