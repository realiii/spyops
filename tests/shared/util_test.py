# -*- coding: utf-8 -*-
"""
Test Utilities
"""


from fudgeo.geometry import Point
from numpy import array

from pytest import approx, mark, raises

from spyops.environment.enumeration import OutputMOption
from spyops.shared.enumeration import DEFAULT_GEOM_CHECKS, GeometryCheck
from spyops.shared.util import (
    check_int_flag_enum, check_str_enum, element_names, expand_extent,
    find_slice_indexes, get_smallest_indexes, get_smallest_values,
    make_unique_name, make_valid_field_name, make_valid_table_name,
    _replace_double_under, nada, safe_float, safe_int)


pytestmark = [mark.utility]


@mark.parametrize('name, expected1, expected2', [
    ('admin', 'admin_1', 'admin_2'),
    ('lmnop', 'lmnop', 'lmnop_1'),
])
def test_make_unique_name(world_tables, name, expected1, expected2):
    """
    Test make_unique_name
    """
    names = element_names(world_tables)
    assert make_unique_name(name, names=names) == expected1
    names.add(expected1)
    assert make_unique_name(name, names=names) == expected2
# End test_make_unique_name function


@mark.parametrize('name, expected', [
    ('', 'empty'),
    ('   ', 'empty'),
    (None, 'none'),
    ('__', 'fc'),
    ('||', 'fc'),
    ('aaa||bbb', 'aaa_bbb'),
    ('1234_asdf', 'fc_1234_asdf'),
    ('q_group 1', 'q_group_1'),
])
def test_make_valid_table_name(name, expected):
    """
    Test make_valid_table_name
    """
    assert make_valid_table_name(name, prefix='fc') == expected
# End test_make_valid_table_name function


def test_replace_double_under():
    """
    Test for _replace_double_under
    """
    assert _replace_double_under('____init____') == '_init_'
# End test_replace_double_under function


def test_expand_extent():
    """
    Test expand extent
    """
    min_value = 10_000_000
    max_value = 10_000_000
    min_x, min_y, max_x, max_y = expand_extent((
        min_value, min_value, max_value, max_value))
    assert min_x == min_y
    assert approx(min_x, abs=0.001) == 9_999_998.75
    assert max_x == max_y
    assert approx(max_x, abs=0.001) == 10_000_001.25
# End test_expand_extent function


@mark.parametrize('value, expected', [
    (None, None),
    (1, 1),
    (1.1, 1),
    ('1', 1),
    ('2.1', 2),
    ('abc', None),
    ('abc123', None),
    ('123abc', None),
])
def test_safe_int(value, expected):
    """
    Test safe_int
    """
    assert safe_int(value) == expected
# End test_safe_int function


@mark.parametrize('value, expected', [
    (None, None),
    (1, 1.),
    ('1', 1.),
    ('1.1', 1.1),
    ('abc', None),
    ('abc123', None),
    ('123abc', None),
])
def test_safe_float(value, expected):
    """
    Test safe_float
    """
    assert safe_float(value) == expected
# End test_safe_float function


@mark.parametrize('value, enum, expected, throws', [
    (None, OutputMOption, None, True),
    ('same', OutputMOption, OutputMOption.SAME, False),
    (OutputMOption.SAME, OutputMOption, OutputMOption.SAME, False),
])
def test_check_str_enum(value, enum, expected, throws):
    """
    Test check_str_enum
    """
    if throws:
        with raises(ValueError):
            check_str_enum(value, enum)
    else:
        assert check_str_enum(value, enum) == expected
# End test_check_str_enum function


