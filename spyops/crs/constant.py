# -*- coding: utf-8 -*-
"""
Constants
"""


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


if __name__ == '__main__':  # pragma: no cover
    pass
