# -*- coding: utf-8 -*-
"""
Query classes for management.fields
"""


from abc import abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING, Type

from fudgeo import Field, Table
from fudgeo.constant import COMMA_SPACE

from spyops.environment import ANALYSIS_SETTINGS
from spyops.query.base import AbstractElementGroupQuery, AbstractSourceQuery
from spyops.query.mixin import AggregateContextMixin, StatisticsMixin
from spyops.shared.constant import EMPTY, VALUE
from spyops.shared.field import (
    FIELD_ALIAS, FIELD_NAME, FIELD_TYPE, add_key_fields, make_field_names)
from spyops.shared.hint import ELEMENT, FIELDS, NUMBER
from spyops.shared.sql import IN
from spyops.shared.stats import (
    DATE_STATS, InterquartileRange, Mean, Median, Min, NUMERIC_STATS, Range,
    STAT_NAME_ALIASES, StdDev, TEXT_STATS)


if TYPE_CHECKING:  # pragma: no cover
    from sqlite3 import Connection


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
        super().__init__(source, target=source)
        self._start_field: Field = start_field
        self._end_field: Field = end_field
        self._sort_fields: FIELDS = sort_fields
    # End init built-in

    @property
    def update(self) -> str:
        """
        Update Query
        """
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
                    ORDER BY {sort_names}) AS {VALUE}
                FROM {tbl})
            UPDATE {tbl}
            SET {self._end_field.escaped_name} = {cte}.{VALUE}
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


class AbstractFieldStatisticsToTableQuery(StatisticsMixin, 
                                          AbstractElementGroupQuery):
    """
    Abstract Field Statistics to Table
    """
    def __init__(self, source: ELEMENT, target: Table, fields: FIELDS,
                 group_fields: FIELDS, where_clause: str, *, 
                 stat_classes: tuple[tuple[Type, str], ...]) -> None:
        """
        Initialize the AbstractFieldStatisticsToTableQuery class
        """
        super().__init__(element=source, fields=group_fields)
        self._target: Table = target
        self._input_fields: FIELDS = fields
        self._where_clause: str = where_clause
        self._stat_classes: tuple[tuple[Type, str], ...] = stat_classes
    # End init built-in

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        fields = [FIELD_NAME, FIELD_ALIAS, FIELD_TYPE]
        for cls, field_type in self._stat_classes:
            name, alias = STAT_NAME_ALIASES[cls(EMPTY).statistic]
            fields.append(Field(name=name, alias=alias, data_type=field_type))
        if self._fields:
            # NOTE here we deem standardization of the statistics columns to
            #  be more important than the grouping field names
            group_fields = list(self._fields)
            add_key_fields(group_fields, key_fields=fields)
            # NOTE ignore the output from the function and rely on the inplace
            #  assignment of field objects in the group_fields list
            fields = [*group_fields, *fields]
        return fields
    # End _get_unique_fields method

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        stub = '{}'
        where_clause = self._get_where_clause()
        if self._fields:
            field_names = self._concatenate(self._group_names, stub)
            sql = self._make_select(
                self.source, field_names=field_names, where_clause=where_clause)
            return f'{sql} GROUP BY {self._group_names}'
        return self._make_select(
            self.source, field_names=stub, where_clause=where_clause)
    # End select property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        fields = self._get_unique_fields()
        return self._make_insert(
            self.target.escaped_name, field_names=make_field_names(fields),
            field_count=len(fields))
    # End insert property

    @property
    def target(self) -> Table:
        """
        Target
        """
        return self.target_empty
    # End target property

    @cached_property
    def target_empty(self) -> Table:
        """
        Target Empty
        """
        return self._target.geopackage.create_table(
            self._target.name, fields=self._get_unique_fields(),
            overwrite=ANALYSIS_SETTINGS.overwrite)
    # End target_empty property

    def build_statistics(self, connection: 'Connection') -> list[tuple]:
        """
        Build Statistics Records
        """
        records = []
        count = len(self._fields)
        head = slice(0, count)
        # noinspection PyArgumentEqualDefault
        tail = slice(count, None)
        select_stub = self.select
        classes, _ = zip(*self._stat_classes)
        for field in self._input_fields:
            field_data = field.name, field.alias, field.data_type
            stats = [cls(field) for cls in classes]
            select = select_stub.format(
                COMMA_SPACE.join([s.aggregate for s in stats]))
            cursor = connection.execute(select)
            records.extend([(*rec[head], *field_data, *rec[tail])
                            for rec in cursor.fetchall()])
        return records
    # End build_statistics method
# End AbstractFieldStatisticsToTableQuery class


class QueryFieldStatisticsToTableNumeric(AbstractFieldStatisticsToTableQuery):
    """
    Query Field Statistics to Table for Numeric Fields
    """
    def __init__(self, source: ELEMENT, target: Table, fields: FIELDS,
                 group_fields: FIELDS, where_clause: str) -> None:
        """
        Initialize the QueryFieldStatisticsToTableNumeric class
        """
        super().__init__(source, target=target, fields=fields,
                         group_fields=group_fields, where_clause=where_clause,
                         stat_classes=NUMERIC_STATS)
    # End init built-in
# End QueryFieldStatisticsToTableNumeric class


class QueryFieldStatisticsToTableText(AbstractFieldStatisticsToTableQuery):
    """
    Query Field Statistics to Table for Text Fields
    """
    def __init__(self, source: ELEMENT, target: Table, fields: FIELDS,
                 group_fields: FIELDS, where_clause: str) -> None:
        """
        Initialize the QueryFieldStatisticsToTableText class
        """
        super().__init__(source, target=target, fields=fields,
                         group_fields=group_fields, where_clause=where_clause,
                         stat_classes=TEXT_STATS)
    # End init built-in
