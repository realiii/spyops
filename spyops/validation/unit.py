# -*- coding: utf-8 -*-
"""
Validation for Settings that might also be an input
"""


from functools import wraps
from typing import Any, Callable, TYPE_CHECKING

from bottleneck import nanmean
from numpy import array

from spyops.crs.unit import (
    DecimalDegrees, LinearUnit, degrees_to_meters,
    get_linear_unit_conversion_factor,
    get_unit_name, unit_factory, unit_from_number)
from spyops.crs.util import get_crs_from_source
from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.util import tolerance_scale_factor
from spyops.geometry.extent import extent_from_feature_class
from spyops.shared.constant import METRE
from spyops.shared.hint import UNIT, UNIT_TOLERANCE
from spyops.shared.keywords import METERS_ATTR, VALUE_ATTR
from spyops.validation.base import AbstractValidate


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from pyproj import CRS


class ValidateLinearUnit(AbstractValidate):
    """
    Validate Linear Unit
    """
    def __init__(self, name: str, *, feature_class_name: str,
                 as_number: bool = False, use_source_crs: bool = True) -> None:
        """
        Initialize the ValidateLinearUnit class

        :param name: Name of the argument to validate
        :param feature_class_name: Name of the feature class argument from
            which the spatial reference will be used
        :param as_number: If True, the unit will be returned as a number,
            otherwise as a Linear Unit
        :param use_source_crs: If True, the unit will be returned in the
            coordinate system of the feature class, otherwise in the output
            coordinate system
        """
        super().__init__()
        self._name: str = name
        self._feature_class_name: str = feature_class_name
        self._as_number: bool = as_number
        self._use_source_crs: bool = use_source_crs
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
            feature_class = kwargs[self._feature_class_name]
            obj = self._validate_value(obj, feature_class)
            self._set_object(obj, kwargs=kwargs)
            return func(**kwargs)
        # End wrapper function
        return wrapper
    # End call built-in

    def _get_object(self, kwargs: dict[str, Any]) -> UNIT_TOLERANCE:
        """
        Get Object from kwargs and optionally perform some checks
        """
        return kwargs[self._name]
    # End _get_object method

    def _set_object(self, obj: UNIT, kwargs: dict[str, Any]) -> None:
        """
        Set Object into the kwargs
        """
        kwargs[self._name] = obj
    # End _set_object method

    def _validate_value(self, obj: UNIT_TOLERANCE,
                        feature_class: 'FeatureClass') -> UNIT | float:
        """
        Validate Value
        """
        if not isinstance(obj, (LinearUnit, DecimalDegrees, float, int, str)):
            raise TypeError(f'Invalid type for {self._name}: {type(obj)}')
        unit = obj
        if isinstance(obj, (float, int)):
            if self._as_number:
                return abs(obj)
            unit = unit_from_number(
                obj, feature_class=feature_class, name=self._name)
        elif isinstance(obj, str):
            unit = unit_factory(obj)
        if not isinstance(unit, (LinearUnit, DecimalDegrees)):
            raise ValueError(
                f'{self._name} value {obj} could not be interpreted as a unit')
        unit.value = abs(unit.value or 0)
        if not self._as_number:
            return unit
        return self._convert_to_number(unit, feature_class)
    # End _validate_value method

    def _convert_to_number(self, unit: UNIT,
                           feature_class: 'FeatureClass') -> float:
        """
        Convert to Number, translating unit same units as the feature class
        or from output coordinate system
        """
        crs = get_crs_from_source(feature_class)
        output_crs = ANALYSIS_SETTINGS.output_coordinate_system
        if not self._use_source_crs and output_crs:
            crs = output_crs
        if isinstance(unit, DecimalDegrees):
            value = getattr(unit, VALUE_ATTR, 0)
            if crs.is_projected:
                (min_x, min_y,
                 max_x, max_y) = extent_from_feature_class(feature_class)
                coordinates = array([
                    [min_x, min_y], [min_x, max_y],
                    [max_x, min_y], [max_x, max_y]], dtype=float)
                value = nanmean(degrees_to_meters(
                    crs, coordinates=coordinates, value=value))
                value *= self._get_conversion_factor(crs)
        else:
            value = getattr(unit, METERS_ATTR, 0)
            if crs.is_projected:
                value *= self._get_conversion_factor(crs)
            else:
                value *= tolerance_scale_factor(feature_class)
        return value
    # End _convert_to_number method

    @staticmethod
    def _get_conversion_factor(crs: 'CRS') -> float:
        """
        Get Conversion Factor
        """
        if not (unit_name := get_unit_name(crs)):
            return 1.
        return get_linear_unit_conversion_factor(
            from_name=METRE, to_name=unit_name)
    # End _get_conversion_factor method
# End ValidateLinearUnit class


if __name__ == '__main__':  # pragma: no cover
    pass
