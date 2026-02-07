# -*- coding: utf-8 -*-
"""
Base Classes for Validation
"""


from abc import ABCMeta, abstractmethod
from functools import wraps
from inspect import signature
from typing import Any, Callable, ClassVar

from spyops.environment import ANALYSIS_SETTINGS
from spyops.shared.constant import PADDED_PIPE
from spyops.shared.hint import GPKG


class AbstractValidate(metaclass=ABCMeta):
    """
    Abstract Validate
    """
    @abstractmethod
    def __call__(self, func: Callable) -> Callable:  # pragma: no cover
        """
        Make the class callable
        """
        pass
    # End call built-in

    @staticmethod
    def _get_arguments(func: Callable, args: tuple[Any, ...],
                       kwargs: dict[str, Any]) -> dict[str, Any]:
        """
        Get the arguments and values as kwargs
        """
        sig = signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        return bound.arguments
    # End _get_arguments method

    @staticmethod
    def _make_iterable(obj: Any) -> tuple | list:
        """
        Make iterable
        """
        if not isinstance(obj, (list, tuple)):
            return obj,
        else:  # pragma: no cover
            return obj
    # End _make_iterable method
# End AbstractValidate class


class AbstractValidateArgument(AbstractValidate, metaclass=ABCMeta):
    """
    Abstract Validation on an Argument by Name
    """
    def __init__(self, name: str) -> None:
        """
        Initialize the AbstractValidateArgument class
        """
        super().__init__()
        self._name: str = name
    # End init built-in

    def _get_object(self, kwargs: dict[str, Any]) -> Any:
        """
        Get Object from kwargs and optionally perform some checks
        """
        return kwargs[self._name]
    # End _get_object method

    def _set_object(self, obj: Any, kwargs: dict[str, Any]) -> None:
        """
        Set Object into the kwargs
        """
        kwargs[self._name] = obj
    # End _set_object method
# End AbstractValidateArgument class


class AbstractValidateType(AbstractValidateArgument, metaclass=ABCMeta):
    """
    Abstract Validate Type
    """
    _types: ClassVar[tuple[type, ...]] = ()

    def _check_element(self, obj: Any) -> Any:
        """
        Check Element
        """
        if not isinstance(obj, str):
            return obj
        if not (settings_gpkg := ANALYSIS_SETTINGS.current_workspace):
            return obj
        return self._by_name(obj, settings_gpkg)
    # End _check_element method

    def _by_name(self, obj: str, geopackage: GPKG) -> Any:
        """
        Check for an element by Name
        """
        return geopackage[obj]
    # End _by_name method

    def _validate_type(self, obj: Any) -> None:
        """
        Validate Type
        """
        if isinstance(obj, self._types):
            return
        types = PADDED_PIPE.join(t.__name__ for t in self._types)
        raise TypeError(
            f'{self._name} must be {types}, got {type(obj).__name__}')
    # End _validate_type method
# End AbstractValidateType class


class AbstractValidateTypeExists(AbstractValidateType):
    """
    Abstract Validate Type and Object Exists
    """
    def __init__(self, name: str, *, exists: bool = True) -> None:
        """
        Initialize the ValidateContent class
        """
        super().__init__(name=name)
        self._exists: bool = exists
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
            kwargs = self._get_arguments(func=func, args=args, kwargs=kwargs)
            obj = self._get_object(kwargs)
            self._validate_type(obj)
            self._set_object(obj, kwargs=kwargs)
            if not self._validate_exists(obj):
                return func(**kwargs)
            self._validation(obj)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _validate_exists(self, obj: Any) -> bool:
        """
        Validate Exists
        """
        if not self._exists:
            return False
        if obj.exists:
            return True
        raise ValueError(f'{self._name} does not exist')
    # End _validate_exists method

    @abstractmethod
    def _validation(self, obj: Any) -> None:  # pragma: no cover
        """
        Validation
        """
        pass
    # End _validation method
# End AbstractValidateTypeExists class


if __name__ == '__main__':  # pragma: no cover
    pass
