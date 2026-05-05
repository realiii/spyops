# -*- coding: utf-8 -*-
"""
Validation for Feature Classes, Tables, and GeoPackages
"""


from functools import wraps
from typing import Any, Callable, ClassVar

from fudgeo import FeatureClass, MemoryGeoPackage, Table

from spyops.shared.constant import PADDED_PIPE
from spyops.shared.exception import OverwriteError
from spyops.shared.hint import ELEMENT, GPKG, NAMES
from spyops.validation.base import AbstractValidate, AbstractValidateTypeExists


class ValidateContent(AbstractValidateTypeExists):
    """
    Validate Content
    """
    def __init__(self, name: str, *, exists: bool = True,
                 has_content: bool = True, is_output: bool = False) -> None:
        """
        Initialize the ValidateContent class

        :param name: Name of the argument to validate
        :param exists: Ensure that the specified item exists
        :param has_content: Ensure that the specified item has content
        :param is_output: Distinguish between input and output items
        """
        super().__init__(name=name, exists=exists)
        self._has_content: bool = has_content
        self._is_output: bool = is_output
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

    def _by_name(self, obj: str, geopackage: GPKG) -> Any:
        """
        Check for an element by Name
        """
        if self._is_output:
            return Table(geopackage=geopackage, name=obj)
        return geopackage[obj]
    # End _by_name method

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


class ValidateElements(ValidateElement):
    """
    Validate Elements
    """
    def _get_object(self, kwargs: dict[str, Any]) -> Any:
        """
        Get Object from kwargs and optionally perform some checks
        """
        obj = []
        for o in self._make_iterable(super()._get_object(kwargs)):
            obj.append(self._check_element(o))
        return obj
    # End _get_object method

    def _validate_exists(self, obj: Any) -> bool:
        """
        Validate Exists
        """
        exists = []
        for o in obj:
            if super()._validate_exists(o):
                exists.append(o)
        obj[:] = exists
        return bool(exists)
    # End _validate_exists method

    def _validate_type(self, obj: Any) -> None:
        """
        Validate Type
        """
        for o in obj:
            super()._validate_type(o)
    # End _validate_type method

    def _validation(self, obj: Any) -> None:
        """
        Validation
        """
        for o in obj:
            self._validate_content(o)
    # End _validation method
# End ValidateElements class


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
                 has_content: bool = True, is_output: bool = False,
                 geometry_types: NAMES = (),
                 has_z: bool = False, has_m: bool = False,
                 add_index: bool = True) -> None:
        """
        Initialize the ValidateFeatureClass class
        """
        super().__init__(name=name, exists=exists, is_output=is_output,
                         has_content=has_content)
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


class ValidateOverwriteInput(AbstractValidate):
    """
    Validate Overwrite Input, use in conjunction with validate_element,
    validate_table, or validate_feature_class decorators so that the target
    and inputs have been validated before this validation is performed.
    """
    def __init__(self, target: str, *inputs: str) -> None:
        """
        Initialize the ValidateOverwriteInput class
        """
        super().__init__()
        self._target: str = target
        self._inputs: NAMES = inputs
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
            target: ELEMENT = kwargs[self._target]
            for name in self._inputs:
                self._check_same(target, other=kwargs[name], name=name)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _check_same(self, target: ELEMENT, other: ELEMENT, name: str) -> None:
        """
        Check Target Same as Input
        """
        if target.name.casefold() != other.name.casefold():
            return
        if not self._check_same_geopackage(target, other):
            return
        raise OverwriteError(
            f'Value for output argument {self._target} is same as value '
            f'for input argument {name}')
    # End _check_same method

    @staticmethod
    def _check_same_geopackage(target: ELEMENT, other: ELEMENT) -> bool:
        """
        Check Same GeoPackage
        """
        if target.geopackage is other.geopackage:
            return True
        if not isinstance(target.geopackage, other.geopackage.__class__):
            return False
        if isinstance(target.geopackage, MemoryGeoPackage):
            # NOTE if get here identity check has failed, we assume two
            #  different MemoryGeoPackages, which is true unless someone has
            #  taken control over the connection string for MemoryGeoPackage
            #  or done some other changes to the internals
            return True
        else:
            return target.geopackage.path.samefile(other.geopackage.path)
    # End _check_same_geopackage method
# End ValidateOverwriteInput class


if __name__ == '__main__':  # pragma: no cover
    pass
