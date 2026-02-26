# -*- coding: utf-8 -*-
"""
Test for Validation used on Enumeration-esque values
"""


from pytest import raises, mark

from spyops.shared.enumeration import (
    AttributeOption, GeometryAttribute, OutputTypeOption)
from spyops.shared.exception import OperationsError
from spyops.validation import (
    validate_str_enumeration, validate_geometry_attribute, validate_output_type)


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
    @validate_output_type('option', 's')
    def geom_function(s, o, option):
        return option

    if throws:
        with raises(OperationsError):
            geom_function(source, operator, option)
    else:
        assert geom_function(source, operator, option) == option
# End test_validate_output_type function


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
