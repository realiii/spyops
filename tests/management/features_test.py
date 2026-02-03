# -*- coding: utf-8 -*-
"""
Tests for Features
"""


from fudgeo import FeatureClass
from fudgeo.enumeration import ShapeType
from pyproj import CRS
from pytest import mark, param, approx

from spyops.environment import Extent, OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.environment.core import zm_config
from spyops.geometry.constant import FUDGEO_GEOMETRY_LOOKUP
from spyops.management import multipart_to_singlepart
from spyops.shared.constant import EPSG, ESRI
from spyops.shared.field import ORIG_FID

from tests.util import UseGrids


class TestMultiPartToSinglePart:
    """
    Test multipart to single part
    """
    @mark.zm
    @mark.parametrize('fc_name, count', [
        ('structures_ma', 1452),
        ('structures_m_ma', 1452),
        ('structures_z_ma', 1452),
        ('structures_zm_ma', 1452),
        ('toponymy_mp', 142),
        ('toponymy_m_mp', 142),
        ('toponymy_z_mp', 142),
        ('toponymy_zm_mp', 142),
        ('transmission_ml', 51),
        ('transmission_m_ml', 51),
        ('transmission_z_ml', 51),
        ('transmission_zm_ml', 51),
        ('transmission_mp', 11),
        ('transmission_m_mp', 11),
        ('transmission_z_mp', 11),
        ('transmission_zm_mp', 11),
    ])
    @mark.parametrize('output_z', [
        param(OutputZOption.SAME, marks=mark.large),
        OutputZOption.ENABLED,
        param(OutputZOption.DISABLED, marks=mark.large),
    ])
    @mark.parametrize('output_m', [
        param(OutputMOption.SAME, marks=mark.large),
        OutputMOption.ENABLED,
        param(OutputMOption.DISABLED, marks=mark.large),
    ])
    def test_output_zm(self, ntdb_zm_small, mem_gpkg, fc_name, count, output_z, output_m):
        """
        Test multipart to single-part using Output ZM
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=f'{fc_name}_explode')
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source)
            exploded = multipart_to_singlepart(source=source, target=target)
        assert exploded.shape_type in (
            ShapeType.linestring, ShapeType.point, ShapeType.polygon)
        cls = FUDGEO_GEOMETRY_LOOKUP[exploded.shape_type][exploded.has_z, exploded.has_m]
        assert exploded.is_multi_part is False
        assert exploded.has_z == zm.z_enabled
        assert exploded.has_m == zm.m_enabled
        assert len(exploded) == count
        assert len(exploded.fields) == len(source.fields) + 1
        geoms, ids = zip(*exploded.select(ORIG_FID).fetchall())
        assert len(set(ids)) == len(source)
        assert all(isinstance(g, cls) for g in geoms)
    # End test_output_zm method

    @mark.transform
    @mark.parametrize('fc_name, auth_name, srs_id, flag, extent', [
        ('structures_6654_ma', EPSG, 2955, False, (674894.5, 5653715.0, 710369.625, 5680768.5)),
        ('structures_6654_zm_ma', EPSG, 2955, False, (674894.5, 5653715.0, 710369.625, 5680768.5)),
        ('transmission_6654_m_ml', EPSG, 2955, False, (674555.1875, 5652839.5, 710282.9375, 5681615.5)),
        ('transmission_6654_z_ml', EPSG, 2955, False, (674555.1875, 5652839.5, 710282.9375, 5681615.5)),
        ('toponymy_6654_m_mp', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0)),
        ('toponymy_6654_z_mp', EPSG, 2955, False, (675601.0, 5653706.5, 710185.125, 5681412.0)),
        ('structures_10tm_ma', ESRI, 102179, False, (35292.07421875, 5647691.0, 70171.859375, 5674681.0)),
        ('structures_10tm_zm_ma', ESRI, 102179, False, (35292.07421875, 5647691.0, 70171.859375, 5674681.0)),
        ('transmission_10tm_m_ml', ESRI, 102179, False, (34970.6953125, 5647467.0, 70035.03125, 5675514.0)),
        ('transmission_10tm_z_ml', ESRI, 102179, False, (34970.6953125, 5647467.0, 70035.03125, 5675514.0)),
        ('toponymy_10tm_m_mp', ESRI, 102179, False, (35593.41796875, 5647808.0, 70109.640625, 5675312.5)),
        ('toponymy_10tm_z_mp', ESRI, 102179, False, (35593.41796875, 5647808.0, 70109.640625, 5675312.5)),
    ])
    def test_output_crs(self, ntdb_zm_small, mem_gpkg, fc_name, auth_name,
                        srs_id, flag, extent):
        """
        Test multi to single with output CRS and different input spatial reference systems
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        crs = CRS.from_authority(auth_name=auth_name, code=srs_id)
        with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs), UseGrids(flag):
            zm = zm_config(source)
            result = multipart_to_singlepart(source=source, target=target)
            assert result.spatial_reference_system.srs_id == srs_id
            assert result.spatial_reference_system.org_coord_sys_id == srs_id
            assert len(result) > len(source)
            assert approx(result.extent, abs=0.001) == extent
            assert result.has_z == zm.z_enabled
            assert result.has_m == zm.m_enabled
    # End test_output_crs method

    @mark.parametrize('fc_name, pre_count, post_count', [
        ('structures_6654_ma', 18, 1442),
        ('structures_6654_zm_ma', 18, 1442),
        ('transmission_6654_m_ml', 4, 50),
        ('transmission_6654_z_ml', 4, 50),
        ('toponymy_6654_m_mp', 1, 142),
        ('toponymy_6654_z_mp', 1, 142),
        ('structures_10tm_ma', 18, 1442),
        ('structures_10tm_zm_ma', 18, 1442),
        ('transmission_10tm_m_ml', 4, 50),
        ('transmission_10tm_z_ml', 4, 50),
        ('toponymy_10tm_m_mp', 1, 142),
        ('toponymy_10tm_z_mp', 1, 142),
    ])
    def test_extent(self, ntdb_zm_small, mem_gpkg, fc_name, pre_count, post_count):
        """
        Test multi to single with extent set, because these features are
        so highly grouped the small extent does not filter out many, extent
        is applied to the source features before processing
        """
        source = ntdb_zm_small[fc_name]
        target = FeatureClass(geopackage=mem_gpkg, name=fc_name)
        crs = CRS(4326)
        assert len(source) == pre_count
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.2, 51.05, -114.05, 51.15, crs)):
            result = multipart_to_singlepart(source=source, target=target)
            assert len(result) == post_count
    # End test_output_crs method
# End TestMultiPartToSinglePart class


if __name__ == '__main__':  # pragma: no cover
    pass
