# -*- coding: utf-8 -*-
"""
Validation tests for Fields
"""


from pytest import raises, mark
from fudgeo import Field
from fudgeo.enumeration import FieldType

from spyops.crs.unit import DecimalDegrees, Kilometers, Meters
from spyops.shared.field import REALS, TEXT_AND_NUMBERS
from spyops.shared.stats import Average, First
from spyops.validation import (
    validate_compatible_fields, validate_distance, validate_feature_class,
    validate_field,
    validate_statistic_field, validate_table)


pytestmark = [mark.validation]


@mark.parametrize('fld, exists, throws', [
    (Field('NAME', data_type=FieldType.text), True, False),
    (Field('name', data_type=FieldType.text), True, False),
    (Field('asdf', data_type=FieldType.text), True, True),
    (Field('NAME', data_type=FieldType.text), False, False),
    (Field('name', data_type=FieldType.text), False, False),
    (Field('asdf', data_type=FieldType.text), False, True),
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
    (FieldType.float, (), True, False),
    (FieldType.float, REALS, True, False),
    (FieldType.float, TEXT_AND_NUMBERS, True, False),
    (FieldType.text, TEXT_AND_NUMBERS, True, False),
    (FieldType.text, REALS, True, True),
    (FieldType.text, FieldType.boolean, True, True),
    (FieldType.float, (), False, False),
    (FieldType.float, REALS, False, False),
    (FieldType.float, TEXT_AND_NUMBERS, False, False),
    (FieldType.text, TEXT_AND_NUMBERS, False, False),
    (FieldType.text, REALS, False, True),
    (FieldType.text, FieldType.boolean, False, True),
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


@mark.parametrize('single, field, optional, expected', [
    (True, None, True, type(None)),
    (True, 'ID', False, Field),
    (False, 'ID', False, Field),
    (False, ['ID'], False, Field),
])
def test_validate_field_data_type_and_string_name(inputs, single, field, optional, expected):
    """
    Test validate field data type
    """
    fc = inputs['intersect_a']
    @validate_field('fld', data_types=TEXT_AND_NUMBERS, single=single,
                    element_name='element', is_optional=optional)
    def field_function(fld, element):
        return fld
    result = field_function(field, element=fc)
    if single:
        assert isinstance(result, expected)
    else:
        assert all(isinstance(f, expected) for f in result)
# End test_validate_field_data_type_and_string_name function


@mark.parametrize('fld, exists, throws', [
    (Field('NAME', data_type=FieldType.text), True, False),
    (Field('name', data_type=FieldType.text), True, False),
    (Field('asdf', data_type=FieldType.text), True, True),
    (Field('NAME', data_type=FieldType.text), False, False),
    (Field('name', data_type=FieldType.text), False, False),
    (Field('asdf', data_type=FieldType.text), False, True),
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


def test_validate_compatible_field_repeated(world_tables):
    """
    Test validate compatible field repeated
    """
    @validate_table('table')
    @validate_field('field1', element_name='table', single=True)
    @validate_field('field2', element_name='table', single=True)
    @validate_compatible_fields('field1', 'field2')
    def field_function(table, field1, field2):
        pass
    tbl = world_tables['admin']
    with raises(ValueError):
        field_function(tbl, 'name', 'name')
# End test_validate_compatible_field_repeated function


@mark.parametrize('fld1, fld2, throws', [
    ('NAME', 'LAND_RANK', True),
    ('DISPUTED', 'LAND_RANK', False),
    ('LAND_RANK', 'SHAPE_LENGTH', False),
    ('LAND_RANK', 'NAME', False),
])
def test_validate_compatible_field(world_tables, fld1, fld2, throws):
    """
    Test validate compatible field repeated
    """
    @validate_table('table')
    @validate_field('field1', element_name='table', single=True)
    @validate_field('field2', element_name='table', single=True)
    @validate_compatible_fields('field1', 'field2')
    def field_function(table, field1, field2):
        return field1, field2
    tbl = world_tables['admin']
    if throws:
        with raises(TypeError):
            field_function(tbl, fld1, fld2)
    else:
        result = field_function(tbl, fld1, fld2)
        assert all(isinstance(f, Field) for f in result)
# End test_validate_compatible_field_repeated function


@mark.parametrize('stats, expected, throws', [
    (Average('ISO_CODE'), None, True),
    (Average('PART_ID'), None, True),
    (Average('LAND_RANK'), [Average(Field('LAND_RANK', data_type='SMALLINT'))], False),
    (First('ISO_CODE'), [First(Field('ISO_CODE', data_type='TEXT(10)'))], False),
    (First(Field('ISO_CODE', data_type='TEXT')), [First(Field('ISO_CODE', data_type='TEXT(10)'))], False),
    ([First(Field('ISO_CODE', data_type='TEXT'))], [First(Field('ISO_CODE', data_type='TEXT(10)'))], False),
    (Field('ISO_CODE', data_type='TEXT'), None, True),
    (None, [], False),
    ([None], [], False),
    ((), [], False),
])
def test_validate_statistic_field(world_tables, stats, expected, throws):
    """
    Test validate statistic field
    """
    @validate_table('table')
    @validate_statistic_field('stat_fields', element_name='table')
    def stat_function(table, stat_fields):
        return stat_fields
    tbl = world_tables['admin']
    if throws:
        with raises((ValueError, TypeError)):
            stat_function(tbl, stats)
    else:
        result = stat_function(tbl, stats)
        assert all(isinstance(s.field, Field) for s in result)
        assert tuple(result) == tuple(expected)
# End test_validate_statistic_field function


@mark.parametrize('fc_name, value, expected, throws', [
    ('hydro_4617_a', None, None, True),
    ('hydro_4617_a', [], None, True),
    ('hydro_4617_a', 5, DecimalDegrees(5), False),
    ('hydro_4617_a', 5.6, DecimalDegrees(5.6), False),
    ('hydro_6654_a', 5, Meters(5), False),
    ('hydro_6654_a', 5.6, Meters(5.6), False),
    ('hydro_6654_a', 'asdf', None, True),
    ('hydro_6654_a', '5 kms', Kilometers(5), False),
    ('hydro_6654_a', 'CODE', Field('CODE', data_type=FieldType.mediumint), False),
    ('hydro_6654_a', 'PART_ID', Field('PART_ID', data_type=FieldType.integer), False),
    ('hydro_6654_a', 'VALDATE', Field('VALDATE', data_type='TEXT(10)'), False),
])
def test_validate_distance(ntdb_zm_small, fc_name, value, expected, throws):
    """
    Test validate distance
    """
    @validate_feature_class('fc')
    @validate_distance('dist', element_name='fc')
    def dist_function(fc, dist):
        return dist
    tbl = ntdb_zm_small[fc_name]
    if throws:
        with raises((TypeError, ValueError)):
            dist_function(tbl, value)
    else:
        assert dist_function(tbl, value) == expected
# End test_validate_distance function


if __name__ == '__main__':  # pragma: no cover
    pass
