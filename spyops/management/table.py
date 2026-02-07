# -*- coding: utf-8 -*-
"""
Data Management for Tables
"""


from typing import TYPE_CHECKING

from spyops.environment import ANALYSIS_SETTINGS
from spyops.shared.constant import SOURCE
from spyops.shared.hint import ELEMENT, FIELDS, GPKG
from spyops.shared.util import make_valid_name
from spyops.validation import validate_element, validate_geopackage

if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Table


@validate_element(SOURCE, has_content=False)
def get_count(source: ELEMENT) -> int:
    """
    Get Count

    Number of rows in a table or feature class
    """
    return len(source)
# End get_count function


@validate_geopackage()
def create_table(geopackage: GPKG, name: str, *, fields: FIELDS = (),
                 description: str = '') -> 'Table':
    """
    Create Table

    Create a new table in a geopackage with specified fields
    """
    overwrite = ANALYSIS_SETTINGS.overwrite
    name = make_valid_name(name, prefix='tbl')
    return geopackage.create_table(
        name, fields=fields, description=description, overwrite=overwrite)
# End create_table function


if __name__ == '__main__':  # pragma: no cover
    pass
