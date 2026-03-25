# -*- coding: utf-8 -*-
"""
Fixtures
"""


from pathlib import Path
from typing import Generator

from fudgeo import GeoPackage, MemoryGeoPackage
from pytest import fixture


def _open_geopackage(path: Path) -> Generator[GeoPackage, None, None]:
    """
    Open GeoPackage and Close connection
    """
    gpkg = GeoPackage(path)
    yield gpkg
    gpkg.connection.close()
# End _open_geopackage function


@fixture(scope='session')
def data_path() -> Path:
    """
    Data Path
    """
    return Path(__file__).parent.parent.joinpath('data')
# End data_path function


@fixture(scope='session')
def inputs(data_path) -> Generator[GeoPackage, None, None]:
    """
    Inputs
    """
    yield from _open_geopackage(data_path.joinpath('inputs.gpkg'))
# End inputs function


@fixture(scope='session')
def buffering(data_path) -> Generator[GeoPackage, None, None]:
    """
    Buffering
    """
    yield from _open_geopackage(data_path.joinpath('buffering.gpkg'))
# End buffering function


@fixture(scope='session')
def check_repair(data_path) -> Generator[GeoPackage, None, None]:
    """
    Check Repair
    """
    yield from _open_geopackage(data_path.joinpath('check_repair.gpkg'))
# End check_repair function


@fixture(scope='session')
def planar(data_path) -> Generator[GeoPackage, None, None]:
    """
    Planar
    """
    yield from _open_geopackage(data_path.joinpath('planar.gpkg'))
# End planar function


@fixture(scope='session')
def ntdb_zm_meh(data_path) -> Generator[GeoPackage, None, None]:
    """
    NTDB Clipped to sixteen 50K tiles around YYC, Z values in these
    features are either NaN or a single value (123.456) and most (if not all)
    of the M values are empty (NaN).
    """
    yield from _open_geopackage(data_path.joinpath('ntdb_zm_meh.gpkg'))
# End ntdb_zm_meh function


@fixture(scope='session')
def ntdb_zm(data_path) -> Generator[GeoPackage, None, None]:
    """
    NTDB Clipped to sixteen 50K tiles around YYC, Z and M values in these
    features are fully populated, albeit with bogus-ish values but at least
    varying per vertex.
    """
    yield from _open_geopackage(data_path.joinpath('ntdb_zm.gpkg'))
# End ntdb_zm function


@fixture(scope='session')
def ntdb_zm_meh_small(data_path) -> Generator[GeoPackage, None, None]:
    """
    NTDB Clipped to a single 50K tile near YYC, Z values in these
    features are either NaN or a single value (123.456) and most (if not all)
    of the M values are empty (NaN).
    """
    yield from _open_geopackage(data_path.joinpath('ntdb_zm_meh_small.gpkg'))
# End ntdb_zm_meh_small function


@fixture(scope='session')
def ntdb_zm_small(data_path) -> Generator[GeoPackage, None, None]:
    """
    NTDB Clipped to a single 50K tile near YYC, Z and M values in these
    features are fully populated, albeit with bogus-ish values but at least
    varying per vertex.  Also includes a variety of coordinate systems.
    """
    yield from _open_geopackage(data_path.joinpath('ntdb_zm_small.gpkg'))
# End ntdb_zm_small function


@fixture(scope='session')
def ntdb_zm_tile(data_path) -> Generator[GeoPackage, None, None]:
    """
    NTDB Clipped to a single 50K tile near YYC, Z and M values in these
    features are fully populated, albeit with bogus-ish values but at least
    varying per vertex.  Intersected with grid_a to get DATANAME.
    """
    yield from _open_geopackage(data_path.joinpath('ntdb_zm_tile.gpkg'))
# End ntdb_zm_tile function


@fixture(scope='session')
def grid_index(data_path) -> Generator[GeoPackage, None, None]:
    """
    Index and grid feature classes, includes a variety of coordinate systems.
    """
    yield from _open_geopackage(data_path.joinpath('grid_index.gpkg'))
# End grid_index function


@fixture(scope='session')
def world_tables(data_path) -> Generator[GeoPackage, None, None]:
    """
    World Tables
    """
    yield from _open_geopackage(data_path.joinpath('world_tables.gpkg'))
# End world_tables function


@fixture(scope='session')
def world_features(data_path) -> Generator[GeoPackage, None, None]:
    """
    World Features
    """
    yield from _open_geopackage(data_path.joinpath('world_features.gpkg'))
# End world_features function


@fixture(scope='session')
def crs_geopackage(data_path) -> Generator[GeoPackage, None, None]:
    """
    CRS GeoPackage
    """
    yield from _open_geopackage(data_path.joinpath('crs.gpkg'))
# End crs_geopackage function


@fixture(scope='session')
def nrn_geopackage(data_path) -> Generator[GeoPackage, None, None]:
    """
    NRN GeoPackage
    """
    yield from _open_geopackage(data_path.joinpath('nrn.gpkg'))
# End nrn_geopackage function


@fixture(scope='function')
def fresh_gpkg(tmp_path) -> Generator[GeoPackage, None, None]:
    """
    Fresh GeoPackage
    """
    gpkg = GeoPackage.create(tmp_path.joinpath('geo.gpkg'))
    yield gpkg
    gpkg.connection.close()
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
