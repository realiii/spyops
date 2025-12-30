# -*- coding: utf-8 -*-
"""
Database Functionality
"""


from pathlib import Path
from sqlite3 import Connection, DatabaseError, OperationalError, connect

from geomio.shared.constant import BASE_TABLES


def is_geopackage(path: Path | str) -> bool:
    """
    Is Geopackage?
    """
    if not path:
        return False
    path = Path(path)
    if not path.is_file():
        return False
    try:
        conn = connect(path)
    except OperationalError:  # pragma: no cover
        return False
    if not _is_sqlite(connection=conn):
        conn.close()
        return False
    if not _is_geopackage(connection=conn):
        conn.close()
        return False
    conn.close()
    return True
# End is_geopackage method


def _is_sqlite(connection: Connection) -> bool:
    """
    Check if a file is an SQLite database
    """
    try:
        connection.execute("""PRAGMA quick_check(sqlite_master)""")
    except (DatabaseError, OperationalError):
        return False
    return True
# End _is_sqlite function


def _is_geopackage(connection: 'Connection') -> bool:
    """
    Check if an SQLite database has the Geopackage Structure
    """
    try:
        cursor = connection.execute(
            """SELECT name FROM sqlite_master 
               WHERE type = 'table' AND name LIKE 'gpkg_%'""")
        results = {n for n, in cursor.fetchall()}
    except (DatabaseError, OperationalError):
        return False
    return results.issuperset(BASE_TABLES)
# End _is_geopackage function


def get_table_names(connection: 'Connection') -> list[str]:
    """
    Get Tables Names
    """
    sql = """
        SELECT NAME FROM sqlite_master 
        WHERE TYPE = 'table'
        UNION
        SELECT NAME FROM sqlite_temp_master 
        WHERE TYPE = 'table'
    """
    cursor = connection.execute(sql)
    return [n for n, in cursor.fetchall()]
# End get_table_names function


def has_table(connection: 'Connection', table_name: str) -> bool:
    """
    Check for a table by name, case insensitive
    """
    param: str = 'table_name'
    sql = f"""
        SELECT NAME FROM sqlite_master 
        WHERE TYPE = 'table' AND lower(NAME) = :{param}
        UNION
        SELECT NAME FROM sqlite_temp_master 
        WHERE TYPE = 'table' AND lower(NAME) = :{param}
    """
    cursor = connection.execute(sql, {param: table_name.casefold()})
    return bool(cursor.fetchone())
# End has_table method


if __name__ == '__main__':  # pragma: no cover
    pass
