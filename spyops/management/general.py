# -*- coding: utf-8 -*-
"""
General Data Management
"""


from spyops.environment import OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.shared.constant import SOURCE, TARGET
from spyops.shared.element import copy_element
from spyops.shared.hint import ELEMENT, ELEMENTS
from spyops.validation import (
    validate_element, validate_elements, validate_overwrite_input,
    validate_target_element)


__all__ = ['copy', 'delete']


@validate_element(SOURCE, has_content=False)
@validate_target_element()
@validate_overwrite_input(TARGET, SOURCE)
def copy(source: ELEMENT, target: ELEMENT) -> ELEMENT:
    """
    Copy Table or Feature Class

    Copies a source table to a target table or source feature class
    to a target feature class.  This function only honors the
    workspace-related analysis settings.
    """
    with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, None),
          Swap(Setting.GEOGRAPHIC_TRANSFORMATIONS, []),
          Swap(Setting.EXTENT, None), Swap(Setting.Z_VALUE, None),
          Swap(Setting.OUTPUT_M_OPTION, OutputMOption.SAME),
          Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.SAME)):
        element = copy_element(source=source, target=target)
    return element
# End copy function


@validate_elements(SOURCE, has_content=False)
def delete(source: ELEMENT | ELEMENTS) -> bool:
    """
    Delete Table(s) and/or Feature Class(es)
    """
    if not source:
        return False
    for element in source:
        element.drop()
    return True
# End delete function


if __name__ == '__main__':  # pragma: no cover
    pass
