# -*- coding: utf-8 -*-
"""
Validation
"""

from spyops.validation.container import ValidateGeopackage
from spyops.validation.crs import ValidateSameCRS
from spyops.validation.element import (
    ValidateElement, ValidateFeatureClass, ValidateTable)
from spyops.validation.enumish import ValidateEnumeration, ValidateOutputType
from spyops.validation.field import ValidateField, ValidateGeometryDimension
from spyops.validation.result import ValidateResult
from spyops.validation.setting import ValidateXYTolerance


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


if __name__ == '__main__':  # pragma: no cover
    pass
