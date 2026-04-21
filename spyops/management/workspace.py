# -*- coding: utf-8 -*-
"""
Workspace Data Management
"""


from pathlib import Path
from typing import Callable

from fudgeo import GeoPackage
from fudgeo.enumeration import GPKGFlavors


__all__ = ['create_sqlite_database', 'create_geopackage']


def create_sqlite_database(path: Path | str, *, is_epsg_flavor: bool = False,
                           enable_metadata: bool = False,
                           enable_schema: bool = False,
                           ogr_contents: bool = False) -> GeoPackage:
    """
    Create SQLite Database

    Create a GeoPackage using the specified fully qualified path.
    """
    if is_epsg_flavor:
        flavor = GPKGFlavors.epsg
    else:
        flavor = GPKGFlavors.esri
    return GeoPackage.create(
        path, flavor=flavor, enable_metadata=enable_metadata,
        enable_schema=enable_schema, ogr_contents=ogr_contents)
# End create_sqlite_database function


create_geopackage: Callable[[Path | str, bool, bool, bool, bool], GeoPackage] = create_sqlite_database


if __name__ == '__main__':  # pragma: no cover
    pass
