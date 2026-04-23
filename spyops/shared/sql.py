# -*- coding: utf-8 -*-
"""
SQL
"""


TEMP_SCHEMA: str = 'temp'
ROWID: str = 'ROWID'
SQL_NO_ID: str = f"""{ROWID} <= -1"""
SQL_ALL_ID: str = f"""{ROWID} > -1"""
IN: str = 'IN'
NOT_IN: str = 'NOT IN'


if __name__ == '__main__':  # pragma: no cover
    pass
