# -*- coding: utf-8 -*-
"""
Validation
"""


from abc import ABCMeta, abstractmethod
from functools import wraps
from inspect import signature
from pathlib import Path
from typing import Any, Callable, ClassVar
from warnings import warn

from fudgeo import FeatureClass, Field, GeoPackage, MemoryGeoPackage, Table
from fudgeo.constant import MEMORY

from geomio.crs.util import check_same_crs, get_crs_from_source
from geomio.shared.constant import NAME_ATTR, PADDED_PIPE, XY_TOLERANCE
from geomio.shared.exception import OperationsWarning
from geomio.shared.field import TYPE_ALIAS_LUT, validate_fields
from geomio.shared.hint import ELEMENT, NAMES


class AbstractValidate(metaclass=ABCMeta):
    """
    Abstract Validate
    """
    @abstractmethod
    def __call__(self, func: Callable) -> Callable:  # pragma: no cover
        """
        Make the class callable
        """
        pass
    # End call built-in

    @staticmethod
    def _get_arguments(func: Callable, args: tuple[Any, ...],
                       kwargs: dict[str, Any]) -> dict[str, Any]:
        """
        Get the arguments and values as kwargs
        """
        sig = signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        return bound.arguments
    # End _get_arguments method

    @staticmethod
    def _make_iterable(obj: Any) -> tuple | list:
        """
        Make iterable
        """
        if not isinstance(obj, (list, tuple)):
            return obj,
        return obj
    # End _make_iterable method
# End AbstractValidate class


class AbstractValidateType(AbstractValidate, metaclass=ABCMeta):
    """
    Abstract Validate Type
    """
    _types: ClassVar[tuple[type, ...]] = ()

    def __init__(self, name: str) -> None:
        """
        Initialize the AbstractValidateType class
        """
        super().__init__()
        self._name: str = name
    # End init built-in

    def _validate_type(self, obj: Any) -> None:
        """
        Validate Type
        """
        if isinstance(obj, self._types):
            return
        types = PADDED_PIPE.join(t.__name__ for t in self._types)
        raise TypeError(
            f'{self._name} must be {types}, got {type(obj).__name__}')
    # End _validate_type method
# End AbstractValidateType class


class AbstractValidateTypeExists(AbstractValidateType):
    """
    Abstract Validate Type and Object Exists
    """
    def __init__(self, name: str, exists: bool = True) -> None:
        """
        Initialize the ValidateContent class
        """
        super().__init__(name=name)
        self._exists: bool = exists
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
            obj = kwargs[self._name]
            self._validate_type(obj)
            if not self._validate_exists(obj):
                return func(**kwargs)
            self._validation(obj)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _validate_exists(self, obj: Any) -> bool:
        """
        Validate Exists
        """
        if not self._exists:
            return False
        if obj.exists:
            return True
        raise ValueError(f'{self._name} does not exist')
    # End _validate_exists method

    @abstractmethod
    def _validation(self, obj: Any) -> None:  # pragma: no cover
        """
        Validation
        """
        pass
    # End _validation method
# End AbstractValidateTypeExists class


class ValidateSameCRS(AbstractValidate):
    """
    Validate Same Coordinate Reference System
    """
    def __init__(self, *names) -> None:
        """
        Initialize the ValidateSameCRS class
        """
        super().__init__()
        self._names: NAMES = names
    # End init built-in

    def __call__(self, func: Callable) -> Callable:  # pragma: no cover
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
            first, *others = self._names
            crs = get_crs_from_source(kwargs[first])
            for other in others:
                check_same_crs(crs, get_crs_from_source(kwargs[other]))
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in
# End ValidateSameCRS class


class ValidateXYTolerance(AbstractValidate):
    """
    Validate XY Tolerance
    """
    def __init__(self, name: str = XY_TOLERANCE) -> None:
        """
        Initialize the ValidateXYTolerance class
        """
        super().__init__()
        self._name: str = name
    # End init built-in

    def __call__(self, func: Callable) -> Callable:  # pragma: no cover
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
            tolerance = kwargs[self._name]
            if not (tolerance is None or isinstance(tolerance, (int, float))):
                raise TypeError(
                    f'{self._name} must be a number or None, '
                    f'got {type(tolerance)}')
            # NOTE grid size of None --> use the highest precision of inputs
            #  grid size of 0 --> use double precision
            #  The default precision for geometries if not specified is 0
            #  which means double precision.  For our use cases at the moment
            #  the use of 0 and None are the same since we are not working with
            #  direct input of geometries but rather feature classes.
            if tolerance:
                tolerance = max(0, tolerance)
            kwargs[self._name] = tolerance
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in
# End ValidateXYTolerance class


