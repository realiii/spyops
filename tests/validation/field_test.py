# -*- coding: utf-8 -*-
"""
Validation tests for Fields
"""


from pytest import raises, mark
from fudgeo import Field
from fudgeo.enumeration import SQLFieldType

from spyops.shared.field import REALS, TEXT_AND_NUMBERS
from spyops.validation import validate_field, validate_table


pytestmark = [mark.validation]


@mark.parametrize('fld, exists, throws', [
    (Field('NAME', data_type=SQLFieldType.text), True, False),
    (Field('name', data_type=SQLFieldType.text), True, False),
    (Field('asdf', data_type=SQLFieldType.text), True, True),
    (Field('NAME', data_type=SQLFieldType.text), False, False),
    (Field('name', data_type=SQLFieldType.text), False, False),
    (Field('asdf', data_type=SQLFieldType.text), False, True),
    ('asdf', True, True),
    ('NAME', True, False),
    (('NAME', 'ANOTHER_NAME'), True, True),
])
def test_validate_field_multiple_fields(world_tables, fld, exists, throws):
    """
    Test validate field multiple fields
    """
    @validate_table('table')
    @validate_field('fields', element_name='table', single=False, exists=exists)
    def field_function(table, fields):
        pass
    tbl = world_tables['admin']
    if throws:
        with raises(ValueError):
            field_function(tbl, fld)
    else:
        field_function(tbl, fld)
# End test_validate_field_multiple_fields function


@mark.parametrize('data_type, data_types, single, throws', [
    (SQLFieldType.float, (), True, False),
    (SQLFieldType.float, REALS, True, False),
    (SQLFieldType.float, TEXT_AND_NUMBERS, True, False),
    (SQLFieldType.text, TEXT_AND_NUMBERS, True, False),
    (SQLFieldType.text, REALS, True, True),
    (SQLFieldType.text, SQLFieldType.boolean, True, True),
    (SQLFieldType.float, (), False, False),
    (SQLFieldType.float, REALS, False, False),
    (SQLFieldType.float, TEXT_AND_NUMBERS, False, False),
    (SQLFieldType.text, TEXT_AND_NUMBERS, False, False),
    (SQLFieldType.text, REALS, False, True),
    (SQLFieldType.text, SQLFieldType.boolean, False, True),
])
def test_validate_field_data_type(data_type, data_types, single, throws):
    """
    Test validate field data type
    """
    @validate_field('field', data_types=data_types, single=single)
    def field_function(field):
        pass
    fld = Field('asdf', data_type=data_type)
    if throws:
        with raises(ValueError):
            field_function(fld)
    else:
        field_function(fld)
# End test_validate_field_data_type function


@mark.parametrize('single, field', [
    (True, 'ID'),
    (False, 'ID'),
    (False, ['ID']),
])
def test_validate_field_data_type_and_string_name(inputs, single, field):
    """
    Test validate field data type
    """
    fc = inputs['intersect_a']
    @validate_field('fld', data_types=TEXT_AND_NUMBERS, single=single, element_name='element')
    def field_function(fld, element):
        return fld
    result = field_function(field, element=fc)
    if single:
        assert isinstance(result, Field)
    else:
        assert all(isinstance(f, Field) for f in result)
# End test_validate_field_data_type_and_string_name function


@mark.parametrize('fld, exists, throws', [
    (Field('NAME', data_type=SQLFieldType.text), True, False),
    (Field('name', data_type=SQLFieldType.text), True, False),
    (Field('asdf', data_type=SQLFieldType.text), True, True),
    (Field('NAME', data_type=SQLFieldType.text), False, False),
    (Field('name', data_type=SQLFieldType.text), False, False),
    (Field('asdf', data_type=SQLFieldType.text), False, True),
    ('asdf', True, True),
    ('NAME', True, False),
])
def test_validate_field_single_field(world_tables, fld, exists, throws):
    """
    Test validate field single field
    """
    @validate_table('table')
    @validate_field('field', element_name='table', single=True, exists=exists)
    def field_function(table, field):
        pass
    tbl = world_tables['admin']
    if throws:
        with raises(ValueError):
            field_function(tbl, fld)
    else:
        field_function(tbl, fld)
# End test_validate_field_single_field function


if __name__ == '__main__':  # pragma: no cover
    pass
