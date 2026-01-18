# -*- coding: utf-8 -*-
"""
Utility Functions
"""

from spyops.environment.enumeration import Setting
from spyops.shared.constant import EMPTY, SPACE, UNDERSCORE


def as_title(setting: Setting | str | None) -> str:
    """
    Change a setting enumeration value to a title text for exceptions
    """
    if setting is None:
        return EMPTY
    if setting == Setting.XY_TOLERANCE:
        return 'XY Tolerance'
    return str(setting).replace(UNDERSCORE, SPACE).title()
# End as_title function


if __name__ == '__main__':  # pragma: no cover
    pass
