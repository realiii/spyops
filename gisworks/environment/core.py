# -*- coding: utf-8 -*-
"""
Environment / Analysis Settings
"""
from typing import NamedTuple

from gisworks.environment.workspace import _Workspace
from gisworks.environment.geometry import _GeometryDimensions
from gisworks.environment.enumeration import OutputMOption, OutputZOption
from gisworks.shared.hint import GPKG, XY_TOL


class _AnalysisSettings:
    """
    Analysis Settings
    """
    __slots__ = ['_overwrite', '_dimensions', '_workspace']

    def __init__(self) -> None:
        """
        Initialize the _AnalysisSettings class
        """
        super().__init__()
        self._overwrite: bool = False
        self._dimensions: _GeometryDimensions = _GeometryDimensions()
        self._workspace: _Workspace = _Workspace()
    # End init built-in

    @property
    def overwrite(self) -> bool:
        """
        Overwrite
        """
        return self._overwrite

    @overwrite.setter
    def overwrite(self, value: bool) -> None:
        self._overwrite = bool(value)
    # End overwrite property

    @property
    def xy_tolerance(self) -> XY_TOL:
        """
        XY Tolerance
        """
        return self._dimensions.xy_tolerance

    @xy_tolerance.setter
    def xy_tolerance(self, value: XY_TOL) -> None:
        self._dimensions.xy_tolerance = value
    # End xy_tolerance property

    @property
    def output_z_option(self) -> OutputZOption:
        """
        Output Z Option
        """
        return self._dimensions.output_z_option

    @output_z_option.setter
    def output_z_option(self, value: OutputZOption) -> None:
        self._dimensions.output_z_option = value
    # End output_z_option property

    @property
    def z_value(self) -> float:
        """
        Z Value
        """
        return self._dimensions.z_value

    @z_value.setter
    def z_value(self, value: float) -> None:
        self._dimensions.z_value = value
    # End z_value property

    @property
    def output_m_option(self) -> OutputMOption:
        """
        Output M Option
        """
        return self._dimensions.output_m_option

    @output_m_option.setter
    def output_m_option(self, value: OutputMOption) -> None:
        self._dimensions.output_m_option = value
    # End output_m_option property

    @property
    def current_workspace(self) -> GPKG | None:
        """
        Current Workspace
        """
        return self._workspace.current

    @current_workspace.setter
    def current_workspace(self, value: GPKG | None) -> None:
        self._workspace.current = value
    # End current_workspace property

    @property
    def scratch_workspace(self) -> GPKG | None:
        """
        Scratch Workspace
        """
        return self._workspace.scratch

    @scratch_workspace.setter
    def scratch_workspace(self, value: GPKG | None) -> None:
        self._workspace.scratch = value
    # End scratch_workspace property
# End _AnalysisSettings class


ANALYSIS_SETTINGS: _AnalysisSettings = _AnalysisSettings()


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
