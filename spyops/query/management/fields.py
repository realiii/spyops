# -*- coding: utf-8 -*-
"""
Query classes for management.fields
"""


from fudgeo import Field

from spyops.query.base import AbstractSourceQuery
from spyops.shared.constant import EMPTY
from spyops.shared.field import make_field_names
from spyops.shared.hint import ELEMENT, FIELDS


class QueryCalculateEndTime(AbstractSourceQuery):
    """
    Query for Calculate End Time
    """
    def __init__(self, source: ELEMENT, start_field: Field, end_field: Field,
                 sort_fields: FIELDS) -> None:
        """
        Initialize the QueryCalculateEndTime class
        """
        # noinspection PyTypeChecker
        super().__init__(source, target=source, xy_tolerance=None)
        self._start_field: Field = start_field
        self._end_field: Field = end_field
        self._sort_fields: FIELDS = sort_fields
    # End init built-in

    @property
    def update(self) -> str:
        """
        Update Query
        """
        value = 'value'
        cte = 'lead_values'
        tbl = self.source.escaped_name
        # noinspection PyUnresolvedReferences
        key_name = self.source.primary_key_field.escaped_name
        if self._sort_fields:
            sort_names = make_field_names(self._sort_fields)
        else:
            sort_names = key_name
        return f"""
            WITH {cte} AS (
                SELECT {key_name}, LEAD({self._start_field.escaped_name}) OVER (
                    ORDER BY {sort_names}) AS {value}
                FROM {tbl})
            UPDATE {tbl}
            SET {self._end_field.escaped_name} = {cte}.{value}
            FROM {cte}
            WHERE {tbl}.{key_name} = {cte}.{key_name};
        """
    # End update property

    @property
    def insert(self) -> str:
        """
        Insert
        """
        return EMPTY
    # End insert property
# End QueryCalculateEndTime class


if __name__ == '__main__':  # pragma: no cover
    pass
