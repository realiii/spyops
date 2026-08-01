# -*- coding: utf-8 -*-
"""
Delimited File
"""


from pathlib import Path
from typing import TYPE_CHECKING

from fudgeo.context import ExecuteMany

from spyops.query.conversion.delimited import (
    QueryDelimitedFileToTable, QueryTableToDelimitedFile)
from spyops.shared.hint import ELEMENT, SORT_FIELDS
from spyops.shared.keywords import SORT_FIELDS_ARG, SOURCE, TARGET
from spyops.validation import (
    validate_file, validate_result, validate_sort_field,
    validate_source_element, validate_target_table)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Table


__all__ = ['table_to_delimited_file', 'delimited_file_to_table']


@validate_source_element()
@validate_file(TARGET)
@validate_sort_field(SORT_FIELDS_ARG, element_name=SOURCE)
def table_to_delimited_file(source: ELEMENT, target: Path | str, *,
                            delimiter: str = ',', where_clause: str = '',
                            sort_fields: SORT_FIELDS = (),
                            use_aliases: bool = False) -> Path:
    """
    Table to Delimited File

    Export rows from a table or feature class to a delimited file optionally
    using a where clause, sorting the rows, and using field or alias names
    as the headers.
    """
    target: Path
    query = QueryTableToDelimitedFile(
        source, delimiter=delimiter, where_clause=where_clause,
        sort_fields=sort_fields, use_aliases=use_aliases)
    return query.export(target)
# End table_to_delimited_file function


@validate_result()
@validate_file(SOURCE, is_output=False)
@validate_target_table()
def delimited_file_to_table(source: Path | str, target: 'Table', *,
                            delimiter: str = ',') -> 'Table':
    """
    Delimited File to Table

    Convert a delimited file to a table. Field names are derived from the file
    header.  Field data types are automatically guessed by sampling values
    in the file.
    """
    source: Path
    query = QueryDelimitedFileToTable(
        source, target=target, delimiter=delimiter)
    insert_sql = query.insert
    with (query.target.geopackage.connection as cout,
          ExecuteMany(connection=cout, table=query.target) as executor):
        if not (rows := query.rows()):
            return query.target
        executor(sql=insert_sql, data=rows)
    return query.target
# End delimited_file_to_table function


if __name__ == '__main__':  # pragma: no cover
    pass
