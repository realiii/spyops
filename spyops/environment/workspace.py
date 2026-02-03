# -*- coding: utf-8 -*-
"""
Workspace Settings
"""


from pathlib import Path
from tempfile import gettempdir
from typing import Any

from fudgeo import GeoPackage, MemoryGeoPackage
from fudgeo.constant import MEMORY

from spyops.shared.database import is_geopackage
from spyops.environment.enumeration import Setting
from spyops.shared.hint import GPKG
from spyops.environment.util import as_title


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
        self._scratch: GPKG | None = None
        self._folder: Path | None = self._get_temp_path()
    # End init built-in

    @staticmethod
    def _get_temp_path() -> Path | None:
        """
        Get Temp Path
        """
        try:
            return Path(gettempdir())
        except FileNotFoundError:
            return None
    # End _get_temp_path method

    @property
    def current(self) -> GPKG | None:
        """
        Current Workspace
        """
        return self._current

    @current.setter
    def current(self, value: GPKG | None) -> None:
        self._current = self._check_workspace(
            value, setting=Setting.CURRENT_WORKSPACE)
    # End current property

    @property
    def folder(self) -> Path | None:
        """
        Scratch Folder
        """
        return self._folder

    @folder.setter
    def folder(self, value: Path | None) -> None:
        if value is None or not isinstance(value, Path):
            value = None
        elif isinstance(value, Path) and not value.is_dir():
            value = None
        self._folder = value
    # End folder property

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


if __name__ == '__main__':  # pragma: no cover
    pass
