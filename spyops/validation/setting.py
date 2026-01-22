# -*- coding: utf-8 -*-
"""
Validation for Settings that might also be an input
"""


from functools import wraps
from typing import Any, Callable

from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.shared.hint import XY_TOL
from spyops.shared.util import safe_float
from spyops.validation.base import AbstractValidate


class ValidateXYTolerance(AbstractValidate):
    """
    Validate XY Tolerance
    """
    def __init__(self, name: str = str(Setting.XY_TOLERANCE)) -> None:
        """
        Initialize the ValidateXYTolerance class
        """
        super().__init__()
        self._name: str = name
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
            tolerance = self._get_object(kwargs)
            tolerance = self._validate_value(tolerance)
            self._set_object(tolerance, kwargs=kwargs)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _get_object(self, kwargs: dict[str, Any]) -> XY_TOL:
        """
        Get Object from kwargs and optionally perform some checks
        """
        return safe_float(kwargs[self._name])
    # End _get_object method

    def _set_object(self, obj: XY_TOL, kwargs: dict[str, Any]) -> None:
        """
        Set Object into the kwargs
        """
        kwargs[self._name] = obj
    # End _set_object method

    @staticmethod
    def _validate_value(function_xy: XY_TOL) -> XY_TOL:
        """
        Validate Value and also compare with XY Setting

        When working with shapely the grid size parameter:
        * None --> use the highest precision of inputs
        * 0 --> use double precision

        The default precision for geometries if not specified is 0,
        which means double precision.  For our use cases at the moment
        the use of 0 and None are the same since we are not working with
        direct input of geometries but rather feature classes.

        When a value provided is less than 0, it is treated as 0.
        """
        settings_xy = ANALYSIS_SETTINGS.xy_tolerance
        has_input = function_xy is not None
        has_settings = settings_xy is not None
        if not has_settings:
            if not has_input:
                return function_xy
            tolerance = function_xy
        else:
            if has_input:
                tolerance = function_xy
            else:
                tolerance = settings_xy
        return max(0, tolerance)
    # End _validate_value method
# End ValidateXYTolerance class


if __name__ == '__main__':  # pragma: no cover
    pass
