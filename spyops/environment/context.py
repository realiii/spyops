# -*- coding: utf-8 -*-
"""
Swap Context for an Environment / Analysis Setting
"""


from typing import Any, Self

from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.enumeration import Setting


class Swap:
    """
    Swap Setting via Context
    """
    def __init__(self, setting: Setting, value: Any) -> None:
        """
        Initialize the Swap class
        """
        super().__init__()
        setting = self._check_setting(setting)
        self._setting: Setting = setting
        self._cached: Any = getattr(ANALYSIS_SETTINGS, setting)
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
    def _check_setting(setting: Setting) -> Setting:
        """
        Check Setting is Expected
        """
        if isinstance(setting, Setting):
            return setting
        if not isinstance(setting, str):
            raise TypeError(f'Invalid setting: {setting!r}')
        return Setting(setting.casefold())
    # End _check_setting method

    def __enter__(self) -> Self:
        """
        Context Manager Enter
        """
        setattr(ANALYSIS_SETTINGS, self._setting, self._value)
        self._value = getattr(ANALYSIS_SETTINGS, self._setting)
        return self
    # End enter built-in

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Context Manager Exit
        """
        setattr(ANALYSIS_SETTINGS, self._setting, self._cached)
        return False
    # End exit built-in
# End Swap class


if __name__ == '__main__':  # pragma: no cover
    pass
