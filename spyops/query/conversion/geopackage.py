# -*- coding: utf-8 -*-
"""
Query Classes for conversion.geopackage module
"""


from spyops.environment import ANALYSIS_SETTINGS
from spyops.query.base import BaseQuerySelect
from spyops.shared.element import copy_element
from spyops.shared.hint import ELEMENT, GPKG
from spyops.shared.util import element_names, make_unique_name


class QueryTableToGeoPackage(BaseQuerySelect):
    """
    Query Table to GeoPackage
    """
    def __init__(self, element: ELEMENT, geopackage: GPKG) -> None:
        """
        Initialize the QueryTableToGeoPackage class
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

    def copy(self) -> ELEMENT:
        """
        Copy
        """
        return copy_element(source=self._element, target=self.target)
    # End copy method
# End QueryTableToGeoPackage class


if __name__ == '__main__':  # pragma: no cover
    pass
