# -*- coding: utf-8 -*-
"""
Delimited File
"""


from pathlib import Path

from spyops.query.conversion.delimited import QueryTableToDelimitedFile
from spyops.shared.hint import ELEMENT, SORT_FIELDS
from spyops.shared.keywords import SORT_FIELDS_ARG, SOURCE, TARGET
from spyops.validation import (
    validate_file, validate_sort_field, validate_source_element)


__all__ = ['table_to_delimited_file']


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


if __name__ == '__main__':  # pragma: no cover
    pass
