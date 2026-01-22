# -*- coding: utf-8 -*-
"""
Validation for Coordinate Reference Systems
"""


from functools import wraps
from typing import Callable

from spyops.crs.util import check_same_crs, get_crs_from_source
from spyops.shared.hint import NAMES
from spyops.validation.base import AbstractValidate


class ValidateSameCRS(AbstractValidate):
    """
    Validate Same Coordinate Reference System
    """
    def __init__(self, *names) -> None:
        """
        Initialize the ValidateSameCRS class
        """
        super().__init__()
        self._names: NAMES = names
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
            first, *others = self._names
            crs = get_crs_from_source(kwargs[first])
            for other in others:
                check_same_crs(crs, get_crs_from_source(kwargs[other]))
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in
# End ValidateSameCRS class


if __name__ == '__main__':  # pragma: no cover
    pass
