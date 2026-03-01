# -*- coding: utf-8 -*-
"""
Constants
"""


from pathlib import Path


SKIP_FILE_PREFIXES: tuple[str, ...] = str(Path(__file__).parent.parent),


QUESTION: str = '?'
PIPE: str = '|'
SPACE: str = ' '
EMPTY: str = ''
COLON: str = ':'
PLUS: str = '+'
DOT: str = '.'
UNDERSCORE: str = '_'
DOUBLE_UNDER: str = f'{UNDERSCORE}{UNDERSCORE}'
PADDED_PIPE: str = f'{SPACE}{PIPE}{SPACE}'


SRS_ID_WKB: int = -1  # used where only need WKB


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
INCLUDE_VERTICAL_KEY: str = 'include_vertical'
TRANSFORMER_KEY: str = 'transformer'


DEGREE: str = 'degree'
METRE: str = 'metre'


FIELD: str = 'field'
FIELD_PROPERTY: str = 'field_property'
FIELDS_ARG: str = 'fields'
ELEMENTS_ARG: str = 'elements'
SOURCE: str = 'source'
OPERATOR: str = 'operator'
TARGET: str = 'target'
GEOPACKAGE: str = 'geopackage'
GROUP_FIELDS: str = 'group_fields'
INDEX_FIELDS: str = 'index_fields'
ATTRIBUTE_OPTION: str = 'attribute_option'
ALGORITHM_OPTION: str = 'algorithm_option'
WEIGHT_OPTION: str = 'weight_option'
CHECK_OPTIONS: str = 'check_options'
OUTPUT_TYPE_OPTION: str = 'output_type_option'
GEOMETRY_ATTRIBUTE: str = 'geometry_attribute'
LENGTH_UNIT: str = 'length_unit'
AREA_UNIT: str = 'area_unit'


TEMP_SCHEMA: str = 'temp'
ROWID: str = 'ROWID'
SQL_NO_ID: str = f"""{ROWID} <= -1"""
SQL_ALL_ID: str = f"""{ROWID} > -1"""

IN: str = 'IN'
NOT_IN: str = 'NOT IN'

if __name__ == '__main__':  # pragma: no cover
    pass
