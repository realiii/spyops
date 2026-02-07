# -*- coding: utf-8 -*-
"""
Validation
"""


from functools import partial

from spyops.shared.constant import TARGET
from spyops.validation.container import ValidateGeopackage
from spyops.validation.crs import ValidateCRS
from spyops.validation.element import (
    ValidateElement, ValidateFeatureClass, ValidateOverwriteInput,
    ValidateTable)
from spyops.validation.enumish import ValidateEnumeration, ValidateOutputType
from spyops.validation.field import ValidateField, ValidateGeometryDimension
from spyops.validation.result import ValidateResult
from spyops.validation.setting import ValidateXYTolerance


# NOTE aliases, decorators look better as snake case
validate_crs = ValidateCRS
validate_element = ValidateElement
validate_enumeration = ValidateEnumeration
validate_feature_class = ValidateFeatureClass
validate_field = ValidateField
validate_geometry_dimension = ValidateGeometryDimension
validate_geopackage = ValidateGeopackage
validate_output_type = ValidateOutputType
validate_overwrite_input = ValidateOverwriteInput
validate_result = ValidateResult
validate_table = ValidateTable
validate_xy_tolerance = ValidateXYTolerance


if __name__ == '__main__':  # pragma: no cover
    pass
