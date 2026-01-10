# -*- coding: utf-8 -*-
"""
Fixtures
"""


from pathlib import Path

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
def ntdb_clipped(data_path) -> GeoPackage:
    """
    NTDB Clipped to sixteen 50K tiles around YYC
    """
    return GeoPackage(data_path.joinpath('ntdb_clipped.gpkg'))
# End ntdb_clipped function


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
def mem_gpkg(tmp_path) -> MemoryGeoPackage:
    """
    Fresh MemoryGeoPackage
    """
    return MemoryGeoPackage.create()
# End mem_gpkg function


if __name__ == '__main__':  # pragma: no cover
    pass
