# -*- coding: utf-8 -*-
"""
Validation for Containers
"""

from pathlib import Path
from typing import Any, ClassVar

from fudgeo import GeoPackage, MemoryGeoPackage
from fudgeo.constant import MEMORY

from spyops.environment import ANALYSIS_SETTINGS
from spyops.shared.keywords import GEOPACKAGE
from spyops.shared.hint import GPKG
from spyops.validation.base import AbstractValidateTypeExists


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


if __name__ == '__main__':  # pragma: no cover
    pass