@mark.parametrize('value, enum, expected, throws', [
    (None, GeometryCheck, None, True),
    (1, GeometryCheck, GeometryCheck.EXTENT, False),
    ('extent', GeometryCheck, GeometryCheck.EXTENT, True),
    (GeometryCheck.EXTENT, GeometryCheck, GeometryCheck.EXTENT, False),
    (GeometryCheck.EXTENT | GeometryCheck.EMPTY, GeometryCheck, 3, False),
    (GeometryCheck.EXTENT | GeometryCheck.EMPTY, GeometryCheck, GeometryCheck.EXTENT | GeometryCheck.EMPTY, False),
    (DEFAULT_GEOM_CHECKS, GeometryCheck, DEFAULT_GEOM_CHECKS, False),
])
def test_check_int_flag_enum(value, enum, expected, throws):
    """
    Test check_int_flag_enum
    """
    if throws:
        with raises(ValueError):
            check_int_flag_enum(value, enum)
    else:
        assert check_int_flag_enum(value, enum) == expected
# End test_check_int_flag_enum function


@mark.parametrize('name, expected', [
    ('HAPPY_PATH', 'HAPPY_PATH'),
    ('CONSTRAINT', 'FIELD_CONSTRAINT'),
    ('', 'FIELD'),
    ('_', 'FIELD'),
    ('__', 'FIELD'),
    ('___', 'FIELD'),
    ('123', 'FIELD_123'),
    ('_123_', 'FIELD_123'),
    ('##$_999', 'FIELD_999'),
    ('FID', 'FID_1'),
])
def test_make_valid_field_name(name, expected):
    """
    Test make valid field name
    """
    assert make_valid_field_name(name) == expected
# End test_make_valid_field_name function


@mark.parametrize('indexes, expected', [
    ([], ()),
    ([0, 0, 0, 0], (0, 4)),
    ([0, 0, 1, 1], (0, 2, 4)),
    ([0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2], (0, 3, 8, 12)),
])
def test_find_slice_indexes(indexes, expected):
    """
    Test find_slice_indexes
    """
    assert find_slice_indexes(array(indexes, dtype=int)) == expected
# End test_find_slice_indexes function


@mark.parametrize('ids, values, n, unique, mins', [
    ([], [], 2, [], []),
    ([0], [1.1], 2, [0], [1.1]),
    ([0, 0, 1, 1, 1], [1.1, 2, 1.2, 4.2, 3.3], 2, [0, 0, 1, 1], [1.1, 2, 1.2, 3.3]),
    ([0, 0, 1, 1, 1], [1.1, 2, 1.2, 4.2, 3.3], 3, [0, 0, 1, 1, 1], [1.1, 2, 1.2, 3.3, 4.2]),
])
def test_get_smallest_values(ids, values, n, unique, mins):
    """
    Test get smallest in group
    """
    ids = array(ids)
    values = array(values)
    unique_ids, smallest = get_smallest_values(ids=ids, values=values, n=n)
    assert unique_ids.tolist() == unique
    assert approx(smallest.tolist(), abs=0.001, nan_ok=True) == mins
# End test_get_smallest_values function


@mark.parametrize('ids, values, n, unique, mins', [
    ([], [], 2, [], []),
    ([0], [1.1], 2, [0], [0]),
    ([0, 0, 1, 1, 1], [1.1, 2, 1.2, 4.2, 3.3], 2, [0, 0, 1, 1], [0, 1, 2, 4]),
    ([0, 0, 1, 1, 1], [1.1, 2, 1.2, 4.2, 3.3], 3, [0, 0, 1, 1, 1], [0, 1, 2, 4, 3]),
    ([1, 1, 0, 1, 0], [1.1, 2, 1.2, 4.2, 3.3], 3, [0, 0, 1, 1, 1], [2, 4, 0, 1, 3]),
])
def test_get_smallest_indexes(ids, values, n, unique, mins):
    """
    Test get smallest in group, returning indexes
    """
    ids = array(ids)
    values = array(values)
    unique_ids, smallest = get_smallest_indexes(ids=ids, values=values, n=n)
    assert unique_ids.tolist() == unique
    assert smallest.tolist() == mins
# End test_get_smallest_indexes function


@mark.parametrize('value, expected', [
    (None, None),
    (2, 2),
    (Point, Point),
])
def test_nada(value, expected):
    """
    Test
    """
    assert nada(value) == expected
# End test_nada function


if __name__ == '__main__':  # pragma: no cover
    pass
