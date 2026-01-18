# -*- coding: utf-8 -*-
"""
Test for Utility Functions
"""


from pytest import mark

from gisworks.environment.enumeration import Setting
from gisworks.environment.util import as_title


pytestmark = [mark.environment]


@mark.parametrize('value, expected', [
    (Setting.XY_TOLERANCE, 'XY Tolerance'),
    (Setting.OVERWRITE, 'Overwrite'),
    (Setting.CURRENT_WORKSPACE, 'Current Workspace'),
    (Setting.OUTPUT_Z_OPTION, 'Output Z Option'),
    (Setting.Z_VALUE, 'Z Value'),
    (Setting.OUTPUT_M_OPTION, 'Output M Option'),
    ('asdf', 'Asdf'),
    (None, ''),
])
def test_as_title(value, expected):
    """
    Test as_title
    """
    assert as_title(value) == expected
# End test_as_title function


if __name__ == '__main__':  # pragma: no cover
    pass
