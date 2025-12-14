# -*- coding: utf-8 -*-
"""
Test Utilities
"""


from pytest import mark

from geomio.shared.util import (
    element_names, make_unique_name, make_valid_name, _replace_double_under)


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


if __name__ == '__main__':  # pragma: no cover
    pass
