# -*- coding: utf-8 -*-
"""
Test Field
"""


from fudgeo import Field
from fudgeo.enumeration import DataType, SQLFieldType
from pytest import mark

from geomio.shared.field import (
    clone_field, common_fields, get_geometry_column_name, make_field_names,
    validate_fields)


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
    fld = Field(name='asdf', data_type=SQLFieldType.text, size=50,
              is_nullable=False, default='ABCDEFG')
    cloned = clone_field(fld, 'qwer')
    assert fld != cloned
    assert fld is not cloned
    assert cloned == Field(
        name='qwer', data_type=SQLFieldType.text, size=50,
        is_nullable=False, default='ABCDEFG'
    )
# End test_clone_field function


if __name__ == '__main__':  # pragma: no cover
    pass
