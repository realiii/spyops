# -*- coding: utf-8 -*-
"""
Query Classes for conversion.delimited module
"""


from csv import QUOTE_NONNUMERIC, excel, writer
from functools import cache
from pathlib import Path

from fudgeo.constant import FETCH_SIZE

from spyops.query.base import BaseQuerySelectOrderBy
from spyops.query.conversion.util import _make_unique_fields, _get_dialect
from spyops.shared.constant import COMMA, EMPTY
from spyops.shared.field import make_field_names, validate_fields
from spyops.shared.hint import ELEMENT, FIELDS, SORT_FIELDS


class QueryTableToDelimitedFile(BaseQuerySelectOrderBy):
    """
    Query Table to Delimited File
    """
    def __init__(self, source: ELEMENT, delimiter: str = COMMA,
                 where_clause: str = EMPTY, sort_fields: SORT_FIELDS = (),
                 use_aliases: bool = False) -> None:
        """
        Initialize the QueryTableToDelimitedFile class
        """
        super().__init__(source, target=None, where_clause=where_clause,
                         sort_fields=sort_fields, )
        self._delimiter: str = delimiter
        self._use_aliases: bool = use_aliases
    # End init built-in

    @cache
    def _field_names_and_count(self, element: ELEMENT) -> tuple[int, str, str]:
        """
        Field Names for Select and Insert + Derive Field Count
        """
        fields = self._get_unique_fields()
        return len(fields), EMPTY, make_field_names(fields)
    # End _field_names_and_count method

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        return validate_fields(
            self.source, fields=self.source.fields, exclude_primary=False)
    # End _get_unique_fields method

    def _get_attribute_names(self) -> tuple[str, ...]:
        """
        Get Attribute Names
        """
        fields = self._get_unique_fields()
        if not self._use_aliases:
            return tuple(f.name for f in fields)
        return tuple(f.alias or f.name for f in fields)
    # End _get_attribute_names method

    def export(self, path: Path) -> Path:
        """
        Export the query results to a delimited file.
        """
        dialect = _get_dialect(self._delimiter)
        with self.source.geopackage.connection as cin:
            cursor = cin.execute(self.select)
            with path.open('w') as fout:
                csv = writer(fout, dialect=dialect, quoting=QUOTE_NONNUMERIC)
                csv.writerow(self._get_attribute_names())
                while records := cursor.fetchmany(FETCH_SIZE):
                    csv.writerows(records)
        return path
    # End export method
# End QueryTableToDelimitedFile class


if __name__ == '__main__':  # pragma: no cover
    pass
