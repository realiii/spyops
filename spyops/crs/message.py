# -*- coding: utf-8 -*-
"""
Messages
"""


UNSUPPORTED_WKT: str = 'Unsupported WKT: {}'
EMPTY_INPUT: str = '{}: {} is empty'
UNABLE_TO_USE_CRS: str = 'Unable to use authority and code from {}'
UNSUPPORTED_CRS: str = 'Unsupported CRS authority ({}) or code ({})'
CRS_REQUIRED: str = 'A coordinate reference system is required'
NO_TRANSFORMER: str = (
    'No valid transformation exists for CRS {} ({}) and CRS {} ({})')
INVALID_AOI: str = (
    'The area of use "{}" does not intersect with the area of interest')


if __name__ == '__main__':  # pragma: no cover
    pass
