# -*- coding: utf-8 -*-
"""
Test for Validation used on Enumeration-esque values
"""


from fudgeo import Field
from pytest import raises, mark

from spyops.shared.enumeration import (
    AttributeOption, DissolveOption, EndOption, GeometryAttribute,
    OutputTypeOption, SideOption)
from spyops.shared.exception import OperationsError
from spyops.validation import (
    validate_dissolve_option, validate_end_option, validate_field,
    validate_side_option, validate_str_enumeration, validate_geometry_attribute,
    validate_output_type)


pytestmark = [mark.validation]


@mark.parametrize('value, expected, throws', [
    (None, None, True),
    ('ALL', AttributeOption.ALL, False),
    (AttributeOption.ONLY_FID, AttributeOption.ONLY_FID, False),
    (10, None, True),
])
def test_validate_enumeration(value, expected, throws):
    """
    Test validate enumeration
    """
    @validate_str_enumeration('option', AttributeOption)
    def enum_function(option):
        return option
    if throws:
        with raises(ValueError):
            enum_function(value)
    else:
        assert enum_function(value) == expected
# End test_validate_enumeration function


@mark.parametrize('source_name, operator_name, option, throws', [
    ('admin_a', 'intersect_a', OutputTypeOption.SAME, False),
    ('rivers_l', 'intersect_a', OutputTypeOption.SAME, False),
    ('airports_p', 'intersect_a', OutputTypeOption.SAME, False),
    ('rivers_l', 'rivers_portion_l', OutputTypeOption.SAME, False),
    ('airports_p', 'rivers_portion_l', OutputTypeOption.SAME, False),
    ('airports_p', 'river_p', OutputTypeOption.SAME, False),
    ('admin_a', 'intersect_a', OutputTypeOption.LINE, False),
    ('rivers_l', 'intersect_a', OutputTypeOption.LINE, False),
    ('airports_p', 'intersect_a', OutputTypeOption.LINE, True),
    ('rivers_l', 'rivers_portion_l', OutputTypeOption.LINE, False),
    ('airports_p', 'rivers_portion_l', OutputTypeOption.LINE, True),
    ('airports_p', 'river_p', OutputTypeOption.LINE, True),
    ('admin_a', 'intersect_a', OutputTypeOption.POINT, False),
    ('rivers_l', 'intersect_a', OutputTypeOption.POINT, False),
    ('airports_p', 'intersect_a', OutputTypeOption.POINT, False),
    ('rivers_l', 'rivers_portion_l', OutputTypeOption.POINT, False),
    ('airports_p', 'rivers_portion_l', OutputTypeOption.POINT, False),
    ('airports_p', 'river_p', OutputTypeOption.POINT, False),
])
def test_validate_output_type(inputs, world_features, source_name, operator_name, option, throws):
    """
    Test validate output type
    """
    source = world_features[source_name]
    operator = inputs[operator_name]
    @validate_output_type('opt', 's')
    def geom_function(s, o, opt):
        return opt

    if throws:
        with raises(OperationsError):
            geom_function(source, operator, option)
    else:
        assert geom_function(source, operator, option) == option
# End test_validate_output_type function


@mark.parametrize('fc_name, option, expected', [
    ('admin_a', SideOption.FULL, SideOption.FULL),
    ('admin_a', SideOption.RIGHT, SideOption.FULL),
    ('admin_a', SideOption.LEFT, SideOption.FULL),
    ('admin_a', SideOption.ONLY_OUTSIDE, SideOption.ONLY_OUTSIDE),
    ('rivers_l', SideOption.FULL, SideOption.FULL),
    ('rivers_l', SideOption.LEFT, SideOption.LEFT),
    ('rivers_l', SideOption.RIGHT, SideOption.RIGHT),
    ('rivers_l', SideOption.ONLY_OUTSIDE, SideOption.FULL),
    ('airports_p', SideOption.FULL, SideOption.FULL),
    ('airports_p', SideOption.LEFT, SideOption.FULL),
    ('airports_p', SideOption.RIGHT, SideOption.FULL),
    ('airports_p', SideOption.ONLY_OUTSIDE, SideOption.FULL),
])
def test_validate_side_option(world_features, fc_name, option, expected):
    """
    Test validate side option
    """
    source = world_features[fc_name]

    @validate_side_option('opt', 's')
    def diss_function(s, opt):
        return opt

    assert diss_function(source, option) == expected
# End test_validate_side_option function


