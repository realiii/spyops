# -*- coding: utf-8 -*-
"""
Utilities
"""


from sqlite3 import OperationalError

from geomio.shared.exception import OperationsError
from geomio.shared.hint import ELEMENT
from geomio.shared.util import add_spatial_index


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
    return add_spatial_index(element)
# End shared_select function


if __name__ == '__main__':  # pragma: no cover
    pass
