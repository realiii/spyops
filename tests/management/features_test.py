# -*- coding: utf-8 -*-
"""
Tests for Features
"""


from fudgeo import FeatureClass
from fudgeo.enumeration import GeometryType
from pytest import mark, param

from spyops.environment import OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.environment.core import zm_config
from spyops.geometry.constant import FUDGEO_GEOMETRY_LOOKUP
from spyops.management import multipart_to_singlepart
from spyops.shared.field import ORIG_FID


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
            GeometryType.linestring, GeometryType.point, GeometryType.polygon)
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
# End TestMultiPartToSinglePart class


if __name__ == '__main__':  # pragma: no cover
    pass
