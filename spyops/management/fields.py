# -*- coding: utf-8 -*-
"""
Data Management for Fields
"""


from collections import defaultdict
from typing import TYPE_CHECKING

from fudgeo import Field
from fudgeo.context import ExecuteMany
from fudgeo.enumeration import FieldPropertyType, FieldType, ShapeType
from fudgeo.extension.schema import EnumerationConstraint, RangeConstraint

from spyops.shared.reclass import AbstractReclass, EqualIntervalReclass
from spyops.query.management.fields import (
    FIELD_STANDARDIZE_TYPE, FIELD_TRANSFORM_TYPE, QueryCalculateEndTime,
    QueryFieldStatisticsToTableDate, QueryFieldStatisticsToTableNumeric,
    QueryFieldStatisticsToTableText, QueryReclassifyField,
    QueryReclassifyFieldUniqueValues)
from spyops.shared.constant import EMPTY
from spyops.shared.field import (
    DATES, GNSS_COMMON_FIELDS, GNSS_FIX_TYPE_FIELD, GNSS_NUM_SATS_FIELD,
    GNSS_POLY_LINE_FIELDS, GNSS_POSITION_SOURCE_TYPE_FIELD,
    GNSS_WORST_FIX_TYPE_FIELD, NUMBERS, TEXTS, TEXT_AND_NUMBERS,
    filter_by_data_type, simplify_type)
from spyops.shared.keywords import (
    ELEMENTS_ARG, END_FIELD, FIELD, FIELDS_ARG, FIELD_PROPERTY, GROUP_FIELDS,
    LABEL_FIELD, METHOD, OUTPUT_FIELD, OUTPUT_TYPE_OPTION, SORT_FIELDS_ARG,
    SOURCE, START_FIELD)
from spyops.shared.enumeration import (
    FieldProperty, ReclassificationMethod, StandardizationMethod,
    StatisticOutputOption, TransformationMethod)
from spyops.shared.hint import (
    ELEMENT, ELEMENTS, FIELDS, FIELD_NAMES, NUMBER, OPT_FIELD_STR)
from spyops.validation import (
    validate_compatible_fields, validate_elements, validate_overwrite_source,
    validate_result, validate_source_element, validate_source_feature_class,
    validate_str_enumeration, validate_field, validate_target_table)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, Table
    from fudgeo.extension.schema import Schema


__all__ = ['delete_field', 'add_field', 'calculate_field', 'alter_field',
           'add_gps_metadata_fields', 'calculate_end_time',
           'field_statistics_to_table', 'standardize_field', 'transform_field',
           'reclassify_field']


@validate_result()
@validate_source_element(has_content=False)
@validate_field(FIELDS_ARG, element_name=SOURCE)
def delete_field(source: ELEMENT, fields: FIELDS | FIELD_NAMES) -> ELEMENT:
    """
    Delete Fields from a Table or Feature Class

    Deletes one or more fields from a table or feature class.
    """
    source.drop_fields(fields)
    return source
# End delete_field function


@validate_result()
@validate_source_element(has_content=False)
@validate_field(FIELDS_ARG, exists=False)
@validate_elements(ELEMENTS_ARG, has_content=False)
def add_field(source: ELEMENT, *, fields: FIELDS = (),
              elements: ELEMENTS = ()) -> ELEMENT:
    """
    Add Fields to a Table or Feature Class

    Adds one or more fields to a table or feature class using the schemas
    of elements and / or explicitly defined fields.
    """
    if not fields and not elements:
        return source
    fields: list[Field]
    fields = list(fields)
    for element in elements:
        # noinspection PyProtectedMember
        fields.extend(element._validate_fields(element.fields))
    if not fields:
        return source
    grouped = defaultdict(list)
    for field in fields:
        grouped[field.name.casefold()].append(field)
    source.add_fields([f for f, *_ in grouped.values()])
    return source
# End add_field function


@validate_result()
@validate_source_element()
@validate_field(FIELD, single=True, element_name=SOURCE)
def calculate_field(source: ELEMENT, field: Field | str, expression: str, *,
                    where_clause: str = '') -> ELEMENT:
    """
    Calculate Field

    Calculate a value into an existing field using a SQL expression based
    on field names, database functions, etc. Optionally, use a where clause
    to restrict the calculation to a subset of rows.
    """
    if not where_clause:
        where_clause = EMPTY
    else:
        where_clause = f'WHERE {where_clause}'
    field: Field
    with source.geopackage.connection as conn:
        # noinspection SqlWithoutWhere
        conn.execute(f"""
            UPDATE {source.escaped_name}  
            SET {field.escaped_name} = {expression} 
            {where_clause}
        """)
    return source
# End calculate_field function


