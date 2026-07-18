# -*- coding: utf-8 -*-
"""
Test Field
"""


from fudgeo import Field
from fudgeo.enumeration import FieldType
from pytest import mark

from spyops.shared.field import (
    clone_field, common_fields, find_field_data_type, get_geometry_column_name,
    make_field_names,
    make_unique_fields, validate_fields, _guess_data_type)


pytestmark = [mark.field]


@mark.parametrize('exclude_geometry, exclude_primary, count', [
    (True, True, 11),
    (True, False, 12),
    (False, False, 13),
    (False, True, 12),
])
def test_validate_fields(world_features, exclude_geometry, exclude_primary, count):
    """
    Test validate_fields
    """
    element = world_features['cities_p']
    fields = validate_fields(
        element, fields=element.fields, exclude_geometry=exclude_geometry,
        exclude_primary=exclude_primary)
    assert len(fields) == count
# End test_validate_fields function


def test_validate_fields_repeats(world_features):
    """
    Test validate_fields with repeated fields
    """
    element = world_features['cities_p']
    fields = validate_fields(
        element, fields=element.fields * 2, exclude_geometry=True,
        exclude_primary=True)
    assert len(fields) == 11
# End test_validate_fields_repeats function


@mark.parametrize('fields, count', [
    (Field('A', data_type='TEXT'), 0),
    ([Field('A', data_type='TEXT'), Ellipsis], 0),
])
def test_validate_fields_edge(world_features, fields, count):
    """
    Test validate_fields edge cases
    """
    element = world_features['cities_p']
    fields = validate_fields(element, fields=fields)
    assert len(fields) == count
# End test_validate_fields_edge function


def test_make_field_names_empty():
    """
    Test make_field_names empty
    """
    assert make_field_names([]) == ''
# End test_make_field_names_empty function


@mark.parametrize('include, expected', [
    (False, 'SHAPE'),
    (True, 'SHAPE "[Point]"'),
])
def test_get_geometry_column_name(world_features, include, expected):
    """
    Test get_geometry_column_name
    """
    fc = world_features['cities_p']
    assert get_geometry_column_name(fc, include_geom_type=include) == expected
# End test_get_geometry_column_name function


def test_common_fields(world_features, inputs):
    """
    Test common_fields
    """
    updater = inputs['updater_a']
    admin = world_features['admin_a']
    fields = common_fields(updater, admin)
    assert len(fields) == 1
    field, = fields
    assert field.name == 'NAME'
# End test_common_fields function


def test_clone_field():
    """
    Clone a Field, changing its name
    """
    fld = Field(name='asdf', data_type=FieldType.text, size=50,
                is_nullable=False, default='ABCDEFG')
    cloned = clone_field(fld, 'qwer')
    assert fld != cloned
    assert fld is not cloned
    assert cloned == Field(
        name='qwer', data_type=FieldType.text, size=50,
        is_nullable=False, default='ABCDEFG'
    )
    cloned = clone_field(fld, 'qwer', allow_null=True)
    assert cloned.is_nullable
# End test_clone_field function


@mark.parametrize('existing_names, new_names, expected', [
    (('ID', 'NAME'), ('a', 'b'), ('a', 'b')),
    (('ID', 'NAME'), ('ORIG_FID',), ('ORIG_FID',)),
    (('ORIG_FID', 'ID', 'NAME'), ('ORIG_FID',), ('ORIG_FID_1',)),
])
def test_make_unique_fields(existing_names, new_names, expected):
    """
    Test make unique fields
    """
    existing = [Field(n, data_type=FieldType.text) for n in existing_names]
    fields = [Field(n, data_type=FieldType.text) for n in new_names]
    unique_names = [f.name for f in make_unique_fields(existing, fields)]
    assert tuple(unique_names) == expected
# End test_make_unique_fields function


@mark.parametrize('values, expected', [
    ([123, 234, None, 345, 456, 567, 678, 1000, 10000], FieldType.integer),
    ([123., 234.5, None, 345.6, 456.7, 567.8, 678.9, 1000., 10000], FieldType.real),
    (['A123.', '234', '', None, 'B345.', '456', 'C567', '678', '1000.', 'D10000'], FieldType.text),
    (['3/9/2023 12:15', '2/10/2024', '8-Oct-22', 'May-23', '7/1/1960', '1960.7.1', '1960.07.01', '1960-07-01', '1960-7-1'], FieldType.text),
    (['A', 'B', 'C', '1', '2', '3', '4'], FieldType.text),
])
def test_guess_data_type(values, expected):
    """
    Test guess_data_type
    """
    assert _guess_data_type(values) == expected
# End test_guess_data_type function


def test_find_field_data_type():
    """
    Test find_field_data_type
    """
    data = {
        'asdf': [1, 2, 3, 4, 5, None, None],
        'lmnop': ['a', 'b', 'c', 'd', 'e', None, None],
        'xyz': [1.1, 2.2, 3.3, 4.4, 5.5, None, None],
    }
    types = find_field_data_type(list(data), data)
    assert types == (FieldType.integer, FieldType.text, FieldType.real)
# End test_find_field_data_type function


if __name__ == '__main__':  # pragma: no cover
    pass