class ValidateResult(AbstractValidate):
    """
    Validate Result
    """
    def __call__(self, func: Callable) -> Callable:  # pragma: no cover
        """
        Make the class callable
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Handler for the arguments and keyword arguments.
            """
            if not (result := func(*args, **kwargs)):
                return result
            for element in self._make_iterable(result):
                if isinstance(element, (FeatureClass, Table)):
                    _check_output_empty(element)
            return result
        # End wrapper function
        return wrapper
    # End call built-in
# End ValidateResult class


class ValidateGeopackage(AbstractValidateTypeExists):
    """
    Validate Geopackage
    """
    _types: ClassVar[tuple[type, ...]] = GeoPackage, MemoryGeoPackage

    def _validate_exists(self, obj: Any) -> bool:
        """
        Validate Exists
        """
        if not self._exists:
            return False
        if isinstance(obj.path, Path):
            if success := obj.path.is_file():
                return success
        if isinstance(obj.path, str):
            if success := (obj.path == MEMORY):
                return success
        raise ValueError(f'{self._name} does not exist')
    # End _validate_exists method

    def _validation(self, obj: Any) -> None:
        """
        Validation
        """
        pass
    # End _validation method
# End ValidateGeopackage class


class ValidateContent(AbstractValidateTypeExists):
    """
    Validate Element
    """
    def __init__(self, name: str, exists: bool = True,
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

    def __init__(self, name: str, exists: bool = True, has_content: bool = True,
                 geometry_types: NAMES = (),
                 has_z: bool = False, has_m: bool = False) -> None:
        """
        Initialize the ValidateFeatureClass class
        """
        super().__init__(name=name, exists=exists, has_content=has_content)
        self._geometry_types: NAMES = geometry_types
        self._has_z: bool = has_z
        self._has_m: bool = has_m
    # End init built-in

    def _validation(self, obj: Any) -> None:
        """
        Validation
        """
        super()._validation(obj)
        self._validate_geometry_types(obj)
        self._validate_zm(obj)
    # End _validation method

    def _validate_zm(self, obj: Any) -> None:
        """
        Validate Extended Geometry with Z and / or M
        """
        if self._has_z and not obj.has_z:
            raise ValueError(f'{self._name} does not have Z values')
        if self._has_m and not obj.has_m:
            raise ValueError(f'{self._name} does not have M values')
    # End _validate_zm method

    def _validate_geometry_types(self, obj: Any) -> None:
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


class ValidateField(AbstractValidateType):
    """
    Validate Field
    """
    _types: ClassVar[tuple[type, ...]] = Field,

    def __init__(self, name: str, data_types: NAMES = (),
                 element_name: str = '', exists: bool = True,
                 single: bool = False, exclude_geometry: bool = True,
                 exclude_primary: bool = True) -> None:
        """
        Initialize the ValidateField class

        :param name: Name of the argument to validate
        :param data_types: Data types to validate against
        :param element_name: Argument Name of the element to validate against
        :param exists: Ensure that the specified field exists
        :param single: Expect only a single field
        :param exclude_geometry: Exclude geometry column
        :param exclude_primary: Exclude primary key attributes should be excluded
        """
        super().__init__(name=name)
        self._data_types: NAMES = data_types
        self._element_name: str = element_name
        self._exists: bool = exists
        self._single: bool = single
        self._exclude_geometry: bool = exclude_geometry
        self._exclude_primary: bool = exclude_primary
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
            obj = kwargs[self._name]
            try:
                element = kwargs[self._element_name]
            except KeyError:
                element = None
            obj = self._find_field(obj, element=element)
            kwargs[self._name] = obj
            self._validate_type(obj)
            self._validate_data_type(obj)
            self._validate_exists(obj, element=element)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

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
            name = getattr(obj, NAME_ATTR, obj)
            raise ValueError(f'{name} not found in {element.name}')
        if not fields:
            names = [getattr(i, NAME_ATTR, i) for i in self._make_iterable(obj)]
            raise ValueError(f'{names} not found in {element.name}')
        return fields
    # End _find_field method

    def _validate_type(self, obj: Any) -> None:
        """
        Validate Type
        """
        if self._single:
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
            names = obj.name.casefold(),
        else:
            names = [item.name.casefold() for item in obj]
        if not (missing := [n for n in names if n not in source_names]):
            return
        names = PADDED_PIPE.join(missing)
        raise ValueError(f'{names} not found in {element.name}')
    # End _validate_exists method
# End ValidateField class


# NOTE aliases, decorators look better as snake case
validate_element = ValidateElement
validate_feature_class = ValidateFeatureClass
validate_field = ValidateField
validate_geopackage = ValidateGeopackage
validate_result = ValidateResult
validate_same_crs = ValidateSameCRS
validate_table = ValidateTable
validate_xy_tolerance = ValidateXYTolerance


def _check_output_empty(element: ELEMENT) -> ELEMENT:
    """
    Check element for content, warn if empty
    """
    if element.is_empty:
        warn(f'{element.name} created but contains no rows', OperationsWarning)
    return element
# End _check_output_empty function


if __name__ == '__main__':  # pragma: no cover
    pass