@validate_result()
@validate_source_element(has_content=False)
@validate_field(FIELD, single=True, element_name=SOURCE)
@validate_str_enumeration(FIELD_PROPERTY, FieldProperty)
def alter_field(source: ELEMENT, field: Field | str, *,
                field_property: FieldProperty = FieldProperty.NAME,
                value: str | None) -> ELEMENT:
    """
    Alter Field

    Alter an existing field in a Table or Feature Class by updating the
    field name, adding / updating a field alias, or adding / updating
    a field comment.
    """
    lut = {FieldProperty.ALIAS: FieldPropertyType.alias,
           FieldProperty.COMMENT: FieldPropertyType.comment}
    if field_property == FieldProperty.NAME:
        if not value or not str(value).strip():
            raise ValueError('Value must be specified for field name.')
        source.rename_field(field, name=value)
    elif field_property in lut:
        field: Field
        prop_name = lut[field_property]
        source.geopackage.enable_schema_extension()
        if schema := source.geopackage.schema:
            schema.set_field_property(
                table_name=source.name, column_name=field.name,
                prop_name=prop_name, value=value)
    return source
# End alter_field function


@validate_result()
@validate_source_feature_class(has_content=False)
def add_gps_metadata_fields(source: 'FeatureClass') -> 'FeatureClass':
    """
    Add GPS Metadata Fields

    Add GNSS GPS Metadata fields to a Feautre Class, if a field name already
    exists in the Feature Class, it is not overwritten.  If not already
    enabled, the Schema Extension is enabled in the GeoPackage.
    """
    fix_type = EnumerationConstraint(
        name='fix_type_domain', values=[0, 1, 2, 4, 5],
        descriptions=['Fix not valid', 'GPS', 'Differential GPS',
                      'RTK Fixed', 'RTK Float'])
    if source.add_fields(GNSS_COMMON_FIELDS):
        if source.geopackage.enable_schema_extension():
            source_type = EnumerationConstraint(
                name='positionsourcetype_domain', values=[0, 1, 2, 3, 4],
                descriptions=['Unknown', 'User Defined',
                              'Integrated (System) Location Provider',
                              'External GNSS Receiver',
                              'Network Location Provider'])
            satellite_range = RangeConstraint(
                name='num_sats_domain', min_value=0, max_value=99,
                description='Number of Satellites')
            # noinspection PyTypeChecker
            schema: Schema = source.geopackage.schema
            schema.add_constraints([source_type, fix_type, satellite_range])
            schema.add_column_definition(
                table_name=source.name,
                column_name=GNSS_POSITION_SOURCE_TYPE_FIELD.name,
                constraint_name=source_type.name)
            schema.add_column_definition(
                table_name=source.name, column_name=GNSS_FIX_TYPE_FIELD.name,
                constraint_name=fix_type.name)
            schema.add_column_definition(
                table_name=source.name, column_name=GNSS_NUM_SATS_FIELD.name,
                constraint_name=satellite_range.name)
    if ShapeType.point in source.shape_type:
        return source
    if source.add_fields(GNSS_POLY_LINE_FIELDS):
        if source.geopackage.enable_schema_extension():
            # noinspection PyTypeChecker
            schema: Schema = source.geopackage.schema
            schema.add_constraints([fix_type])
            schema.add_column_definition(
                table_name=source.name,
                column_name=GNSS_WORST_FIX_TYPE_FIELD.name,
                constraint_name=fix_type.name)
    return source
# End add_gps_metadata_fields function


@validate_result()
@validate_source_element()
@validate_field(START_FIELD, single=True, element_name=SOURCE)
@validate_field(END_FIELD, single=True, element_name=SOURCE)
@validate_compatible_fields(START_FIELD, END_FIELD)
@validate_field(SORT_FIELDS_ARG, element_name=SOURCE, is_optional=True)
def calculate_end_time(source: ELEMENT, *,
                       start_field: Field | str, end_field: Field | str,
                       sort_fields: FIELDS | FIELD_NAMES = ()) -> ELEMENT:
    """
    Calculate End Time

    Calculates an End Value for each row / feature in a Table / Feature Class.
    The End Values derived from the next value in the Start Field row / feature
    as defined by the underlying table order or based on supplied sort fields.
    """
    # noinspection PyTypeChecker
    query = QueryCalculateEndTime(
        source, start_field=start_field, end_field=end_field,
        sort_fields=sort_fields)
    with query.source.geopackage.connection as cin:
        cin.execute(query.update)
    return query.source
# End calculate_end_time function


@validate_result()
@validate_source_element()
@validate_target_table()
@validate_field(FIELDS_ARG, element_name=SOURCE)
@validate_field(GROUP_FIELDS, element_name=SOURCE, is_optional=True)
@validate_str_enumeration(OUTPUT_TYPE_OPTION, StatisticOutputOption)
@validate_overwrite_source()
def field_statistics_to_table(source: ELEMENT, target: 'Table', *,
                              fields: FIELDS | FIELD_NAMES,
                              group_fields: FIELDS | FIELD_NAMES = (),
                              output_type_option: StatisticOutputOption = (
                                      StatisticOutputOption.NUMERIC),
                              where_clause: str = '') -> 'Table':
    """
    Field Statistics to Table

    Create a table of summary statistics for the selected fields from a table
    or feature class, subsetted by the chosen output type.  Optionally, provide
    a where clause to operate on a subset of the data.
    """
    fields: FIELDS
    group_fields: FIELDS
    if output_type_option == StatisticOutputOption.DATE:
        cls = QueryFieldStatisticsToTableDate
        data_types = DATES
    elif output_type_option == StatisticOutputOption.TEXT:
        cls = QueryFieldStatisticsToTableText
        data_types = TEXTS
    else:
        cls = QueryFieldStatisticsToTableNumeric
        data_types = NUMBERS
    if not (fields := filter_by_data_type(fields, data_types=data_types)):
        raise ValueError(
            f'No fields found matching the {output_type_option} data types.')
    with cls(source, target=target, fields=fields, group_fields=group_fields,
             where_clause=where_clause,) as query:
        with (query.source.geopackage.connection as cin,
              query.target.geopackage.connection as cout,
              ExecuteMany(cout, query.target) as executor):
            records = query.build_statistics(cin)
            executor(query.insert, records)
    return query.target
