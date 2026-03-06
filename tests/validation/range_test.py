# -*- coding: utf-8 -*-
"""
Test Validation Range
"""

from pytest import mark, raises

from spyops.validation import validate_range


pytestmark = [mark.validation]


@mark.parametrize('value, inclusive, clamp, expected, throws', [
    (None, True, True, 10, False),
    (0, True, True, 0., False),
    (-10, True, True, 0., False),
    ('10', True, True, 10., False),
    (None, False, False, 10, False),
    (0, False, False, 0., True),
    (-10, False, False, 0., True),
    ('10', False, False, 10., False),
    (None, False, True, 10, False),
    (0, False, True, 0., False),
    (-10, False, True, 0., False),
    ('10', False, True, 10., False),
    (None, True, False, 10, False),
    (0, True, False, 0., False),
    (-10, True, False, 0., True),
    ('10', True, False, 10., False),
])
def test_validate_range(value, expected, inclusive, clamp, throws):
    """
    Test validate range
    """
    @validate_range('a', default=10, max_value=100, type_=int,
                    inclusive=inclusive, clamp=clamp)
    def range_function(a: int = 20):
        return a
    if throws:
        with raises(ValueError):
            range_function(value)
    else:
        assert range_function(value) == expected
# End test_validate_range function


if __name__ == '__main__':  # pragma: no cover
    pass
