# -*- coding: utf-8 -*-
"""
To GeoPackage
"""


from fudgeo import FeatureClass

from spyops.environment import OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.query.conversion.geopackage import (
    QueryFeatureClassToGeoPackage, QueryTableToGeoPackage)
from spyops.shared.hint import ELEMENT, ELEMENTS, FEATURE_CLASSES, GPKG
from spyops.shared.keywords import SOURCE
from spyops.validation import (
    validate_elements, validate_feature_classes, validate_geopackage,
    validate_result)


__all__ = ['table_to_geopackage', 'feature_class_to_geopackage']


@validate_result()
@validate_elements(SOURCE, has_content=False)
@validate_geopackage()
def table_to_geopackage(source: ELEMENTS, geopackage: GPKG) -> list[ELEMENT]:
    """
    Table to GeoPackage

    Copy one or more tables into a GeoPackage.
    """
    results = []
    with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, None),
          Swap(Setting.GEOGRAPHIC_TRANSFORMATIONS, []),
          Swap(Setting.EXTENT, None), Swap(Setting.Z_VALUE, None),
          Swap(Setting.OUTPUT_M_OPTION, OutputMOption.SAME),
          Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.SAME)):
        for element in source:
            query = QueryTableToGeoPackage(element, geopackage=geopackage)
            results.append(query.copy())
    return results
# End table_to_geopackage function


@validate_result()
@validate_feature_classes(SOURCE, has_content=False)
@validate_geopackage()
def feature_class_to_geopackage(source: FEATURE_CLASSES,
                                geopackage: GPKG) -> list['FeatureClass']:
    """
    Feature Class to GeoPackage

    Copy one or more feature classes into a GeoPackage.
    """
    results = []
    for element in source:
        query = QueryFeatureClassToGeoPackage(element, geopackage=geopackage)
        results.append(query.copy())
    return results
# End feature_class_to_geopackage function


if __name__ == '__main__':  # pragma: no cover
    pass
