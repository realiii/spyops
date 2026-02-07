# -*- coding: utf-8 -*-
"""
Data Management for Tables
"""


from spyops.shared.constant import SOURCE
from spyops.shared.hint import ELEMENT
from spyops.validation import validate_element


@validate_element(SOURCE, has_content=False)
def get_count(source: ELEMENT) -> int:
    """
    Get Count

    Number of rows in a table or feature class
    """
    return len(source)
# End get_count function


if __name__ == '__main__':  # pragma: no cover
    pass
