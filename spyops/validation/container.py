# -*- coding: utf-8 -*-
"""
Validation for Containers
"""


from functools import wraps
from pathlib import Path
from typing import Any, Callable, ClassVar, Type

from fudgeo import GeoPackage, MemoryGeoPackage
from fudgeo.constant import MEMORY

from spyops.environment import ANALYSIS_SETTINGS
from spyops.shared.keywords import GEOPACKAGE
from spyops.shared.hint import GPKG
from spyops.shared.util import safe_float, safe_int
from spyops.validation.base import AbstractValidate, AbstractValidateTypeExists


class ValidateGeopackage(AbstractValidateTypeExists):
    """
    Validate Geopackage
    """
    _types: ClassVar[tuple[type, ...]] = GeoPackage, MemoryGeoPackage

    def __init__(self, name: str = GEOPACKAGE, *, exists: bool = True) -> None:
        """
        Initialize the ValidateGeopackage class

        :param name: Name of the argument to validate
        :param exists: Ensure that the specified geopackage exists
        """
        super().__init__(name=name, exists=exists)
    # End init built-in

    def _validate_exists(self, obj: Any) -> bool:
        """
        Validate Exists
        """
        if not self._exists:
            return False
        if isinstance(obj.path, Path):
            if success := obj.path.is_file():  # pragma: no cover
                return success
        if isinstance(obj.path, str):
            if success := (obj.path == MEMORY):
                return success
        raise ValueError(f'{self._name} does not exist')
    # End _validate_exists method

    def _get_object(self, kwargs: dict[str, Any]) -> GPKG | None:
        """
        Get Object
        """
        if (function_gpkg := super()._get_object(kwargs)) is not None:
            return function_gpkg
        return ANALYSIS_SETTINGS.current_workspace
    # End _get_object method

    def _validation(self, obj: Any) -> None:
        """
        Validation
        """
        pass
    # End _validation method
# End ValidateGeopackage class


class ValidateValues(AbstractValidate):
    """
    Validate Values
    """
    def __init__(self, name: str, type_: Type[int | float] = float) -> None:
        """
        Initialize the ValidateRange class

        :param name: Name of the argument to validate
        :param type_: Type of the value to validate
        """
        super().__init__()
        self._name: str = name
        self._type: Type[int | float] = type_
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
            if not (values := self._get_object(kwargs)):
                raise ValueError(f'{self._name} contains no valid values')
            self._set_object(values, kwargs=kwargs)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _get_object(self, kwargs: dict[str, Any]) -> list[float | int]:
        """
        Get Object from kwargs and optionally perform some checks
        """
        obj = kwargs[self._name]
        values = self._make_iterable(obj)
        if self._type is int:
            values = [safe_int(v) for v in values]
        else:
            values = [safe_float(v) for v in values]
        return [v for v in values if v is not None]
    # End _get_object method

    def _set_object(self, obj: list[float | int],
                    kwargs: dict[str, Any]) -> None:
        """
        Set Object into the kwargs
        """
        kwargs[self._name] = obj
    # End _set_object method
# End ValidateValues class


if __name__ == '__main__':  # pragma: no cover
    pass
