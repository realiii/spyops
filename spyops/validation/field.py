# -*- coding: utf-8 -*-
"""
Validation for Fields
"""


from functools import wraps
from typing import Any, Callable, ClassVar

from fudgeo import Field

from spyops.geometry.validate import (
    check_dimension, check_zm, get_geometry_dimension, get_geometry_zm)
from spyops.shared.constant import PADDED_PIPE
from spyops.shared.keywords import NAME_ATTR
from spyops.shared.field import TYPE_ALIAS_LUT, validate_fields
from spyops.shared.hint import ELEMENT, NAMES
from spyops.validation.base import AbstractValidate, AbstractValidateType


class ValidateField(AbstractValidateType):
    """
    Validate Field
    """
    _types: ClassVar[tuple[type, ...]] = Field,

    def __init__(self, name: str, *, data_types: NAMES = (),
                 element_name: str = '', exists: bool = True,
                 single: bool = False, exclude_geometry: bool = True,
                 exclude_primary: bool = True, is_optional: bool = False) -> None:
        """
        Initialize the ValidateField class

        :param name: Name of the argument to validate
        :param data_types: Data types to validate against
        :param element_name: Argument Name of the element to validate against
        :param exists: Ensure that the specified field exists
        :param single: Expect only a single field
        :param exclude_geometry: Exclude geometry column
        :param exclude_primary: Exclude primary key attributes should be excluded
        :param is_optional: Field argument is not required
        """
        super().__init__(name=name)
        self._data_types: NAMES = data_types
        self._element_name: str = element_name
        self._exists: bool = exists
        self._single: bool = single
        self._exclude_geometry: bool = exclude_geometry
        self._exclude_primary: bool = exclude_primary
        self._is_optional: bool = is_optional
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
            kwargs = self._get_arguments(func=func, args=args, kwargs=kwargs)
            obj = self._get_object(kwargs)
            element = self._get_element(kwargs)
            obj = self._find_field(obj, element=element)
            kwargs[self._name] = obj
            self._validate_type(obj)
            self._validate_data_type(obj)
            self._validate_exists(obj, element=element)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _get_element(self, kwargs: dict[str, Any]) -> Any:
        """
        Get Element
        """
        try:
            element = kwargs[self._element_name]
        except KeyError:
            return None
        return self._check_element(element)
    # End _get_element method

    def _find_field(self, obj: Any, element: ELEMENT) -> Any:
        """
        Find Field
        """
        if not element:
            if not self._single:
                return self._make_iterable(obj)
            return obj
        fields = validate_fields(
            element, fields=obj, exclude_geometry=self._exclude_geometry,
            exclude_primary=self._exclude_primary)
        if self._single:
            if fields:
                return fields[0]
            if self._is_optional:
                return None
            name = getattr(obj, NAME_ATTR, obj)
            raise ValueError(f'{name} not found in {element.name}')
        if not fields:
            names = [getattr(i, NAME_ATTR, i) for i in self._make_iterable(obj)]
            raise ValueError(f'{names} not found in {element.name}')
        obj = self._make_iterable(obj)
        if len(fields) != len(obj):
            found = {f.name.casefold() for f in fields}
            names = [getattr(i, NAME_ATTR, i) for i in obj
                     if getattr(i, NAME_ATTR, i).casefold() not in found]
            raise ValueError(f'{names} not found in {element.name}')
        return fields
    # End _find_field method

    def _validate_type(self, obj: Any) -> None:
        """
        Validate Type
        """
        if self._single:
            if self._is_optional and obj is None:
                return
            super()._validate_type(obj)
        else:
            for item in obj:
                super()._validate_type(item)
    # End _validate_type method

    def _validate_data_type(self, obj: Any) -> None:
        """
        Validate Data Type
        """
        if not (data_types := self._data_types):
            return
        if isinstance(data_types, str):
            data_types = data_types,
        aliases = set(data_types)
        for data_type in data_types:
            aliases.update(TYPE_ALIAS_LUT[data_type])
        aliases = tuple(a.casefold() for a in aliases)
        if self._single:
            if self._is_optional and obj is None:
                return
            if obj.data_type.casefold().startswith(aliases):
                return
        else:
            if all(i.data_type.casefold().startswith(aliases) for i in obj):
                return
        types = PADDED_PIPE.join(data_types)
        raise ValueError(f'{self._name} must have data type of {types}')
    # End _validate_data_type method

    def _validate_exists(self, obj: Any, element: ELEMENT) -> None:
        """
        Validate Exists
        """
        if not self._exists:
            return
        if not element:
            return
        source_names = {n.casefold() for n in element.field_names}
        if self._single:
            if self._is_optional and obj is None:
                return
            names = obj.name.casefold(),
        else:
            names = [item.name.casefold() for item in obj]
        if not (missing := [n for n in names if n not in source_names]):
            return
        else:  # pragma: no cover
            names = PADDED_PIPE.join(missing)
            raise ValueError(f'{names} not found in {element.name}')
    # End _validate_exists method
# End ValidateField class


class ValidateGeometryDimension(AbstractValidate):
    """
    Validate Geometry Dimension
    """
    def __init__(self, *names, same: bool = False, strict: bool = False) -> None:
        """
        Initialize the ValidateGeometryDimension class
        """
        super().__init__()
        self._names: NAMES = names
        self._same: bool = same
        self._strict: bool = strict
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
            self._validate_dimension(kwargs)
            self._validate_extended(kwargs)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _validate_dimension(self, kwargs: dict[str, Any]) -> None:
        """
        Validate Dimension
        """
        first, *others = self._names
        a = get_geometry_dimension(kwargs[first])
        for other in others:
            b = get_geometry_dimension(kwargs[other])
            check_dimension(a=a, name_a=first, b=b, name_b=other,
                            same=self._same)
    # End _validate_dimension method

    def _validate_extended(self, kwargs: dict[str, Any]) -> None:
        """
        Validate Extended Geometry Type (Z and M) when same dimension required
        """
        if not self._strict:
            return
        first, *others = self._names
        a = get_geometry_zm(kwargs[first])
        for other in others:
            b = get_geometry_zm(kwargs[other])
            check_zm(a=a, name_a=first, b=b, name_b=other)
    # End _validate_extended method
# End ValidateGeometryDimension class


if __name__ == '__main__':  # pragma: no cover
    pass
