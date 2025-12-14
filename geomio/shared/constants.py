# -*- coding: utf-8 -*-
"""
Constants
"""


QUESTION: str = '?'
PIPE: str = '|'
SPACE: str = ' '
UNDERSCORE: str = '_'
DOUBLE_UNDER: str = f'{UNDERSCORE}{UNDERSCORE}'
PADDED_PIPE: str = f'{SPACE}{PIPE}{SPACE}'


GEOMS_ATTR: str = 'geoms'
NAME_ATTR: str = 'name'

SOURCE: str = 'source'
OPERATOR: str = 'operator'
TARGET: str = 'target'
GEOPACKAGE: str = 'geopackage'


XY_TOLERANCE: str = 'xy_tolerance'
OVERWRITE: str = 'overwrite'


SQL_EMPTY: str = """ROWID <= -1"""
SQL_FULL: str = """ROWID > -1"""


UNSUPPORTED_WKT: str = 'Unsupported WKT: {}'
EMPTY_INPUT: str = '{}: {} is empty'


if __name__ == '__main__':  # pragma: no cover
    pass
