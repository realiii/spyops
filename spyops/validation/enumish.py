# -*- coding: utf-8 -*-
"""
Validation Enumeration-esque Values
"""


from enum import StrEnum
from functools import wraps
from typing import Any, Callable, TYPE_CHECKING, Type

from fudgeo.enumeration import ShapeType

from spyops.geometry.validate import get_geometry_dimension
from spyops.shared.constant import GEOMETRY_ATTRIBUTE, SOURCE
from spyops.shared.enumeration import GeometryAttribute, OutputTypeOption
from spyops.shared.exception import GeometryDimensionError
from spyops.shared.util import check_enumeration
from spyops.validation.base import (
    AbstractValidate, AbstractValidateArgument, AbstractValidateType)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


class ValidateEnumeration(AbstractValidateArgument):
    """
    Validate Item is of the expected Enumeration
    """
    def __init__(self, name: str, enum: Type[StrEnum]) -> None:
        """
        Initialize the ValidateEnumeration class

        :param name: Name of the argument to validate
        :param enum: Enumeration to validate against
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
                raise GeometryDimensionError(
                    f'{self._name} features class must be a '
                    f'{ShapeType.linestring} or {ShapeType.polygon} '
                    f'shape type for Output Type "{OutputTypeOption.LINE}"')
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in
# End ValidateOutputType class


class ValidateGeometryAttribute(AbstractValidateType):
    """
    Validate Geometry Attribute is valid with the Feature Class
    """
    def __init__(self) -> None:
        """
        Initialize the ValidateGeometryAttribute class
        """
        super().__init__(SOURCE)
        self._enum_name: str = GEOMETRY_ATTRIBUTE
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
            source = self._get_object(kwargs)
            attribute = check_enumeration(
                kwargs[self._enum_name], enum=GeometryAttribute)
            self._validate_value(source, attribute)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _get_object(self, kwargs: dict[str, Any]) -> 'FeatureClass':
        """
        Get Object from kwargs and optionally perform some checks
        """
        obj = super()._get_object(kwargs)
        return self._check_element(obj)
    # End _get_object method

    def _validate_value(self, source: 'FeatureClass',
                        attribute: GeometryAttribute) -> None:
        """
        Validate Value
        """
        shape_type = source.shape_type
        has_z, has_m = source.has_z, source.has_m
        if shape_type in (ShapeType.point, ShapeType.multi_point):
            if source.is_multi_part:
                is_valid = self._validate_multi_points(
                    attribute, has_z=has_z, has_m=has_m)
            else:
                is_valid = self._validate_points(
                    attribute, has_z=has_z, has_m=has_m)
        elif shape_type in (ShapeType.linestring,
                            ShapeType.multi_linestring):
            is_valid = self._validate_lines(attribute, has_z=has_z, has_m=has_m)
        else:
            is_valid = self._validate_polygons(
                attribute, has_z=has_z, has_m=has_m)
        if not is_valid:
            raise ValueError(
                f'Geometry attribute "{attribute}" is not valid for '
                f'{source.geometry_type} geometry type.')
    # End _validate_value method

    @staticmethod
    def _validate_points(attribute: GeometryAttribute, *,
                         has_z: bool, has_m: bool) -> bool:
        """
        Validate Points and MultiPoints
        """
        valid = GeometryAttribute.POINT_X, GeometryAttribute.POINT_Y
        if has_z:
            valid = *valid, GeometryAttribute.POINT_Z
        if has_m:
            valid = *valid, GeometryAttribute.POINT_M
        return attribute in valid
    # End _validate_points method

    def _validate_multi_points(self, attribute: GeometryAttribute, *,
                               has_z: bool, has_m: bool) -> bool:
        """
        Validate Multi Points
        """
        valid = self._non_point_valid(has_z=has_z, has_m=has_m)
        return attribute in valid
    # End _validate_multi_points method

    @staticmethod
    def _non_point_valid(*, has_z: bool, has_m: bool) \
            -> tuple[GeometryAttribute, ...]:
        """
        Non Point Valid Geometry Attributes
        """
        valid = (
            GeometryAttribute.CENTROID_X,
            GeometryAttribute.CENTROID_Y,
            GeometryAttribute.EXTENT_MAX_X,
            GeometryAttribute.EXTENT_MAX_Y,
            GeometryAttribute.EXTENT_MIN_X,
            GeometryAttribute.EXTENT_MIN_Y,
            GeometryAttribute.PART_COUNT,
            GeometryAttribute.POINT_COUNT,
        )
        if has_z:
            valid = *valid, *(
                GeometryAttribute.CENTROID_Z, GeometryAttribute.EXTENT_MAX_Z,
                GeometryAttribute.EXTENT_MIN_Z)
        if has_m:
            valid = *valid, GeometryAttribute.CENTROID_M
        return valid
    # End _validate_multi_points method

    @staticmethod
    def _inside_valid(*, has_z: bool, has_m: bool) \
            -> tuple[GeometryAttribute, ...]:
        """
        Inside Attributes for Lines and Polygons
        """
        valid = (GeometryAttribute.INSIDE_X, GeometryAttribute.INSIDE_Y)
        if has_z:
            valid = *valid, GeometryAttribute.INSIDE_Z
        if has_m:
            valid = *valid, GeometryAttribute.INSIDE_M
        return valid
    # End _inside_valid method

    def _validate_lines(self, attribute: GeometryAttribute, *,
                        has_z: bool, has_m: bool) -> bool:
        """
        Validate LineString and MultLineString
        """
        valid = (
            GeometryAttribute.LENGTH,
            GeometryAttribute.LENGTH_GEODESIC,
            GeometryAttribute.LINE_BEARING,
            GeometryAttribute.LINE_END_X,
            GeometryAttribute.LINE_END_Y,
            GeometryAttribute.LINE_START_X,
            GeometryAttribute.LINE_START_Y,
        )
        valid = (*valid, *self._non_point_valid(has_z=has_z, has_m=has_m),
                 *self._inside_valid(has_z=has_z, has_m=has_m))
        if has_z:
            valid = *valid, *(
                GeometryAttribute.LINE_END_Z, GeometryAttribute.LINE_START_Z)
        if has_m:
            valid = *valid, *(
                GeometryAttribute.LINE_END_M, GeometryAttribute.LINE_START_M)
        return attribute in valid
    # End _validate_lines method

    def _validate_polygons(self, attribute: GeometryAttribute, *,
                           has_z: bool, has_m: bool) -> bool:
        """
        Validate Polygons and MultiPolygons
        """
        valid = (
            GeometryAttribute.AREA,
            GeometryAttribute.AREA_GEODESIC,
            GeometryAttribute.PERIMETER,
            GeometryAttribute.PERIMETER_GEODESIC,
            GeometryAttribute.HOLE_COUNT,
        )
        valid = (*valid, *self._non_point_valid(has_z=has_z, has_m=has_m),
                 *self._inside_valid(has_z=has_z, has_m=has_m))
        return attribute in valid
    # End _validate_polygons method
# End ValidateGeometryAttribute class


if __name__ == '__main__':  # pragma: no cover
    pass
