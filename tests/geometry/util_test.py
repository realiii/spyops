# -*- coding: utf-8 -*-
"""
Tests for Geometry Util Module
"""


from fudgeo.geometry.point import Point
from pytest import mark

from gisworks.geometry.util import nada


pytestmark = [mark.geometry]


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
