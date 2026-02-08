# -*- coding: utf-8 -*-
"""
Data Management for Tables
"""


from typing import Callable, TYPE_CHECKING

from spyops.environment import ANALYSIS_SETTINGS
from spyops.shared.constant import SOURCE
from spyops.shared.hint import ELEMENT, FIELDS, GPKG
from spyops.shared.util import make_valid_name
from spyops.validation import (
    validate_element, validate_geopackage, validate_result)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Table


__all__ = ['get_count', 'create_table', 'delete_rows', 'truncate_table']


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

    Create a new table in a geopackage with specified fields and
    optional description.
    """
    overwrite = ANALYSIS_SETTINGS.overwrite
    name = make_valid_name(name, prefix='tbl')
    return geopackage.create_table(
        name, fields=fields, description=description, overwrite=overwrite)
# End create_table function


@validate_result()
@validate_element(SOURCE, has_content=False)
def delete_rows(source: ELEMENT, *, where_clause: str = '') -> ELEMENT:
    """
    Delete rows from a Table or Feature Class

    Deletes rows from a table or feature class using a where clause (optional).
    """
    source.delete(where_clause=where_clause)
    return source
# End delete_rows function


# Aliases
truncate_table: Callable[[ELEMENT, str], ELEMENT] = delete_rows


if __name__ == '__main__':  # pragma: no cover
    pass
