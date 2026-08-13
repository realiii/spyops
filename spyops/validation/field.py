# -*- coding: utf-8 -*-
"""
Validation for Fields
"""


from functools import wraps
from typing import Any, Callable, ClassVar

from fudgeo import Field
from fudgeo.enumeration import FieldType

from spyops.crs.unit import (
    DecimalDegrees, LinearUnit, unit_factory, unit_from_number)
from spyops.geometry.validate import (
    check_dimension, check_zm, get_geometry_dimension, get_geometry_zm)
from spyops.shared.constant import PADDED_PIPE
from spyops.shared.enumeration import PlacementOption
from spyops.shared.keywords import NAME_ATTR
from spyops.shared.field import (
    COMPATIBILITY_LUT, TEXT_AND_NUMBERS, TYPE_ALIAS_LUT, simplify_type,
    validate_fields)
from spyops.shared.hint import ELEMENT, NAMES
from spyops.shared.sort import AbstractSortField
from spyops.shared.stats import AbstractStatisticField
from spyops.shared.util import safe_float
from spyops.validation.base import AbstractValidate, AbstractValidateType


class ValidateField(AbstractValidateType):
    """
    Validate Field
    """
    _types: ClassVar[tuple[type, ...]] = Field,

    def __init__(self, name: str, *, data_types: NAMES | str = (),
                 element_name: str = '', exists: bool = True,
                 single: bool = False, exclude_geometry: bool = True,
                 exclude_primary: bool = True,
                 is_optional: bool = False) -> None:
        """
        Initialize the ValidateField class

        :param name: Name of the argument to validate
        :param data_types: Data types to validate against
        :param element_name: Argument Name of the element to validate against
        :param exists: Ensure that the specified field exists
        :param single: Expect only a single field
        :param exclude_geometry: Exclude geometry column
        :param exclude_primary: Exclude primary key attribute
        :param is_optional: Field argument is not required
        """
        super().__init__(name=name)
        self._data_types: NAMES | str = data_types
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
            self._set_object(obj, kwargs=kwargs)
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
            if self._is_optional:
                return []
            names = [getattr(i, NAME_ATTR, i) for i in self._make_iterable(obj)]
            raise ValueError(f'{names} not found in {element.name}')
        obj = self._make_iterable(obj)
        if len(fields) != len(obj):
            found = {f.name.casefold() for f in fields}
            # noinspection PyUnresolvedReferences
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
            if self._check_data_type([obj], aliases):
                return
        else:
            if self._check_data_type(obj, aliases):
                return
        types = PADDED_PIPE.join(data_types)
        raise ValueError(f'{self._name} must have data type of {types}')
    # End _validate_data_type method
    
    @staticmethod
    def _check_data_type(fields: list[Field],
                         aliases: tuple[str, ...]) -> bool:
        """
        Check Data Type
        """
        dt = FieldType.datetime.casefold()
        has_datetime = dt in aliases
        has_date = FieldType.date.casefold() in aliases
        valid_types = [f.data_type.casefold() for f in fields
                       if f.data_type.casefold().startswith(aliases)]
        if has_date and not has_datetime:
            valid_types = [t for t in valid_types if t != dt]
        return bool(valid_types)
    # End _check_data_type method

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


class ValidateDistance(ValidateField):
    """
    Validate Distance
    """
    _types: ClassVar[tuple[type, ...]] = (
        LinearUnit, DecimalDegrees, Field, str, float, int)

    def __init__(self, name: str, *, element_name: str) -> None:
        """
        Initialize the ValidateDistance class

        :param name: Name of the argument to validate
        :param element_name: Argument Name of the element to validate against
        """
        # noinspection PyArgumentEqualDefault
        super().__init__(
            name=name, data_types=TEXT_AND_NUMBERS, element_name=element_name,
            exists=True, single=True, exclude_geometry=True,
            exclude_primary=False, is_optional=False)
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
            element = self._get_element(kwargs)
            if isinstance(obj, (float, int)):
                obj = unit_from_number(
                    obj, feature_class=element, name=self._name)
            if isinstance(obj, str):
                if unit := unit_factory(obj):
                    obj = unit
            if isinstance(obj, (Field, str)):
                obj = self._find_field(obj, element=element)
                self._validate_data_type(obj)
                self._validate_exists(obj, element=element)
            self._set_object(obj, kwargs=kwargs)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in
# End ValidateDistance class


