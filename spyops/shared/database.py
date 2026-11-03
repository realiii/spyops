# -*- coding: utf-8 -*-
"""
Database Functionality
"""


from pathlib import Path
from sqlite3 import Connection, DatabaseError, OperationalError, connect

from fudgeo import MemoryGeoPackage

from spyops.shared.constant import SPYOPS, UNDERSCORE
from spyops.shared.hint import ELEMENT
from spyops.shared.stats import STATS_FUNCS


BASE_TABLES: set[str] = {'gpkg_spatial_ref_sys', 'gpkg_contents',
                         'gpkg_geometry_columns', 'gpkg_tile_matrix_set',
                         'gpkg_tile_matrix', 'gpkg_extensions'}


def is_geopackage(path: Path | str) -> bool:
    """
    Is GeoPackage?
    """
    if not path:
        return False
    path: Path = Path(path)
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
    # noinspection SqlResolve
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
    Check for a table by name, case-insensitive
    """
    param: str = 'table_name'
    sql = f"""
        SELECT NAME FROM sqlite_master 
        WHERE TYPE = 'table' AND NAME = :{param}
        COLLATE NOCASE
        UNION
        SELECT NAME FROM sqlite_temp_master 
        WHERE TYPE = 'table' AND NAME = :{param}
        COLLATE NOCASE
    """
    cursor = connection.execute(sql, {param: table_name})
    return bool(cursor.fetchone())
# End has_table method


def add_aggregates(connection: 'Connection') -> None:
    """
    Add Aggregate Classes, avoid stomping on possible existing functions
    """
    for name, func in STATS_FUNCS.items():
        connection.create_aggregate(f'{SPYOPS}{UNDERSCORE}{name}', 1, func)
# End add_aggregates function


def remove_aggregates(connection: 'Connection') -> None:
    """
    Remove Aggregate Classes
    """
    for name in STATS_FUNCS:
        # noinspection bad-argument-type
        connection.create_aggregate(f'{SPYOPS}{UNDERSCORE}{name}', 1, None)
# End remove_aggregates function


def check_same_geopackage(target: ELEMENT, other: ELEMENT) -> bool:
    """
    Check Same GeoPackage
    """
    if target.geopackage is other.geopackage:
        return True
    if not isinstance(target.geopackage, other.geopackage.__class__):
        return False
    if isinstance(target.geopackage, MemoryGeoPackage):
        # NOTE if get here identity check has failed, we assume two
        #  different MemoryGeoPackages, which is true unless someone has
        #  taken control over the connection string for MemoryGeoPackage
        #  or done some other changes to the internals
        return True
    else:
        return target.geopackage.path.samefile(other.geopackage.path)
# End check_same_geopackage function


def check_same_element(target: ELEMENT, other: ELEMENT) -> bool:
    """
    Check Same Element
    """
    if target.name.casefold() != other.name.casefold():
        return False
    return check_same_geopackage(target, other)
# End check_same_element function


if __name__ == '__main__':  # pragma: no cover
    pass
