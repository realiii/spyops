# -*- coding: utf-8 -*-
"""
Internal functions for conversion package
"""


from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, Union

from fudgeo import FeatureClass
from fudgeo.context import ExecuteMany

from spyops.geometry.util import validated_transform
from spyops.shared.records import extend_records


if TYPE_CHECKING:  # pragma: no cover
    from spyops.query.conversion.gps import AbstractQueryGPXToFeatures
    from spyops.query.conversion.json import AbstractQueryGeoJSONToFeatures


QUERY: TypeAlias = Union[
    'AbstractQueryGPXToFeatures', 'AbstractQueryGeoJSONToFeatures']


def _to_features(source: Path, query: QUERY) -> FeatureClass:
    """
    Converts from file-based source to target feature class
    """
    records = []
    insert_sql = query.insert
    config = query.geometry_config
    transformer = query.source_transformer
    with (query.target.geopackage.connection as cout,
          ExecuteMany(connection=cout, table=query.target) as executor):
        if not (features := query.features(source)):
            return query.target
        geometries, *_ = zip(*features)
        features, geometries = validated_transform(
            transformer, features=features, geometries=geometries)
        results = [(g, attrs) for g, (_, *attrs) in zip(geometries, features)]
        extend_records(results, records=records, config=config)
        executor(sql=insert_sql, data=records)
    return query.target
# End _to_features function


if __name__ == '__main__':  # pragma: no cover
    pass
