# -*- coding: utf-8 -*-
"""
Fixtures
"""


from pathlib import Path
from typing import Generator

from fudgeo import GeoPackage, MemoryGeoPackage
from pytest import fixture


@fixture(scope='session')
def data_path() -> Path:
    """
    Data Path
    """
    return Path(__file__).parent.parent.joinpath('data')
# End data_path function


@fixture(scope='session')
def inputs(data_path) -> GeoPackage:
    """
    Inputs
    """
    return GeoPackage(data_path.joinpath('inputs.gpkg'))
# End inputs function


@fixture(scope='session')
def ntdb_zm_meh(data_path) -> GeoPackage:
    """
    NTDB Clipped to sixteen 50K tiles around YYC, Z values in these
    features are either NaN or a single value (123.456) and most (if not all)
    of the M values are empty (NaN).
    """
    return GeoPackage(data_path.joinpath('ntdb_zm_meh.gpkg'))
# End ntdb_zm_meh function


@fixture(scope='session')
def ntdb_zm(data_path) -> GeoPackage:
    """
    NTDB Clipped to sixteen 50K tiles around YYC, Z and M values in these
    features are fully populated, albeit with bogus-ish values but at least
    varying per vertex.
    """
    return GeoPackage(data_path.joinpath('ntdb_zm.gpkg'))
# End ntdb_zm function


@fixture(scope='session')
def ntdb_zm_meh_small(data_path) -> GeoPackage:
    """
    NTDB Clipped to a single 50K tile near YYC, Z values in these
    features are either NaN or a single value (123.456) and most (if not all)
    of the M values are empty (NaN).
    """
    return GeoPackage(data_path.joinpath('ntdb_zm_meh_small.gpkg'))
# End ntdb_zm_meh_small function


@fixture(scope='session')
def ntdb_zm_small(data_path) -> GeoPackage:
    """
    NTDB Clipped to a single 50K tile near YYC, Z and M values in these
    features are fully populated, albeit with bogus-ish values but at least
    varying per vertex.
    """
    return GeoPackage(data_path.joinpath('ntdb_zm_small.gpkg'))
# End ntdb_zm_small function


@fixture(scope='session')
def grid_index(data_path) -> GeoPackage:
    """
    Index and grid feature classes
    """
    return GeoPackage(data_path.joinpath('grid_index.gpkg'))
# End grid_index function


@fixture(scope='session')
def world_tables(data_path) -> GeoPackage:
    """
    World Tables
    """
    return GeoPackage(data_path.joinpath('world_tables.gpkg'))
# End world_tables function


@fixture(scope='session')
def world_features(data_path) -> GeoPackage:
    """
    World Features
    """
    return GeoPackage(data_path.joinpath('world_features.gpkg'))
# End world_features function


@fixture(scope='session')
def crs_geopackage(data_path) -> GeoPackage:
    """
    CRS GeoPackage
    """
    return GeoPackage(data_path.joinpath('crs.gpkg'))
# End crs_geopackage function


@fixture(scope='function')
def fresh_gpkg(tmp_path) -> GeoPackage:
    """
    Fresh GeoPackage
    """
    return GeoPackage.create(tmp_path.joinpath('geo.gpkg'))
# End fresh_gpkg function


@fixture(scope='function')
def mem_gpkg(tmp_path) -> Generator[MemoryGeoPackage, None, None]:
    """
    Fresh MemoryGeoPackage
    """
    gpkg = MemoryGeoPackage.create()
    yield gpkg
    gpkg.connection.close()
# End mem_gpkg function


if __name__ == '__main__':  # pragma: no cover
    pass
