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
COMMA: str = ','
UNDERSCORE: str = '_'
DOUBLE_UNDER: str = f'{UNDERSCORE}{UNDERSCORE}'
PADDED_PIPE: str = f'{SPACE}{PIPE}{SPACE}'


SRS_ID_WKB: int = -1  # used where only need WKB


SPYOPS: str = 'spyops'
DRID: str = '__DRID__'
VALUE: str = 'value'

DEGREE: str = 'degree'
METRE: str = 'metre'

EXT_GPX: str = 'gpx'
EXT_GEOJSON: str = 'geojson'


FEATURE: str = 'Feature'
FEATURE_COLLECTION: str = 'FeatureCollection'


if __name__ == '__main__':  # pragma: no cover
    pass
