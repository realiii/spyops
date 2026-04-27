# -*- coding: utf-8 -*-
"""
Validation
"""


from functools import partial

from spyops.shared.keywords import OPERATOR, SOURCE, TARGET
from spyops.shared.field import NUMBERS
from spyops.validation.container import ValidateGeopackage, ValidateValues
from spyops.validation.crs import (
    ValidateSupportedCRS,
    ValidateCoordinateSystem, ValidateTransform)
from spyops.validation.element import (
    ValidateElement, ValidateElements, ValidateFeatureClass,
    ValidateOverwriteInput, ValidateTable)
from spyops.validation.enumish import (
    ValidateDissolveOption, ValidateGeometryGroupOption, ValidateGroupOption,
    ValidateIntFlagEnumeration,
    ValidateSideOption, ValidateStrEnumeration, ValidateGeometryAttribute,
    ValidateOutputType)
from spyops.validation.field import (
    ValidateCompatibleFields, ValidateDistance, ValidateField,
    ValidateGeometryDimension, ValidateStatisticField)
from spyops.validation.range import ValidateRange
from spyops.validation.result import ValidateResult
from spyops.validation.setting import ValidateXYTolerance


# NOTE aliases, decorators look better as snake case
validate_compatible_fields = ValidateCompatibleFields
validate_coordinate_system = ValidateCoordinateSystem
validate_dissolve_option = ValidateDissolveOption
validate_distance = ValidateDistance
validate_element = ValidateElement
validate_elements = ValidateElements
validate_feature_class = ValidateFeatureClass
validate_field = ValidateField
validate_geometry_attribute = ValidateGeometryAttribute
validate_geometry_dimension = ValidateGeometryDimension
validate_geometry_group_option = ValidateGeometryGroupOption
validate_geopackage = ValidateGeopackage
validate_group_option = ValidateGroupOption
validate_int_flag_enumeration = ValidateIntFlagEnumeration
validate_output_type = ValidateOutputType
validate_overwrite_input = ValidateOverwriteInput
validate_range = ValidateRange
validate_result = ValidateResult
validate_side_option = ValidateSideOption
validate_statistic_field = ValidateStatisticField
validate_str_enumeration = ValidateStrEnumeration
validate_supported_crs = ValidateSupportedCRS
validate_table = ValidateTable
validate_transform = ValidateTransform
validate_values = ValidateValues
validate_xy_tolerance = ValidateXYTolerance


# NOTE commonly used configurations
validate_operator_feature_class = partial(validate_feature_class, name=OPERATOR)
validate_overwrite_source = partial(validate_overwrite_input, TARGET, SOURCE)
validate_source_feature_class = partial(validate_feature_class, name=SOURCE)
validate_source_element = partial(validate_element, name=SOURCE)
validate_source_numeric_field = partial(
    validate_field, single=True, element_name=SOURCE, data_types=NUMBERS)
validate_target_element = partial(
    validate_element, name=TARGET, exists=False, is_output=True)
validate_target_feature_class = partial(
    validate_feature_class, name=TARGET, exists=False, is_output=True)
validate_target_table = partial(
    validate_table, name=TARGET, exists=False, is_output=True)


if __name__ == '__main__':  # pragma: no cover
    pass
