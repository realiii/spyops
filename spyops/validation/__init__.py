# -*- coding: utf-8 -*-
"""
Validation
"""


from functools import partial

from spyops.shared.constant import OPERATOR, SOURCE, TARGET
from spyops.validation.container import ValidateGeopackage
from spyops.validation.crs import ValidateCRS
from spyops.validation.element import (
    ValidateElement, ValidateElements, ValidateFeatureClass,
    ValidateOverwriteInput, ValidateTable)
from spyops.validation.enumish import (
    ValidateIntFlagEnumeration, ValidateStrEnumeration,
    ValidateGeometryAttribute, ValidateOutputType)
from spyops.validation.field import ValidateField, ValidateGeometryDimension
from spyops.validation.result import ValidateResult
from spyops.validation.setting import ValidateXYTolerance


# NOTE aliases, decorators look better as snake case
validate_crs = ValidateCRS
validate_element = ValidateElement
validate_elements = ValidateElements
validate_str_enumeration = ValidateStrEnumeration
validate_int_flag_enumeration = ValidateIntFlagEnumeration
validate_feature_class = ValidateFeatureClass
validate_field = ValidateField
validate_geometry_attribute = ValidateGeometryAttribute
validate_geometry_dimension = ValidateGeometryDimension
validate_geopackage = ValidateGeopackage
validate_output_type = ValidateOutputType
validate_overwrite_input = ValidateOverwriteInput
validate_result = ValidateResult
validate_table = ValidateTable
validate_xy_tolerance = ValidateXYTolerance

# NOTE commonly used configurations
validate_source_feature_class = partial(validate_feature_class, name=SOURCE)
validate_operator_feature_class = partial(validate_feature_class, name=OPERATOR)
validate_target_element = partial(
    validate_element, name=TARGET, exists=False, is_output=True)
validate_target_feature_class = partial(
    validate_feature_class, name=TARGET, exists=False, is_output=True)
validate_target_table = partial(
    validate_table, name=TARGET, exists=False, is_output=True)
validate_overwrite_source = partial(
    validate_overwrite_input, TARGET, SOURCE)

if __name__ == '__main__':  # pragma: no cover
    pass