# End field_statistics_to_table function


@validate_result()
@validate_source_element()
@validate_field(FIELD, single=True, element_name=SOURCE, data_types=NUMBERS)
@validate_field(OUTPUT_FIELD, single=True, element_name=SOURCE,
                data_types=NUMBERS)
@validate_compatible_fields(FIELD, OUTPUT_FIELD)
@validate_str_enumeration(METHOD, StandardizationMethod)
def standardize_field(source: ELEMENT, field: Field | str,
                      output_field: Field | str, *,
                      method: StandardizationMethod = (
                              StandardizationMethod.Z_SCORE),
                      min_value: NUMBER = 0, max_value: NUMBER = 0,
                      where_clause: str = '') -> ELEMENT:
    """
    Standardize Field

    Standardizes the values in a field by using one of the standardization
    methods.  Resulting values are written to an output field in the same
    feature class or table.  Optionally, provide a where clause to operate
    on a subset of the data.
    """
    cls = FIELD_STANDARDIZE_TYPE[method]
    kwargs = dict(source=source, field=field, output_field=output_field,
                  where_clause=where_clause)
    if method == StandardizationMethod.MIN_MAX:
        # noinspection PyTypeChecker
        kwargs.update(dict(min_value=min(min_value, max_value),
                           max_value=max(min_value, max_value)))
    with cls(**kwargs) as query:
        with query.source.geopackage.connection as cin:
            cin.execute(query.update)
    return query.source
# End standardize_field function


@validate_result()
@validate_source_element()
@validate_field(FIELD, single=True, element_name=SOURCE, data_types=NUMBERS)
@validate_field(OUTPUT_FIELD, single=True, element_name=SOURCE,
                data_types=NUMBERS)
@validate_compatible_fields(FIELD, OUTPUT_FIELD)
@validate_str_enumeration(METHOD, TransformationMethod)
def transform_field(source: ELEMENT, field: Field | str,
                    output_field: Field | str, *,
                    method: TransformationMethod = TransformationMethod.BOX_COX,
                    power: NUMBER = 0, shift: NUMBER = 0,
                    where_clause: str = '') -> ELEMENT:
    """
    Transform Field

    Transforms values in a field by applying a mathematical function.
    Optionally, provide a where clause to operate on a subset of the data.
    """
    field: Field
    output_field: Field
    cls = FIELD_TRANSFORM_TYPE[method]
    with cls(source=source, field=field, output_field=output_field,
             power=power, shift=shift, where_clause=where_clause) as query:
        with query.source.geopackage.connection as cin:
            cin.execute(query.update)
    return query.source
# End transform_field function


@validate_result()
@validate_source_element()
@validate_field(FIELD, single=True, element_name=SOURCE,
                data_types=TEXT_AND_NUMBERS)
@validate_field(OUTPUT_FIELD, single=True, element_name=SOURCE,
                data_types=NUMBERS)
@validate_field(LABEL_FIELD, single=True, element_name=SOURCE, data_types=TEXTS,
                is_optional=True)
def reclassify_field(source: ELEMENT, field: Field | str,
                     output_field: Field | str,
                     reclass: AbstractReclass = EqualIntervalReclass(), *,
                     label_field: OPT_FIELD_STR = None,
                     where_clause: str = '') -> ELEMENT:
    """
    Reclassify Field

    Reclassify values in a field by applying a reclassification methodology.
    Generates a range label for the reclassified values.  Optionally,
    provide a where clause to operate on a subset of the data.
    """
    field: Field
    output_field: Field
    label_field: Field | None
    unique = ReclassificationMethod.UNIQUE_VALUES
    if simplify_type(field) == FieldType.text:
        if reclass.method != unique:
            raise ValueError(
                'Text fields only support the Unique Values method')
    if reclass.method == unique:
        cls = QueryReclassifyFieldUniqueValues
    else:
        cls = QueryReclassifyField
    with cls(source=source, field=field, output_field=output_field,
             label_field=label_field, reclass=reclass,
             where_clause=where_clause) as query:
        with query.source.geopackage.connection as cin:
            cin.execute(query.update)
            if sql := query.update_label:
                cin.execute(sql)
    return query.source
# End reclassify_field function


if __name__ == '__main__':  # pragma: no cover
    pass
