# -*- coding: utf-8 -*-
"""
Test Utilities
"""


from pytest import approx, mark, raises

from gisworks.environment.enumeration import OutputMOption
from gisworks.shared.util import (
    check_enumeration, element_names, expand_extent, make_unique_name,
    make_valid_name, _replace_double_under, safe_float, safe_int)


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
def test_make_valid_name(name, expected):
    """
    Test make_valid_name
    """
    assert make_valid_name(name, prefix='fc') == expected
# End test_make_valid_name function


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
def test_check_enumeration(value, enum, expected, throws):
    """
    Test check_enumeration
    """
    if throws:
        with raises(ValueError):
            check_enumeration(value, enum)
    else:
        assert check_enumeration(value, enum) == expected
# End test_check_enumeration function


if __name__ == '__main__':  # pragma: no cover
    pass
