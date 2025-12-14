# -*- coding: utf-8 -*-
"""
Utilities
"""


from sqlite3 import OperationalError

from geomio.shared.exceptions import OperationsError
from geomio.shared.hints import ELEMENT


def shared_select(source: ELEMENT, target: ELEMENT, where_clause: str,
                  overwrite: bool) -> ELEMENT:
    """
    Common code for Table Select and Select functions
    """
    try:
        element = source.copy(
            name=target.name, geopackage=target.geopackage,
            description=target.description, where_clause=where_clause,
            overwrite=overwrite)
    except (OperationalError, ValueError) as err:
        raise OperationsError(err)
    return element
# End shared_select function


if __name__ == '__main__':  # pragma: no cover
    pass
