# -*- coding: utf-8 -*-
"""
Validation for Feature Classes, Tables, and GeoPackages
"""


from typing import Any, ClassVar

from fudgeo import FeatureClass, Table

from spyops.shared.constant import PADDED_PIPE
from spyops.shared.hint import NAMES
from spyops.validation.base import AbstractValidateTypeExists


class ValidateContent(AbstractValidateTypeExists):
    """
    Validate Content
    """
    def __init__(self, name: str, *, exists: bool = True,
                 has_content: bool = True) -> None:
        """
        Initialize the ValidateContent class
        """
        super().__init__(name=name, exists=exists)
        self._has_content: bool = has_content
    # End init built-in

    def _validate_content(self, obj: Any) -> None:
        """
        Validate Content
        """
        if not self._has_content:
            return
        if not obj.is_empty:
            return
        raise ValueError(f'{self._name} is empty')
    # End _validate_content method

    def _get_object(self, kwargs: dict[str, Any]) -> Any:
        """
        Get Object from kwargs and optionally perform some checks
        """
        obj = super()._get_object(kwargs)
        return self._check_element(obj)
    # End _get_object method

    def _validation(self, obj: Any) -> None:
        """
        Validation
        """
        self._validate_content(obj)
    # End _validation method
# End ValidateContent class


class ValidateElement(ValidateContent):
    """
    Validate Element
    """
    _types: ClassVar[tuple[type, ...]] = FeatureClass, Table
# End ValidateElement class


class ValidateTable(ValidateContent):
    """
    Validate Table
    """
    _types: ClassVar[tuple[type, ...]] = Table,
# End ValidateTable class


class ValidateFeatureClass(ValidateContent):
    """
    Validate Feature Class
    """
    _types: ClassVar[tuple[type, ...]] = FeatureClass,

    def __init__(self, name: str, *, exists: bool = True,
                 has_content: bool = True, geometry_types: NAMES = (),
                 has_z: bool = False, has_m: bool = False,
                 add_index: bool = True) -> None:
        """
        Initialize the ValidateFeatureClass class
        """
        super().__init__(name=name, exists=exists, has_content=has_content)
        self._geometry_types: NAMES = geometry_types
        self._has_z: bool = has_z
        self._has_m: bool = has_m
        self._add_index: bool = add_index
    # End init built-in

    def _validation(self, obj: Any) -> None:
        """
        Validation
        """
        super()._validation(obj)
        self._validate_geometry_types(obj)
        self._validate_zm(obj)
        self._add_spatial_index(obj)
    # End _validation method

    def _add_spatial_index(self, obj: FeatureClass) -> None:
        """
        Add Spatial Index
        """
        if not self._add_index:  # pragma: no cover
            return
        obj.add_spatial_index()
    # End _add_spatial_index method

    def _validate_zm(self, obj: FeatureClass) -> None:
        """
        Validate Extended Geometry with Z and / or M
        """
        if self._has_z and not obj.has_z:
            raise ValueError(f'{self._name} does not have Z values')
        if self._has_m and not obj.has_m:
            raise ValueError(f'{self._name} does not have M values')
    # End _validate_zm method

    def _validate_geometry_types(self, obj: FeatureClass) -> None:
        """
        Validate Geometry Types
        """
        if not (geom_types := self._geometry_types):
            return
        if isinstance(geom_types, str):
            geom_types = geom_types,
        if obj.shape_type in geom_types:
            return
        types = PADDED_PIPE.join(geom_types)
        raise ValueError(f'{self._name} must have geometry type of {types}')
    # End _validate_geometry_types method
# End ValidateFeatureClass class


if __name__ == '__main__':  # pragma: no cover
    pass
