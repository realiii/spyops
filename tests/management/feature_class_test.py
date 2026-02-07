# -*- coding: utf-8 -*-
"""
Tests for Feature Class
"""
from fudgeo import FeatureClass
from fudgeo.constant import FID, SHAPE
from numpy import isfinite
from pytest import approx, mark

from spyops.management.feature_class import (
    create_feature_class,
    recalculate_feature_class_extent)


pytestmark = [mark.management, mark.feature_class]


def test_recalculate_feature_class_extent(ntdb_zm_small, mem_gpkg):
    """
    Test recalculate feature class extent
    """
    fc = ntdb_zm_small['hydro_a'].copy(name='hydro_a_copy', geopackage=mem_gpkg)
    assert isfinite(fc.extent).all()
    bogus = (0, 0, 1, 1)
    fc.extent = bogus
    assert fc.extent == bogus
    result = recalculate_feature_class_extent(fc)
    assert approx(result.extent, abs=0.001) == (-114.5, 51, -113.9999, 51.25)
# End test_recalculate_feature_class_extent function


def test_create_feature_class(mem_gpkg):
    """
    Test create feature class
    """
    fc_name = 'test fc'
    srs = mem_gpkg.spatial_references[4326]
    result = create_feature_class(mem_gpkg, fc_name, srs=srs)
    assert isinstance(result, FeatureClass)
    assert result.name == 'test_fc'
    assert [f.name for f in result.fields] == [FID, SHAPE]
# End test_create_feature_class function


if __name__ == '__main__':  # pragma: no cover
    pass