class ValidatePlacement(ValidateDistance):
    """
    Validate Placement
    """
    def __init__(self, name: str, *, element_name: str, enum_name: str) -> None:
        """
        Initialize the ValidatePlacement class

        :param name: Name of the argument to validate
        :param element_name: Argument Name of the element to validate against
        :param enum_name: Argument Name of the enum to validate against
        """
        super().__init__(name=name, element_name=element_name)
        self._enum_name: str = enum_name
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
            element = self._get_element(kwargs)
            enum_value = kwargs[self._enum_name]
            if enum_value == PlacementOption.PERCENTAGE:
                percent = safe_float(obj)
                self._validate_percentage(percent, obj)
                obj = percent
            elif enum_value == PlacementOption.DISTANCE:
                if isinstance(obj, (float, int)):
                    obj = unit_from_number(
                        obj, feature_class=element, name=self._name)
                elif isinstance(obj, str):
                    obj = unit_factory(obj)
            else:
                if not isinstance(obj, (Field, str)):
                    raise TypeError(
                        f'{self._name} must be a valid field or string field '
                        f'name, got {type(obj)}')
                obj = self._find_field(obj, element=element)
                self._validate_data_type(obj)
                self._validate_exists(obj, element=element)
            if not obj:
                raise TypeError(
                    f'Unable to interpret {self._get_object(kwargs)} '
                    f'for {self._name}')
            self._set_object(obj, kwargs=kwargs)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _validate_percentage(self, percentage: Any, obj: Any) -> None:
        """
        Validate Percentage
        """
        stub = f'{self._name} must be a valid percentage'
        if not isinstance(percentage, (float, int)):
            raise TypeError(f'{stub}, got {type(obj)}')
        if percentage < 0 or percentage > 100:
            raise ValueError(f'{stub} between 0 and 100, got {percentage}')
    # End _validate_percentage method
# End ValidatePlacement class


class ValidateStatisticField(ValidateField):
    """
    Validate Statistic Field
    """
    _types: ClassVar[tuple[type, ...]] = AbstractStatisticField,

    def __init__(self, name: str, *, element_name: str,
                 is_optional: bool = True) -> None:
        """
        Initialize the ValidateStatisticField class

        :param name: Name of the argument to validate
        :param element_name: Argument Name of the element to validate against
        :param is_optional: Field argument is not required
        """
        # noinspection PyArgumentEqualDefault
        super().__init__(name=name, element_name=element_name, exists=True,
                         single=False, exclude_geometry=True,
                         exclude_primary=False, is_optional=is_optional)
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
            if not (obj := [o for o in self._make_iterable(obj) if o]):
                self._set_object(obj, kwargs=kwargs)
                return func(**kwargs)
            self._validate_type(obj)
            element = self._get_element(kwargs)
            obj = self._find_field(obj, element=element)
            self._set_object(obj, kwargs=kwargs)
            self._validate_data_type(obj)
            self._validate_exists(obj, element=element)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _find_field(self, obj: Any, element: ELEMENT) -> Any:
        """
        Find Fields and set them onto the objects
        """
        obj = self._make_iterable(obj)
        fields = {}
        for o in obj:
            field = o.field
            if not isinstance(field, (Field, str)):
                continue
            # noinspection PyUnresolvedReferences
            fields[getattr(field, NAME_ATTR, field).casefold()] = field
        fields = super()._find_field(list(fields.values()), element=element)
        fields = {field.name.casefold(): field for field in fields}
        for o in obj:
            field = o.field
            # noinspection PyUnresolvedReferences
            o.field = fields.get(getattr(field, NAME_ATTR, field).casefold())
        return [o for o in obj if o.field]
    # End _find_field method

    def _validate_data_type(self, obj: Any) -> None:
        """
        Validate Data Type
        """
        for o in obj:
            o.validate()
    # End _validate_data_type method

    def _validate_exists(self, obj: Any, element: ELEMENT) -> None:
        """
        Validate Exists
        """
        obj = [o.field for o in obj if o.field]
        super()._validate_exists(obj, element=element)
    # End _validate_exists method
# End ValidateStatisticField class


class ValidateSortField(ValidateStatisticField):
    """
    Validate Sort Field
    """
    _types: ClassVar[tuple[type, ...]] = AbstractSortField,
# End ValidateSortField class


class ValidateGeometryDimension(AbstractValidate):
    """
    Validate Geometry Dimension
    """
    def __init__(self, *names, same: bool = False,
                 strict: bool = False) -> None:
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


class ValidateCompatibleFields(AbstractValidate):
    """
    Validate Compatible Fields
    """
    def __init__(self, from_name: str, to_name: str) -> None:
        """
        Initialize the ValidateCompatibleFields class
        """
        super().__init__()
        self._from_name: str = from_name
        self._to_name: str = to_name
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
            self._validate_compatibility(kwargs)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _validate_compatibility(self, kwargs: dict[str, Any]) -> None:
        """
        Validate Compatibility
        """
        from_field = kwargs[self._from_name]
        to_field = kwargs[self._to_name]
        if from_field.name == to_field.name:
            raise ValueError(
                f'{self._from_name} and {self._to_name} cannot be the '
                f'same field')
        from_type = simplify_type(from_field)
        to_type = simplify_type(to_field)
        compatible_types = COMPATIBILITY_LUT.get(from_type, ())
        if to_type not in compatible_types:
            raise TypeError(
                f'{self._from_name} and {self._to_name} must be of the same or '
                f'compatible data type')
    # End _validate_compatibility method
# End ValidateCompatibleFields class


if __name__ == '__main__':  # pragma: no cover
    pass
