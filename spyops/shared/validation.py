# -*- coding: utf-8 -*-
"""
Validation
"""


from abc import ABCMeta, abstractmethod
from enum import StrEnum
from functools import wraps
from inspect import signature
from pathlib import Path
from typing import Any, Callable, ClassVar, Type
from warnings import warn

from fudgeo import FeatureClass, Field, GeoPackage, MemoryGeoPackage, Table
from fudgeo.constant import MEMORY
from fudgeo.enumeration import GeometryType

from spyops.crs.util import check_same_crs, get_crs_from_source
from spyops.geometry.extent import set_extent
from spyops.geometry.validate import (
    check_dimension, check_zm, get_geometry_dimension, get_geometry_zm)
from spyops.shared.constant import GEOPACKAGE, NAME_ATTR, PADDED_PIPE
from spyops.shared.enumeration import OutputTypeOption
from spyops.environment.enumeration import Setting
from spyops.shared.exception import OperationsError, OperationsWarning
from spyops.shared.field import TYPE_ALIAS_LUT, validate_fields
from spyops.shared.hint import ELEMENT, GPKG, NAMES, XY_TOL
from spyops.environment import ANALYSIS_SETTINGS
from spyops.shared.util import check_enumeration, safe_float


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
        else:  # pragma: no cover
            return obj
    # End _make_iterable method
# End AbstractValidate class


class AbstractValidateArgument(AbstractValidate, metaclass=ABCMeta):
    """
    Abstract Validation on an Argument by Name
    """
    def __init__(self, name: str) -> None:
        """
        Initialize the AbstractValidateArgument class
        """
        super().__init__()
        self._name: str = name
    # End init built-in

    def _get_object(self, kwargs: dict[str, Any]) -> Any:
        """
        Get Object from kwargs and optionally perform some checks
        """
        return kwargs[self._name]
    # End _get_object method

    def _set_object(self, obj: Any, kwargs: dict[str, Any]) -> None:
        """
        Set Object into the kwargs
        """
        kwargs[self._name] = obj
    # End _set_object method
# End AbstractValidateArgument class


class AbstractValidateType(AbstractValidateArgument, metaclass=ABCMeta):
    """
    Abstract Validate Type
    """
    _types: ClassVar[tuple[type, ...]] = ()

    @staticmethod
    def _check_element(obj: Any) -> Any:
        """
        Check Element
        """
        if not isinstance(obj, str):
            return obj
        if not (settings_gpkg := ANALYSIS_SETTINGS.current_workspace):
            return obj
        return settings_gpkg[obj]
    # End _check_element method

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
    def __init__(self, name: str, *, exists: bool = True) -> None:
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
            kwargs = self._get_arguments(func=func, args=args, kwargs=kwargs)
            obj = self._get_object(kwargs)
            self._validate_type(obj)
            self._set_object(obj, kwargs=kwargs)
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


class ValidateEnumeration(AbstractValidateArgument):
    """
    Validate Item is of the expected Enumeration
    """
    def __init__(self, name: str, enum: Type[StrEnum]) -> None:
        """
        Initialize the ValidateEnumeration class
        """
        super().__init__(name)
        self._enum: Type[StrEnum] = enum
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
            obj = self._get_object(kwargs)
            obj = self._validate_value(obj)
            self._set_object(obj, kwargs=kwargs)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _validate_value(self, obj: Any) -> Any:
        """
        Validate Value
        """
        return check_enumeration(obj, enum=self._enum)
    # End _validate_value method
# End ValidateEnumeration class


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
            first, *others = self._names
            crs = get_crs_from_source(kwargs[first])
            for other in others:
                check_same_crs(crs, get_crs_from_source(kwargs[other]))
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in
# End ValidateSameCRS class


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


