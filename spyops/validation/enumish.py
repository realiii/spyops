# -*- coding: utf-8 -*-
"""
Validation Enumeration-esque Values
"""


from enum import StrEnum
from functools import wraps
from typing import Any, Callable, Type

from fudgeo.enumeration import GeometryType

from spyops.geometry.validate import get_geometry_dimension
from spyops.shared.enumeration import OutputTypeOption
from spyops.shared.exception import OperationsError
from spyops.shared.util import check_enumeration
from spyops.validation.base import AbstractValidate, AbstractValidateArgument


class ValidateEnumeration(AbstractValidateArgument):
    """
    Validate Item is of the expected Enumeration
    """
    def __init__(self, name: str, enum: Type[StrEnum]) -> None:
        """
        Initialize the ValidateEnumeration class
        """
        super().__init__(name)
        self._enum: Type[StrEnum] = enum
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
            obj = self._get_object(kwargs)
            obj = self._validate_value(obj)
            self._set_object(obj, kwargs=kwargs)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _validate_value(self, obj: Any) -> Any:
        """
        Validate Value
        """
        return check_enumeration(obj, enum=self._enum)
    # End _validate_value method
# End ValidateEnumeration class


class ValidateOutputType(AbstractValidate):
    """
    Validate Output Type
    """
    def __init__(self, enum_name: str, name: str) -> None:
        """
        Initialize the ValidateOutputType class
        """
        super().__init__()
        self._enum_name: str = enum_name
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
            if kwargs[self._enum_name] != OutputTypeOption.LINE:
                return func(**kwargs)
            if not get_geometry_dimension(kwargs[self._name]):
                raise OperationsError(
                    f'{self._name} features class must be a '
                    f'{GeometryType.linestring} or {GeometryType.polygon} '
                    f'shape type for Output Type "{OutputTypeOption.LINE}"')
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in
# End ValidateOutputType class


if __name__ == '__main__':  # pragma: no cover
    pass
