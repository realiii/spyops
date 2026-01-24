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
POLYGONS_ATTR: str = 'polygons'
LINES_ATTR: str = 'lines'
POINTS_ATTR: str = 'points'
X_ATTR: str = 'x'
Y_ATTR: str = 'y'
Z_ATTR: str = 'z'
M_ATTR: str = 'm'

INCLUDE_Z: str = 'include_z'
INCLUDE_M: str = 'include_m'

HAS_Z_KEY: str = 'has_z'
HAS_M_KEY: str = 'has_m'
SRS_ID_KEY: str = 'srs_id'

FIELD: str = 'field'
SOURCE: str = 'source'
OPERATOR: str = 'operator'
TARGET: str = 'target'
GEOPACKAGE: str = 'geopackage'
GROUP_FIELDS: str = 'group_fields'
ATTRIBUTE_OPTION: str = 'attribute_option'
ALGORITHM_OPTION: str = 'algorithm_option'
OUTPUT_TYPE_OPTION: str = 'output_type_option'

ROWID: str = 'ROWID'
SQL_EMPTY: str = f"""{ROWID} <= -1"""
SQL_FULL: str = f"""{ROWID} > -1"""

IN: str = 'IN'
NOT_IN: str = 'NOT IN'

UNSUPPORTED_WKT: str = 'Unsupported WKT: {}'
EMPTY_INPUT: str = '{}: {} is empty'
UNABLE_TO_USE_CRS: str = 'Unable to use authority and code from {}'
UNSUPPORTED_CRS: str = 'Unsupported CRS authority ({}) or code ({})'
CRS_REQUIRED: str = 'A coordinate reference system is required'
NO_TRANSFORMER: str = (
    'No valid transformation exists for CRS {} ({}) and CRS {} ({})')
INVALID_AOI: str = (
    'The area of use "{}" does not intersect with the area of interest')


BASE_TABLES: set[str] = {'gpkg_spatial_ref_sys', 'gpkg_contents',
                         'gpkg_geometry_columns', 'gpkg_tile_matrix_set',
                         'gpkg_tile_matrix', 'gpkg_extensions'}


if __name__ == '__main__':  # pragma: no cover
    pass
