# -*- coding: utf-8 -*-
"""
Base Classes
"""


from typing import NamedTuple, TYPE_CHECKING


if TYPE_CHECKING:  # pragma: no cover
    from pyproj.transformer import Transformer


class TransformerRecord(NamedTuple):
    """
    Transformer Record
    """
    is_best: bool
    transform: 'Transformer'
    label: str
# End TransformerRecord class


if __name__ == '__main__':  # pragma: no cover
    pass
