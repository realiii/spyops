# -*- coding: utf-8 -*-
"""
Shared Settings for Analysis
"""


from typing import Any, Self

from geomio.shared.enumeration import Settings
from geomio.shared.hint import XY_TOL
from geomio.shared.util import safe_float


__all__ = ['SETTINGS', 'Swap']


class _AnalysisSettings:
    """
    Analysis Settings
    """
    __slots__ = ['_overwrite', '_dimensions']

    def __init__(self) -> None:
        """
        Initialize the _AnalysisSettings class
        """
        super().__init__()
        self._overwrite: bool = False
        self._dimensions: _GeometryDimensions = _GeometryDimensions()
    # End init built-in

    @property
    def overwrite(self) -> bool:
        """
        Overwrite
        """
        return self._overwrite

    @overwrite.setter
    def overwrite(self, value: bool) -> None:
        self._overwrite = bool(value)
    # End overwrite property

    @property
    def xy_tolerance(self) -> XY_TOL:
        """
        XY Tolerance
        """
        return self._dimensions.xy_tolerance

    @xy_tolerance.setter
    def xy_tolerance(self, value: XY_TOL) -> None:
        self._dimensions.xy_tolerance = value
    # End xy_tolerance property
# End _AnalysisSettings class


class Swap:
    """
    Swap Settings via Context
    """
    def __init__(self, setting: Settings, value: Any) -> None:
        """
        Initialize the Swap class
        """
        super().__init__()
        setting = self._check_setting(setting)
        self._setting: Settings = setting
        self._cached: Any = getattr(SETTINGS, setting)
        self._value: Any = value
    # End init built-in

    @property
    def cached_value(self) -> Any:
        """
        Cached Value
        """
        return self._cached
    # End cached_value property

    @property
    def swap_value(self) -> Any:
        """
        The Swap Value which may be different from the specified value based on
        processing done inside the AnalysisSettings.
        """
        return self._value
    # End swap_value property

    @staticmethod
    def _check_setting(setting: Settings) -> Settings:
        """
        Check Setting is Expected
        """
        if isinstance(setting, Settings):
            return setting
        if not isinstance(setting, str):
            raise TypeError(f'Invalid setting: {setting!r}')
        return Settings(setting.casefold())
    # End _check_setting method

    def __enter__(self) -> Self:
        """
        Context Manager Enter
        """
        setattr(SETTINGS, self._setting, self._value)
        self._value = getattr(SETTINGS, self._setting)
        return self
    # End enter built-in

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Context Manager Exit
        """
        setattr(SETTINGS, self._setting, self._cached)
        return False
    # End exit built-in
# End Swap class


class _GeometryDimensions:
    """
    Geometry Dimensions
    """
    def __init__(self) -> None:
        """
        Initialize the _GeometryDimensions class
        """
        super().__init__()
        self._xy: XY_TOL = None
    # End init built-in

    @property
    def xy_tolerance(self) -> XY_TOL:
        """
        XY Tolerance
        """
        return self._xy

    @xy_tolerance.setter
    def xy_tolerance(self, value: XY_TOL) -> None:
        self._xy = safe_float(value)
    # End xy_tolerance property
# End _GeometryDimensions class


SETTINGS = _AnalysisSettings()


if __name__ == '__main__':  # pragma: no cover
    pass
