# -*- coding: utf-8 -*-
"""
Test for Validation used on Enumeration-esque values
"""


from pytest import raises, mark

from spyops.shared.enumeration import AttributeOption, OutputTypeOption
from spyops.shared.exception import OperationsError
from spyops.validation import validate_enumeration, validate_output_type


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
    @validate_enumeration('option', AttributeOption)
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


if __name__ == '__main__':  # pragma: no cover
    pass