@mark.parametrize('fc_name, option, expected', [
    ('admin_a', EndOption.ROUND, EndOption.ROUND),
    ('admin_a', EndOption.FLAT, EndOption.ROUND),
    ('admin_a', EndOption.SQUARE, EndOption.ROUND),
    ('rivers_l', EndOption.ROUND, EndOption.ROUND),
    ('rivers_l', EndOption.FLAT, EndOption.FLAT),
    ('rivers_l', EndOption.SQUARE, EndOption.SQUARE),
    ('airports_p', EndOption.ROUND, EndOption.ROUND),
    ('airports_p', EndOption.FLAT, EndOption.ROUND),
    ('airports_p', EndOption.SQUARE, EndOption.ROUND),
])
def test_validate_end_option(world_features, fc_name, option, expected):
    """
    Test validate end option
    """
    source = world_features[fc_name]

    @validate_end_option('opt', 's')
    def diss_function(s, opt):
        return opt

    assert diss_function(source, option) == expected
# End test_validate_end_option function


@mark.parametrize('fc_name, option, fields, expected, throws', [
    ('admin_a', DissolveOption.NONE, None, None, False),
    ('admin_a', DissolveOption.NONE, [], None, False),
    ('admin_a', DissolveOption.NONE, 'COUNTRY', None, False),
    ('admin_a', DissolveOption.NONE, ['COUNTRY'], None, False),
    ('admin_a', DissolveOption.ALL, None, None, False),
    ('admin_a', DissolveOption.ALL, [], None, False),
    ('admin_a', DissolveOption.ALL, 'COUNTRY', None, False),
    ('admin_a', DissolveOption.ALL, ['COUNTRY'], None, False),
    ('admin_a', DissolveOption.LIST, None, None, True),
    ('admin_a', DissolveOption.LIST, [], None, True),
    ('admin_a', DissolveOption.LIST, 'COUNTRY', [Field('COUNTRY', data_type='TEXT(50)')], False),
    ('admin_a', DissolveOption.LIST, ['COUNTRY'], [Field('COUNTRY', data_type='TEXT(50)')], False),
])
def test_validate_dissolve_option(world_features, fc_name, option, fields, expected, throws):
    """
    Test validate dissolve option
    """
    source = world_features[fc_name]

    @validate_field('flds', element_name='s', exclude_primary=False, is_optional=True)
    @validate_dissolve_option('opt', 'flds')
    def diss_function(s, opt, flds):
        return flds
    if throws:
        with raises(ValueError):
            diss_function(source, option, fields)
    else:
        assert diss_function(source, option, fields) == expected
# End test_validate_dissolve_option function


@mark.parametrize('name, attribute, throws', [
    ('toponymy_p', GeometryAttribute.POINT_X, False),
    ('toponymy_p', GeometryAttribute.POINT_Y, False),
    ('toponymy_p', GeometryAttribute.POINT_Z, True),
    ('toponymy_p', GeometryAttribute.POINT_M, True),
    ('toponymy_p', GeometryAttribute.PART_COUNT, True),
    ('toponymy_p', GeometryAttribute.CENTROID_X, True),
    ('toponymy_zm_p', GeometryAttribute.POINT_M, False),
    ('toponymy_mp', GeometryAttribute.POINT_X, True),
    ('toponymy_mp', GeometryAttribute.POINT_Z, True),
    ('toponymy_mp', GeometryAttribute.PART_COUNT, False),
    ('toponymy_mp', GeometryAttribute.CENTROID_X, False),
    ('toponymy_zm_mp', GeometryAttribute.POINT_M, True),
    ('transmission_l', GeometryAttribute.POINT_X, True),
    ('transmission_l', GeometryAttribute.CENTROID_X, False),
    ('transmission_l', GeometryAttribute.LENGTH, False),
    ('transmission_l', GeometryAttribute.LINE_AZIMUTH, False),
    ('transmission_l', GeometryAttribute.PERIMETER, True),
    ('transmission_l', GeometryAttribute.EXTENT_MAX_X, False),
    ('transmission_l', GeometryAttribute.EXTENT_MIN_Y, False),
    ('transmission_l', GeometryAttribute.EXTENT_MIN_Z, True),
    ('transmission_l', GeometryAttribute.INSIDE_X, False),
    ('transmission_zm_l', GeometryAttribute.LINE_END_X, False),
    ('hydro_a', GeometryAttribute.HOLE_COUNT, False),
    ('hydro_a', GeometryAttribute.PART_COUNT, False),
    ('hydro_a', GeometryAttribute.POINT_COUNT, False),
    ('hydro_a', GeometryAttribute.PERIMETER_GEODESIC, False),
    ('hydro_a', GeometryAttribute.LINE_START_X, True),
])
def test_validate_geometry_attribute(ntdb_zm_small, name, attribute, throws):
    """
    Test validate geometry attribute
    """
    source = ntdb_zm_small[name]
    @validate_geometry_attribute()
    def geom_function(source, geometry_attribute):
        return geometry_attribute

    if throws:
        with raises(ValueError):
            geom_function(source, attribute)
    else:
        assert geom_function(source, attribute) == attribute
# End test_validate_geometry_attribute function


if __name__ == '__main__':  # pragma: no cover
    pass
