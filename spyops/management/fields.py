# -*- coding: utf-8 -*-
"""
Data Management for Fields
"""


from collections import defaultdict
from typing import TYPE_CHECKING

from fudgeo import Field
from fudgeo.enumeration import FieldPropertyType, ShapeType
from fudgeo.extension.schema import EnumerationConstraint, RangeConstraint

from spyops.shared.constant import EMPTY
from spyops.shared.field import (
    GNSS_COMMON_FIELDS, GNSS_FIX_TYPE_FIELD, GNSS_NUM_SATS_FIELD,
    GNSS_POLY_LINE_FIELDS, GNSS_POSITION_SOURCE_TYPE_FIELD,
    GNSS_WORST_FIX_TYPE_FIELD)
from spyops.shared.keywords import (
    ELEMENTS_ARG, FIELD, FIELDS_ARG, FIELD_PROPERTY, SOURCE)
from spyops.shared.enumeration import FieldProperty
from spyops.shared.hint import ELEMENT, ELEMENTS, FIELDS, FIELD_NAMES
from spyops.validation import (
    validate_element, validate_elements, validate_feature_class,
    validate_str_enumeration, validate_field)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from fudgeo.extension.schema import Schema


__all__ = ['delete_field', 'add_field', 'calculate_field', 'alter_field',
           'add_gps_metadata_fields']


@validate_element(SOURCE, has_content=False)
@validate_field(FIELDS_ARG, element_name=SOURCE)
def delete_field(source: ELEMENT, fields: FIELDS | FIELD_NAMES) -> ELEMENT:
    """
    Delete Fields from a Table or Feature Class

    Deletes one or more fields from a table or feature class.
    """
    source.drop_fields(fields)
    return source
# End delete_field function


@validate_element(SOURCE, has_content=False)
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


@validate_element(SOURCE)
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


@validate_element(SOURCE, has_content=False)
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


@validate_feature_class(SOURCE, has_content=False)
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


if __name__ == '__main__':  # pragma: no cover
    pass
