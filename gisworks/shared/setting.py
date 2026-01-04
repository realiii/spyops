# -*- coding: utf-8 -*-
"""
Shared Settings for Analysis
"""


from pathlib import Path
from typing import Any, Self

from fudgeo import GeoPackage, MemoryGeoPackage
from fudgeo.constant import MEMORY

from gisworks.shared.database import is_geopackage
from gisworks.shared.enumeration import Setting
from gisworks.shared.hint import GPKG, XY_TOL
from gisworks.shared.util import as_title, safe_float


__all__ = ['ANALYSIS_SETTINGS', 'Swap']


class _AnalysisSettings:
    """
    Analysis Settings
    """
    __slots__ = ['_overwrite', '_dimensions', '_workspace']

    def __init__(self) -> None:
        """
        Initialize the _AnalysisSettings class
        """
        super().__init__()
        self._overwrite: bool = False
        self._dimensions: _GeometryDimensions = _GeometryDimensions()
        self._workspace: _Workspace = _Workspace()
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

    @property
    def current_workspace(self) -> GPKG | None:
        """
        Current Workspace
        """
        return self._workspace.current

    @current_workspace.setter
    def current_workspace(self, value: GPKG | None) -> None:
        self._workspace.current = value
    # End current_workspace property

    @property
    def scratch_workspace(self) -> GPKG | None:
        """
        Scratch Workspace
        """
        return self._workspace.scratch

    @scratch_workspace.setter
    def scratch_workspace(self, value: GPKG | None) -> None:
        self._workspace.scratch = value
    # End scratch_workspace property
# End _AnalysisSettings class


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


class _Workspace:
    """
    Workspace
    """
    def __init__(self) -> None:
        """
        Initialize the _Workspace class
        """
        super().__init__()
        self._current: GPKG | None = None
        self._scratch: GPKG | None = MemoryGeoPackage.create()
    # End init built-in

    @property
    def current(self) -> GPKG:
        """
        Current Workspace
        """
        return self._current

    @current.setter
    def current(self, value: GPKG) -> None:
        self._current = self._check_workspace(
            value, setting=Setting.CURRENT_WORKSPACE)
    # End current property

    @property
    def scratch(self) -> GPKG | None:
        """
        Scratch GeoPackage
        """
        return self._scratch

    @scratch.setter
    def scratch(self, value: GPKG | None) -> None:
        self._scratch = self._check_workspace(
            value, setting=Setting.SCRATCH_WORKSPACE)
    # End scratch property

    @staticmethod
    def _check_workspace(value: Any, setting: Setting) -> GPKG | None:
        """
        Check Workspace
        """
        if isinstance(value, (GeoPackage, MemoryGeoPackage, type(None))):
            return value
        if isinstance(value, (str, Path)):
            if value == MEMORY:
                # NOTE new memory database is created each time, no sharing
                return MemoryGeoPackage.create()
            if is_geopackage(value):
                return GeoPackage(value)
            raise IOError(f'Unable to get {as_title(setting)} from: {value!r}')
        return None
    # End _check_workspace method
# End _Workspace class


ANALYSIS_SETTINGS: _AnalysisSettings = _AnalysisSettings()


if __name__ == '__main__':  # pragma: no cover
    pass
