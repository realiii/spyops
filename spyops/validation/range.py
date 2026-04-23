# -*- coding: utf-8 -*-
"""
Validate Range
"""


from functools import wraps
from typing import Any, Callable, Type

from spyops.shared.util import safe_float, safe_int
from spyops.validation.base import AbstractValidate


class ValidateRange(AbstractValidate):
    """
    Validate Range
    """
    def __init__(self, name: str, default: float,
                 min_value: float = 0, max_value: float = 1,
                 inclusive: bool = True, clamp: bool = True,
                 type_: Type[int | float] = float) -> None:
        """
        Initialize the ValidateRange class

        :param name: Name of the argument to validate
        :param default: Default value for the argument
        :param min_value: Minimum value for the range
        :param max_value: Maximum value for the range
        :param inclusive: Whether the range is inclusive
        :param clamp: Whether to clamp the value to the range
        :param type_: Type of the value to validate
        """
        super().__init__()
        self._name: str = name
        self._default: float = default
        min_ = min(min_value, max_value)
        max_ = max(min_value, max_value)
        self._min: float = min_
        self._max: float = max_
        self._inclusive: bool = inclusive
        self._clamp: bool = clamp
        self._type: Type[int | float] = type_
        self._check_inputs(
            name, min_value=min_, max_value=max_,
            default=default, inclusive=inclusive)
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
            value = self._get_object(kwargs)
            value = self._validate_value(value)
            self._set_object(self._type(value), kwargs=kwargs)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _check_inputs(self, name: str, min_value: float, max_value: float,
                      default: float, inclusive: bool) -> None:
        """
        Check Inputs, rough check
        """
        msg = f'Default for {name} must be between {min_value} and {max_value}'
        if inclusive:
            if default < self._min or default > self._max:
                raise ValueError(f'{msg} (inclusive)')
        else:
            if default <= self._min or default >= self._max:
                raise ValueError(f'{msg} (exclusive)')
    # End _check_inputs method

    def _get_object(self, kwargs: dict[str, Any]) -> float | int | None:
        """
        Get Object from kwargs and optionally perform some checks
        """
        value = kwargs[self._name]
        if self._type is int:
            return safe_int(value)
        return safe_float(value)
    # End _get_object method

    def _set_object(self, obj: float | int, kwargs: dict[str, Any]) -> None:
        """
        Set Object into the kwargs
        """
        kwargs[self._name] = obj
    # End _set_object method

    def _validate_value(self, value: float | int | None) -> float | int:
        """
        Validate Value against the range
        """
        if value is None:
            return self._default
        if not self._clamp:
            msg = f'{self._name} must be between {self._min} and {self._max}'
            if self._inclusive:
                if value < self._min or value > self._max:
                    raise ValueError(f'{msg} (inclusive)')
            else:
                if value <= self._min or value >= self._max:
                    raise ValueError(f'{msg} (exclusive)')
        else:
            if self._inclusive:
                if value < self._min:
                    return self._min
                if value > self._max:
                    return self._max
            else:
                if value <= self._min:
                    return self._min
                if value >= self._max:
                    return self._max
        return value
    # End _validate_value method
# End ValidateRange class


if __name__ == '__main__':  # pragma: no cover
    pass
