# -*- coding: utf-8 -*-
"""
Tests for Geometry Convert Module
"""

from pytest import mark

from gisworks.geometry.convert import (
    _as_lines, _use_boundary_factory, get_geometry_converters)
from gisworks.geometry.util import nada
from gisworks.shared.enumeration import OutputTypeOption


pytestmark = [mark.geometry]


@mark.parametrize('output_type_option, source_name, operator_name, expected', [
    (OutputTypeOption.SAME, 'utmzone_sparse_a', 'intersect_a', (False, False)),
    (OutputTypeOption.LINE, 'utmzone_sparse_a', 'intersect_a', (True, True)),
    (OutputTypeOption.POINT, 'utmzone_sparse_a', 'intersect_a', (True, True)),
    (OutputTypeOption.SAME, 'rivers_portion_l', 'intersect_a', (False, False)),
    (OutputTypeOption.LINE, 'rivers_portion_l', 'intersect_a', (False, False)),
    (OutputTypeOption.POINT, 'rivers_portion_l', 'intersect_a', (False, True)),
    (OutputTypeOption.SAME, 'river_p', 'intersect_a', (False, False)),
    (OutputTypeOption.POINT, 'river_p', 'intersect_a', (False, False)),

    (OutputTypeOption.SAME, 'rivers_portion_l', 'rivers_portion_l', (False, False)),
    (OutputTypeOption.LINE, 'rivers_portion_l', 'rivers_portion_l', (False, False)),
    (OutputTypeOption.POINT, 'rivers_portion_l', 'rivers_portion_l', (False, False)),
    (OutputTypeOption.POINT, 'river_p', 'rivers_portion_l', (False, False)),

    (OutputTypeOption.SAME, 'river_p', 'river_p', (False, False)),
    (OutputTypeOption.POINT, 'river_p', 'river_p', (False, False)),
])
def test_use_boundary_factory(inputs, output_type_option, source_name, operator_name, expected):
    """
    Test _use_boundary_factory, not all cases are tested here because
    there is a reliance on validate_output_type to prevent invalid combinations
    from getting into the factory.
    """
    source = inputs[source_name]
    operator = inputs[operator_name]
    assert _use_boundary_factory(
        source.shape_type, operator_shape_type=operator.shape_type,
        output_type_option=output_type_option) == expected
# End test_use_boundary_factory function


@mark.parametrize('output_type_option, source_name, operator_name, expected', [
    (OutputTypeOption.SAME, 'utmzone_sparse_a', 'intersect_a', (nada, nada)),
    (OutputTypeOption.LINE, 'utmzone_sparse_a', 'intersect_a', (_as_lines, _as_lines)),
    (OutputTypeOption.POINT, 'utmzone_sparse_a', 'intersect_a', (_as_lines, _as_lines)),
    (OutputTypeOption.SAME, 'rivers_portion_l', 'intersect_a', (nada, nada)),
    (OutputTypeOption.LINE, 'rivers_portion_l', 'intersect_a', (nada, nada)),
    (OutputTypeOption.POINT, 'rivers_portion_l', 'intersect_a', (nada, _as_lines)),
    (OutputTypeOption.SAME, 'river_p', 'intersect_a', (nada, nada)),
    (OutputTypeOption.POINT, 'river_p', 'intersect_a', (nada, nada)),

    (OutputTypeOption.SAME, 'rivers_portion_l', 'rivers_portion_l', (nada, nada)),
    (OutputTypeOption.LINE, 'rivers_portion_l', 'rivers_portion_l', (nada, nada)),
    (OutputTypeOption.POINT, 'rivers_portion_l', 'rivers_portion_l', (nada, nada)),
    (OutputTypeOption.POINT, 'river_p', 'rivers_portion_l', (nada, nada)),

    (OutputTypeOption.SAME, 'river_p', 'river_p', (nada, nada)),
    (OutputTypeOption.POINT, 'river_p', 'river_p', (nada, nada)),
])
def test_get_geometry_converters(inputs, output_type_option, source_name, operator_name, expected):
    """
    Test get_geometry_converters
    """
    source = inputs[source_name]
    operator = inputs[operator_name]
    assert get_geometry_converters(source, operator=operator, output_type_option=output_type_option) == expected
# End test_get_geometry_converters function


if __name__ == '__main__':  # pragma: no cover
    pass
