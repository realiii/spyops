# -*- coding: utf-8 -*-
"""
Base Classes
"""


from typing import NamedTuple, Optional, TYPE_CHECKING


if TYPE_CHECKING:  # pragma: no cover
    from pyproj.transformer import Transformer


class TransformOption(NamedTuple):
    """
    Transform Option
    """
    is_best: bool
    accuracy: float | None
    transformer: 'Transformer'
# End TransformOption class


class TransformOptions(NamedTuple):
    """
    Transform Options
    """
    is_required: bool
    best: Optional['Transformer']
    options: list['TransformOption']
# End TransformOptions class


if __name__ == '__main__':  # pragma: no cover
    pass
