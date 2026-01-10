# -*- coding: utf-8 -*-
"""
Workspace Settings
"""


from pathlib import Path
from typing import Any

from fudgeo import GeoPackage, MemoryGeoPackage
from fudgeo.constant import MEMORY

from gisworks.shared.database import is_geopackage
from gisworks.environment.enumeration import Setting
from gisworks.shared.hint import GPKG
from gisworks.environment.util import as_title


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


if __name__ == '__main__':  # pragma: no cover
    pass