class ValidateOutputType(AbstractValidate):
    """
    Validate Output Type
    """
    def __init__(self, enum_name: str, name: str) -> None:
        """
        Initialize the ValidateOutputType class
        """
        super().__init__()
        self._enum_name: str = enum_name
        self._name: str = name
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
            if kwargs[self._enum_name] != OutputTypeOption.LINE:
                return func(**kwargs)
            if not get_geometry_dimension(kwargs[self._name]):
                raise OperationsError(
                    f'{self._name} features class must be a '
                    f'{GeometryType.linestring} or {GeometryType.polygon} '
                    f'shape type for Output Type "{OutputTypeOption.LINE}"')
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in
# End ValidateOutputType class


class ValidateXYTolerance(AbstractValidate):
    """
    Validate XY Tolerance
    """
    def __init__(self, name: str = str(Setting.XY_TOLERANCE)) -> None:
        """
        Initialize the ValidateXYTolerance class
        """
        super().__init__()
        self._name: str = name
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
            tolerance = self._get_object(kwargs)
            tolerance = self._validate_value(tolerance)
            self._set_object(tolerance, kwargs=kwargs)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _get_object(self, kwargs: dict[str, Any]) -> XY_TOL:
        """
        Get Object from kwargs and optionally perform some checks
        """
        return safe_float(kwargs[self._name])
    # End _get_object method

    def _set_object(self, obj: XY_TOL, kwargs: dict[str, Any]) -> None:
        """
        Set Object into the kwargs
        """
        kwargs[self._name] = obj
    # End _set_object method

    @staticmethod
    def _validate_value(function_xy: XY_TOL) -> XY_TOL:
        """
        Validate Value and also compare with XY Setting

        When working with shapely the grid size parameter:
        * None --> use the highest precision of inputs
        * 0 --> use double precision

        The default precision for geometries if not specified is 0,
        which means double precision.  For our use cases at the moment
        the use of 0 and None are the same since we are not working with
        direct input of geometries but rather feature classes.

        When a value provided is less than 0, it is treated as 0.
        """
        settings_xy = ANALYSIS_SETTINGS.xy_tolerance
        has_input = function_xy is not None
        has_settings = settings_xy is not None
        if not has_settings:
            if not has_input:
                return function_xy
            tolerance = function_xy
        else:
            if has_input:
                tolerance = function_xy
            else:
                tolerance = settings_xy
        return max(0, tolerance)
    # End _validate_value method
# End ValidateXYTolerance class


class ValidateResult(AbstractValidate):
    """
    Validate Result
    """
    def __call__(self, func: Callable) -> Callable:
        """
        Make the class callable
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Handler for the arguments and keyword arguments.
            """
            if not (result := func(*args, **kwargs)):  # pragma: no cover
                return result
            for element in self._make_iterable(result):
                if isinstance(element, Table):
                    _check_output(element)
                if isinstance(element, FeatureClass):
                    _check_output(element)
                    set_extent(element)
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

    def __init__(self, name: str = GEOPACKAGE, *, exists: bool = True) -> None:
        """
        Initialize the ValidateGeopackage class
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


class ValidateField(AbstractValidateType):
    """
    Validate Field
    """
    _types: ClassVar[tuple[type, ...]] = Field,

    def __init__(self, name: str, *, data_types: NAMES = (),
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
        else:  # pragma: no cover
            names = PADDED_PIPE.join(missing)
            raise ValueError(f'{names} not found in {element.name}')
    # End _validate_exists method
# End ValidateField class


# NOTE aliases, decorators look better as snake case
validate_element = ValidateElement
validate_enumeration = ValidateEnumeration
validate_feature_class = ValidateFeatureClass
validate_field = ValidateField
validate_geometry_dimension = ValidateGeometryDimension
validate_geopackage = ValidateGeopackage
validate_output_type = ValidateOutputType
validate_result = ValidateResult
validate_same_crs = ValidateSameCRS
validate_table = ValidateTable
validate_xy_tolerance = ValidateXYTolerance


def _check_output(element: ELEMENT) -> ELEMENT:
    """
    Check element for existence and content, warn if not present or empty
    """
    if not element:
        warn(f'{element.name} was not created', OperationsWarning)
        return element
    if not len(element):
        warn(f'{element.name} created but contains no rows', OperationsWarning)
        return element
    return element
# End _check_output function


if __name__ == '__main__':  # pragma: no cover
    pass
