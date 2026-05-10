# -*- coding: utf-8 -*-
"""
Query Classes for management.statistics module
"""


from functools import cache, cached_property
from typing import TYPE_CHECKING

from fudgeo.constant import COMMA_SPACE

from spyops.environment import ANALYSIS_SETTINGS
from spyops.query.base import AbstractElementGroupQuery
from spyops.query.mixin import StatisticsMixin
from spyops.shared.constant import EMPTY
from spyops.shared.field import make_field_names
from spyops.shared.hint import ELEMENT, FIELDS, STATS_FIELDS
from spyops.shared.sql import SQL_ALL_ID


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Table


class QueryStatistics(StatisticsMixin, AbstractElementGroupQuery):
    """
    Query Statistics
    """
    def __init__(self, element: ELEMENT, target: 'Table',
                 statistics: STATS_FIELDS, fields: FIELDS,
                 where_clause: str) -> None:
        """
        Initialize the QueryStatistics class
        """
        super().__init__(element, fields=fields)
        self._target: 'Table' = target
        self._statistics: STATS_FIELDS = statistics
        self._where_clause: str = where_clause
    # End init built-in

    @cache
    def _field_names_and_count(self, element: ELEMENT) \
            -> tuple[int, str, str]:
        """
        Field Names for Select and Insert + Derive Field Count
        """
        fields = self._fields
        stats = self.statistics
        field_count = len(fields) + len(stats)

        select_names = insert_names = make_field_names(fields)
        select_stats = COMMA_SPACE.join([s.aggregate for s in stats])
        if select_names:
            select_names = self._concatenate(select_names, select_stats)
        else:
            select_names = select_stats

        stats_fields = self._get_unique_fields()[len(fields):]
        insert_stats = make_field_names(stats_fields)
        if insert_names:
            insert_names = self._concatenate(insert_names, insert_stats)
        else:
            insert_names = insert_stats
        return field_count, insert_names, select_names
    # End _field_names_and_count method

    @property
    def select(self) -> str:
        """
        Select
        """
        elm = self.source
        # noinspection PyArgumentList
        *_, select_field_names = self._field_names_and_count(elm)
        where_clause = (self._where_clause or EMPTY).strip() or SQL_ALL_ID
        if not self._group_names:
            return self._make_select(
                elm, field_names=select_field_names, where_clause=where_clause)
        return f"""
            SELECT {select_field_names}
            FROM {elm.escaped_name} 
            WHERE {where_clause}
            GROUP BY {self._group_names}
        """
    # End select property

    @property
    def insert(self) -> str:
        """
        Insert
        """
        # noinspection PyArgumentList
        field_count, insert_names, _ = self._field_names_and_count(self.target)
        return self._make_insert(
            self.target.escaped_name, field_names=insert_names,
            field_count=field_count)
    # End insert property

    @property
    def target(self) -> 'Table':
        """
        Target
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
# End QueryStatistics class


if __name__ == '__main__':  # pragma: no cover
    pass
