# -*- coding: utf-8 -*-
"""
To GeoPackage
"""


from spyops.environment import OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.query.conversion.geopackage import QueryTableToGeoPackage
from spyops.shared.hint import ELEMENT, ELEMENTS, GPKG
from spyops.shared.keywords import SOURCE
from spyops.validation import (
    validate_elements, validate_geopackage, validate_result)


__all__ = ['table_to_geopackage']


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


if __name__ == '__main__':  # pragma: no cover
    pass
