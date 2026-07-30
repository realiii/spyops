# -*- coding: utf-8 -*-
"""
Query Classes for conversion.delimited module
"""


from collections import defaultdict
from csv import DictReader, QUOTE_NONNUMERIC, reader, writer
from functools import cache, cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from fudgeo import Field
from fudgeo.constant import FETCH_SIZE

from spyops.environment import ANALYSIS_SETTINGS
from spyops.query.base import AbstractSourceQuery, BaseQuerySelectOrderBy
from spyops.query.conversion.util import _make_unique_fields, _get_dialect
from spyops.shared.constant import COMMA, EMPTY
from spyops.shared.field import (
    find_field_data_type, make_field_names, validate_fields)
from spyops.shared.hint import ELEMENT, FIELDS, SORT_FIELDS
from spyops.shared.util import make_valid_field_name


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Table


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
        # noinspection bad-argument-type
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


class QueryDelimitedFileToTable(AbstractSourceQuery):
    """
    Query Delimited File to Table
    """
    def __init__(self, source: Path, target: 'Table',
                 delimiter: str = COMMA) -> None:
        """
        Initialize the QueryDelimitedFileToTable class
        """
        # noinspection PyTypeChecker
        super().__init__(source=None, target=target)
        self._source: Path = source
        self._delimiter: str = delimiter
    # End init built-in

    @property
    def target(self) -> 'Table':
        """
        Alias for Target Empty
        """
        return self.target_empty
    # End target property

    @cached_property
    def target_empty(self) -> 'Table':
        """
        Target Empty
        """
        return self._target.geopackage.create_table(
            self._target.name, fields=self._get_unique_fields(),
            overwrite=ANALYSIS_SETTINGS.overwrite)
    # End target_empty property

    @cached_property
    def _fields(self) -> FIELDS:
        """
        Fields
        """
        fields = self._get_fields_from_source()
        return _make_unique_fields(fields)
    # End _fields property

    def _get_fields_from_source(self) -> list[Field]:
        """
        Get Fields from Source, guess the data type of the field based on the
        first 100 records of the data.
        """
        field_names = None
        data = defaultdict(list)
        dialect = _get_dialect(self._delimiter)
        with self._source.open() as fin:
            csv_reader = DictReader(fin, dialect=dialect)
            field_names = csv_reader.fieldnames
            for i, row in enumerate(csv_reader, 1):
                if i == 100:
                    break
                for key, value in row.items():
                    data[key].append(value)
        if not data or not field_names:
            return []
        field_names = list(field_names)
        data_types = find_field_data_type(
            field_names, data=data, str_source=True)
        junk = '\ufeff\u00ef\u00bb\u00bf'
        field_names = [make_valid_field_name(name.lstrip(junk).strip().upper())
                       for name in field_names]
        return [Field(name=name, data_type=data_type)
                for name, data_type in zip(field_names, data_types)]
    # End _get_fields_from_source method

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        return self._fields
    # End _get_unique_fields method

    @property
    def insert(self) -> str:
        """
        Insert
        """
        elm = self.target
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property

    def rows(self) -> list[tuple]:
        """
        Rows from Delimited File
        """
        field_count = len(self._fields)
        dialect = _get_dialect(self._delimiter)
        with self._source.open() as fin:
            csv_reader = reader(fin, dialect=dialect)
            # NOTE skip over the header row
            next(csv_reader)
            records = [row[:field_count] for row in csv_reader]
        return self._replace_nulls(records)
    # End rows method

    @staticmethod
    def _replace_nulls(records: list) -> list[tuple]:
        """
        Replace Nulls
        """
        nulls = {'<null>', 'null', '#n/a', 'nul', '<unset>', ''}
        return [tuple([None if v.casefold() in nulls else v
                       for v in record]) for record in records]
    # End _replace_nulls method
# End QueryDelimitedFileToTable class


if __name__ == '__main__':  # pragma: no cover
    pass
