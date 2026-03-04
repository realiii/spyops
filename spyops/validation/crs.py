# -*- coding: utf-8 -*-
"""
Validation for Coordinate Reference Systems
"""


from functools import wraps
from typing import Any, Callable, ClassVar, TYPE_CHECKING, Union
from warnings import warn

from fudgeo import SpatialReferenceSystem
from pyproj import CRS

from spyops.crs.util import check_same_crs, get_crs_from_source
from spyops.shared.constant import SKIP_FILE_PREFIXES
from spyops.shared.exception import (
    CoordinateSystemNotSupportedError, CoordinateSystemNotSupportedWarning)
from spyops.shared.hint import NAMES
from spyops.validation.base import AbstractValidate, AbstractValidateType


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


class ValidateSupportedCRS(AbstractValidate):
    """
    Validate that feature classes have a Spatial Reference System that can
    be understood as a Coordinate Reference System.  Optionally, check that
    the CRSs are the same.
    """
    def __init__(self, *names: str, same: bool = False) -> None:
        """
        Initialize the ValidateSupportedCRS class

        :param names: Names of the argument to validate
        :param same: Coordinate Reference Systems must be the same
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
        crses = []
        valid = True
        for name in self._names:
            feature_class = kwargs[name]
            if crs := _check_supported_crs(feature_class, name=name):
                crses.append(crs)
            else:
                valid = False
        if not valid:
            raise CoordinateSystemNotSupportedError(
                'One or more feature classes have an unsupported '
                'Spatial Reference System, check warnings for details')
        return crses
    # End _check_spatial_reference method
# End ValidateSupportedCRS class


class ValidateCoordinateSystem(AbstractValidateType):
    """
    Validate the value for a Coordinate System is the correct object type.
    """
    _types: ClassVar[tuple[type, ...]] = CRS, SpatialReferenceSystem

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
            crs = self._get_object(kwargs)
            if not isinstance(crs, self._types):
                raise TypeError(
                    f'{self._name} must be a CRS or SpatialReferenceSystem')
            if _check_supported_crs(crs, name=self._name) is None:
                raise CoordinateSystemNotSupportedError(
                    'Specified coordinate system is an unsupported, '
                    'check warnings for details')
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in
# End ValidateCoordinateSystem class


def _check_supported_crs(source: Union[CRS, 'FeatureClass', SpatialReferenceSystem],
                         name: str) -> CRS | None:
    """
    Check Supported CRS
    """
    try:
        return get_crs_from_source(source)
    except CoordinateSystemNotSupportedError as err:
        warn(f'{name} has an unsupported CRS: {err}',
             category=CoordinateSystemNotSupportedWarning,
             skip_file_prefixes=SKIP_FILE_PREFIXES)
        return None
# End _check_supported_crs function


if __name__ == '__main__':  # pragma: no cover
    pass
