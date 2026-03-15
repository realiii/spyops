# -*- coding: utf-8 -*-
"""
Validate Result
"""


from warnings import warn
from functools import wraps
from typing import Callable

from fudgeo import FeatureClass, Table

from spyops.geometry.extent import set_extent
from spyops.shared.constant import SKIP_FILE_PREFIXES
from spyops.shared.keywords import NAME_ATTR
from spyops.shared.exception import EmptyResultWarning, NoResultWarning
from spyops.shared.hint import ELEMENT
from spyops.validation.base import AbstractValidate


class ValidateResult(AbstractValidate):
    """
    Validate Result
    """
    def __call__(self, func: Callable) -> Callable:
        """
        Make the class callable
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Handler for the arguments and keyword arguments.
            """
            if not (result := func(*args, **kwargs)):  # pragma: no cover
                return result
            for element in self._make_iterable(result):
                if isinstance(element, Table):
                    _check_output(element)
                if isinstance(element, FeatureClass):
                    _check_output(element)
                    set_extent(element)
                    element.add_spatial_index()
            return result
        # End wrapper function
        return wrapper
    # End call built-in
# End ValidateResult class


def _check_output(element: ELEMENT) -> ELEMENT:
    """
    Check element for existence and content, warn if not present or empty
    """
    if not element:
        name = getattr(element, NAME_ATTR, 'Output result')
        warn(f'{name} was not created', category=NoResultWarning,
             skip_file_prefixes=SKIP_FILE_PREFIXES)
        return element
    if not len(element):
        warn(f'{element.name} created but contains no rows',
             category=EmptyResultWarning, skip_file_prefixes=SKIP_FILE_PREFIXES)
        return element
    return element
# End _check_output function


if __name__ == '__main__':  # pragma: no cover
    pass