# End QueryFieldStatisticsToTableText class


class QueryFieldStatisticsToTableDate(AbstractFieldStatisticsToTableQuery):
    """
    Query Field Statistics to Table for Date Fields
    """
    def __init__(self, source: ELEMENT, target: Table, fields: FIELDS,
                 group_fields: FIELDS, where_clause: str) -> None:
        """
        Initialize the QueryFieldStatisticsToTableDate class
        """
        super().__init__(source, target=target, fields=fields,
                         group_fields=group_fields, where_clause=where_clause,
                         stat_classes=DATE_STATS)
    # End init built-in
# End QueryFieldStatisticsToTableDate class


class AbstractQueryStandardizeField(AggregateContextMixin, AbstractSourceQuery):
    """
    Abstract Query for Standardize Field
    """
    def __init__(self, source: ELEMENT, field: Field, output_field: Field,
                 where_clause: str) -> None:
        """
        Initialize the AbstractQueryStandardizeField class
        """
        # noinspection PyTypeChecker
        super().__init__(source, target=source, where_clause=where_clause)
        self._field: Field = field
        self._output_field: Field = output_field
    # End init built-in

    @abstractmethod
    def _get_expression(self) -> str:
        """
        Get Standardization Expression
        """
        pass
    # End _get_expression method

    def _cast_statistic(self, stat: str) -> str:
        """
        Cast Statistic
        """
        where_clause = self._build_where_clause()
        return f"""(
            SELECT {stat} 
            FROM {self.source.escaped_name} 
            WHERE {where_clause}
        )"""
    # End _cast_statistic method

    @property
    def update(self) -> str:
        """
        Update Query
        """
        element = self.source
        cte = 'standard_values'
        tbl = element.escaped_name
        # noinspection PyUnresolvedReferences
        key_name = element.primary_key_field.escaped_name
        where_clause = self._build_where_clause()
        expression = self._get_expression()
        return f"""
            WITH {cte} AS (
                SELECT {key_name}, {expression} AS {VALUE}  
                FROM {tbl}
                WHERE {where_clause}
            )
            UPDATE {tbl}
            SET {self._output_field.escaped_name} = {cte}.{VALUE}
            FROM {cte}
            WHERE {tbl}.{key_name} = {cte}.{key_name};
        """
    # End update property

    def _build_where_clause(self) -> str:
        """
        Build Where Clause
        """
        element = self.source
        where_clause = self._get_where_clause()
        if ANALYSIS_SETTINGS.extent:
            if where := self._spatial_index_where(
                    element, extent=self._shared_extent(element)):
                clauses = where.format(IN), where_clause
                where_clause = ' AND '.join(f'({w})' for w in clauses if w)
        return where_clause
    # End _build_where_clause method

    @property
    def insert(self) -> str:
        """
        Insert
        """
        return EMPTY
    # End insert property
# End AbstractQueryStandardizeField class


class QueryStandardizeFieldZScore(AbstractQueryStandardizeField):
    """
    Query Standardize Field Z Score
    """
    def _get_expression(self) -> str:
        """
        Get Standardization Expression
        """
        mean = self._cast_statistic(repr(Mean(self._field)))
        std = self._cast_statistic(repr(StdDev(self._field)))
        return f'({self._field.escaped_name} - {mean}) / {std}'
    # End _get_expression method
# End QueryStandardizeFieldZScore class


class QueryStandardizeFieldMinMax(AbstractQueryStandardizeField):
    """
    Query Standardize Field Min Max
    """
    def __init__(self, source: ELEMENT, field: Field, output_field: Field,
                 min_value: NUMBER, max_value: NUMBER,
                 where_clause: str) -> None:
        """
        Initialize the QueryStandardizeFieldMinMax class
        """
        super().__init__(source, field=field, output_field=output_field,
                         where_clause=where_clause)
        self._min_value: NUMBER = min_value
        self._max_value: NUMBER = max_value
    # End init built-in

    def _get_expression(self) -> str:
        """
        Get Standardization Expression
        """
        min_ = self._cast_statistic(repr(Min(self._field)))
        rng = self._cast_statistic(repr(Range(self._field)))
        a = self._min_value
        b = self._max_value
        numerator = f'({self._field.escaped_name} - {min_}) * ({b} - {a})'
        return f'{a} + ({numerator} / {rng})'
    # End _get_expression method
# End QueryStandardizeFieldMinMax class


class QueryStandardizeFieldAbsoluteMax(AbstractQueryStandardizeField):
    """
    Query Standardize Field Absolute Max
    """
    def _get_expression(self) -> str:
        """
        Get Standardization Expression
        """
        name = self._field.escaped_name
        abs_max = self._cast_statistic(f'MAX(ABS({name}))')
        return f'{name} / {abs_max}'
    # End _get_expression method
# End QueryStandardizeFieldAbsoluteMax class


class QueryStandardizeFieldRobust(AbstractQueryStandardizeField):
    """
    Query Standardized Field Robust Standardization
    """
    def _get_expression(self) -> str:
        """
        Get Standardization Expression
        """
        med = self._cast_statistic(repr(Median(self._field)))
        iqr = self._cast_statistic(repr(InterquartileRange(self._field)))
        return f'({self._field.escaped_name} - {med}) / {iqr}'
    # End _get_expression method
# End QueryStandardizeFieldRobust class


if __name__ == '__main__':  # pragma: no cover
    pass
