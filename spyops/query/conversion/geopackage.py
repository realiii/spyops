# -*- coding: utf-8 -*-
"""
Query Classes for conversion.geopackage module
"""


from typing import TYPE_CHECKING

from spyops.environment import ANALYSIS_SETTINGS
from spyops.query.base import BaseQuerySelect
from spyops.shared.element import copy_element
from spyops.shared.hint import ELEMENT, GPKG
from spyops.shared.util import element_names, make_unique_name


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


class BaseQueryElementToGeoPackage(BaseQuerySelect):
    """
    Base Query Element to GeoPackage
    """
    def __init__(self, element: ELEMENT, geopackage: GPKG) -> None:
        """
        Initialize the BaseQueryElementToGeoPackage class
        """
        target = self._make_target(element, geopackage)
        super().__init__(source=element, target=target)
    # End init built-in

    @staticmethod
    def _make_target(element: ELEMENT, geopackage: GPKG) -> ELEMENT:
        """
        Make Target
        """
        if ANALYSIS_SETTINGS.overwrite:
            return element.__class__(geopackage=geopackage, name=element.name)
        else:
            names = element_names(geopackage)
            name = make_unique_name(element.name, names)
            return element.__class__(geopackage=geopackage, name=name)
    # End _make_target method
# End BaseQueryElementToGeoPackage class


class QueryTableToGeoPackage(BaseQueryElementToGeoPackage):
    """
    Query Table to GeoPackage
    """
    def __init__(self, element: ELEMENT, geopackage: GPKG) -> None:
        """
        Initialize the QueryTableToGeoPackage class
        """
        super().__init__(element, geopackage=geopackage)
    # End init built-in

    def copy(self) -> ELEMENT:
        """
        Copy
        """
        return copy_element(source=self.source, target=self._target)
    # End copy method
# End QueryTableToGeoPackage class


if __name__ == '__main__':  # pragma: no cover
    pass
