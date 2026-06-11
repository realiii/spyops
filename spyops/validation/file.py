# -*- coding: utf-8 -*-
"""
Validate File
"""

from functools import wraps
from pathlib import Path
from typing import Any, Callable

from spyops.environment import ANALYSIS_SETTINGS
from spyops.shared.constant import DOT
from spyops.validation.base import AbstractValidate


class ValidateFile(AbstractValidate):
    """
    Validate File
    """
    def __init__(self, name: str, extension: str | None = None,
                 is_output: bool = True) -> None:
        """
        Initialize the ValidateFile class

        :param name: Name of the argument to validate
        :param extension: File name will be forced to use this extension
        :param is_output: Distinguish between input and output items
        """
        super().__init__()
        self._name: str = name
        self._ext: str | None = self._check_extension(extension)
        self._is_output: bool = is_output
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
            if not (path := self._get_object(kwargs)):
                raise ValueError(f'{self._name} does not contain a valid path')
            path = self._check_path(self._make_path(path))
            self._set_object(path, kwargs=kwargs)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    @staticmethod
    def _check_extension(ext: str | None) -> str | None:
        """
        Check Extension
        """
        if not ext:
            return None
        if not (ext := ext.strip()):
            return None
        if not ext.startswith(DOT):
            ext = f'{DOT}{ext}'
        return ext
    # End _check_extension method

    def _get_object(self, kwargs: dict[str, Any]) -> Path | None:
        """
        Get Object from kwargs and optionally perform some checks
        """
        obj = kwargs[self._name]
        if not isinstance(obj, (Path, str)):
            return None
        if isinstance(obj, str):
            if not (obj := obj.strip()):
                return None
            obj = Path(obj)
        return obj
    # End _get_object method

    def _make_path(self, obj: Path) -> Path:
        """
        Make Path
        """
        obj = obj.resolve()
        if self._ext is not None:
            obj = obj.with_suffix(self._ext)
        return obj
    # End _make_path method

    def _check_path(self, obj: Path) -> Path:
        """
        Check Path
        """
        if not self._is_output:
            if not obj.is_file():
                raise FileNotFoundError(f'{str(obj)} does not exist')
        else:
            if not ANALYSIS_SETTINGS.overwrite and obj.is_file():
                raise FileExistsError(f'{str(obj)} already exists')
        return obj
    # End _check_path method

    def _set_object(self, obj: Path, kwargs: dict[str, Any]) -> None:
        """
        Set Object into the kwargs
        """
        kwargs[self._name] = obj
    # End _set_object method
# End ValidateFile class


if __name__ == '__main__':  # pragma: no cover
    pass
