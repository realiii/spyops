# -*- coding: utf-8 -*-
"""
Utility Functions
"""

from typing import NamedTuple

from gisworks.environment import ANALYSIS_SETTINGS
from gisworks.environment.enumeration import OutputMOption, OutputZOption


class ZMConfig(NamedTuple):
    """
    ZM Configuration
    """
    is_different: bool
    z_enabled: bool
    m_enabled: bool
# End ZMConfig class


def zm_config(has_z: bool, has_m: bool) -> ZMConfig:
    """
    Get ZM Configuration
    """
    z_enabled = _z_enabled(has_z)
    m_enabled = _m_enabled(has_m)
    is_different = z_enabled != has_z or m_enabled != has_m
    return ZMConfig(
        is_different=is_different, z_enabled=z_enabled, m_enabled=m_enabled)
# End zm_config function


def _z_enabled(has_z: bool) -> bool:
    """
    Z Enabled
    """
    if ANALYSIS_SETTINGS.output_z_option == OutputZOption.SAME:
        return has_z
    return ANALYSIS_SETTINGS.output_z_option == OutputZOption.ENABLED
# End _z_enabled function


def _m_enabled(has_m: bool) -> bool:
    """
    M Enabled
    """
    if ANALYSIS_SETTINGS.output_m_option == OutputMOption.SAME:
        return has_m
    return ANALYSIS_SETTINGS.output_m_option == OutputMOption.ENABLED
# End _m_enabled function


if __name__ == '__main__':  # pragma: no cover
    pass
