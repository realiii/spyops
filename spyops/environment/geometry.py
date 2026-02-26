# -*- coding: utf-8 -*-
"""
Geometry Dimensions Settings
"""


from math import isnan, nan

from spyops.environment.enumeration import OutputMOption, OutputZOption
from spyops.shared.hint import XY_TOL
from spyops.shared.util import check_str_enum, safe_float


class _GeometryDimensions:
    """
    Geometry Dimensions
    """
    def __init__(self) -> None:
        """
        Initialize the _GeometryDimensions class
        """
        super().__init__()
        self._xy: XY_TOL = None
        self._z_option: OutputZOption = OutputZOption.SAME
        self._z_value: float = nan
        self._m_option: OutputMOption = OutputMOption.SAME
    # End init built-in

    @property
    def xy_tolerance(self) -> XY_TOL:
        """
        XY Tolerance
        """
        return self._xy

    @xy_tolerance.setter
    def xy_tolerance(self, value: XY_TOL) -> None:
        value = safe_float(value)
        if isinstance(value, float) and isnan(value):
            value = None
        self._xy = value
    # End xy_tolerance property

    @property
    def output_z_option(self) -> OutputZOption:
        """
        Output Z Option
        """
        return self._z_option

    @output_z_option.setter
    def output_z_option(self, value: OutputZOption) -> None:
        self._z_option = check_str_enum(value, enum=OutputZOption)
    # End output_z_option property

    @property
    def output_m_option(self) -> OutputMOption:
        """
        Output M Option
        """
        return self._m_option

    @output_m_option.setter
    def output_m_option(self, value: OutputMOption) -> None:
        self._m_option = check_str_enum(value, enum=OutputMOption)
    # End output_m_option property

    @property
    def z_value(self) -> float:
        """
        Z Value
        """
        return self._z_value

    @z_value.setter
    def z_value(self, value: float) -> None:
        if (value := safe_float(value)) is None:
            value = nan
        self._z_value = value
    # End z_value property
# End _GeometryDimensions class


if __name__ == '__main__':  # pragma: no cover
    pass
