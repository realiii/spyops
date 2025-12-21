# -*- coding: utf-8 -*-
"""
Constants
"""


QUESTION: str = '?'
PIPE: str = '|'
SPACE: str = ' '
EMPTY: str = ''
COLON: str = ':'
PLUS: str = '+'
UNDERSCORE: str = '_'
DOUBLE_UNDER: str = f'{UNDERSCORE}{UNDERSCORE}'
PADDED_PIPE: str = f'{SPACE}{PIPE}{SPACE}'


UNKNOWN: str = 'Unknown'
UNDEFINED: str = 'Undefined'
BAD_SRS_DEFINITIONS: tuple[str, str] = UNDEFINED.casefold(), UNKNOWN.casefold()
ZERO_STR: str = '0'
CUSTOM_RANGE_START: int = 300_000
CUSTOM: str = 'Custom'
CUSTOM_UPPER: str = CUSTOM.upper()
NONE: str = 'NONE'
EPSG: str = 'EPSG'
ESRI: str = 'ESRI'


ID_KEY: str = 'id'
AUTHORITY_KEY: str = 'authority'
CODE_KEY: str = 'code'


GEOMS_ATTR: str = 'geoms'
NAME_ATTR: str = 'name'

FIELD: str = 'field'
SOURCE: str = 'source'
OPERATOR: str = 'operator'
TARGET: str = 'target'
GEOPACKAGE: str = 'geopackage'
GROUP_FIELDS: str = 'group_fields'


SQL_EMPTY: str = """ROWID <= -1"""
SQL_FULL: str = """ROWID > -1"""


UNSUPPORTED_WKT: str = 'Unsupported WKT: {}'
EMPTY_INPUT: str = '{}: {} is empty'
UNABLE_TO_USE_CRS: str = 'Unable to use authority and code from {}'


BASE_TABLES: set[str] = {'gpkg_spatial_ref_sys', 'gpkg_contents',
                         'gpkg_geometry_columns', 'gpkg_tile_matrix_set',
                         'gpkg_tile_matrix', 'gpkg_extensions'}


if __name__ == '__main__':  # pragma: no cover
    pass
