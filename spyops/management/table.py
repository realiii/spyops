# -*- coding: utf-8 -*-
"""
Data Management for Tables
"""


from typing import Callable, TYPE_CHECKING

from spyops.environment import ANALYSIS_SETTINGS
from spyops.shared.element import copy_element
from spyops.shared.keywords import SOURCE
from spyops.shared.hint import ELEMENT, FIELDS, GPKG
from spyops.shared.util import make_valid_name
from spyops.validation import (
    validate_element, validate_geopackage, validate_overwrite_source,
    validate_result, validate_table, validate_target_table)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Table


__all__ = ['get_count', 'create_table', 'delete_rows', 'truncate_table',
           'copy_rows']


@validate_result()
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


@validate_result()
@validate_table(SOURCE)
@validate_target_table()
@validate_overwrite_source()
def copy_rows(source: 'Table', target: 'Table', *,
              where_clause: str = '') -> 'Table':
    """
    Copy Rows

    Copy rows from a table using a where clause (optional) and write results
    to a target table.
    """
    # noinspection PyTypeChecker
    return copy_element(source=source, target=target, where_clause=where_clause)
# End copy_rows function


# Aliases
truncate_table: Callable[[ELEMENT, str], ELEMENT] = delete_rows


if __name__ == '__main__':  # pragma: no cover
    pass
