# -*- coding: utf-8 -*-
"""
Measured Line
"""


from bisect import bisect_left
from math import nan
from typing import Optional, TYPE_CHECKING

from numpy import (
    array, cumsum, diff, flatnonzero, full, hypot, interp, isfinite, zeros_like)


from spyops.shared.hint import VALUES


if TYPE_CHECKING:
    from numpy import ndarray


class MeasuredLine:
    """
    Measured Line
    """
    def __init__(self, xs: VALUES, ys: VALUES, *,
                 zs: Optional[VALUES] = None, ms: Optional[VALUES] = None,
                 lengths: Optional[VALUES] = None,
                 validate_measures: bool = False,
                 is_2d: bool = False, start_length: float = 0.) -> None:
        """
        Initialize the MeasuredLine class
        """
        super().__init__()
        if zs is None:
            zs = zeros_like(xs, dtype=float)
        self._validate_inputs(xs, ys=ys, zs=zs, ms=ms, lengths=lengths)
        ms = self._prepare_measures(
            ms, xs=xs, ys=ys, zs=zs, is_2d=is_2d, validate=validate_measures)
        lengths = self._prepare_measures(
            lengths, xs=xs, ys=ys, zs=zs, is_2d=is_2d,
            validate=validate_measures, start=start_length)
        coords = full((len(xs), 5), fill_value=nan, dtype=float)
        coords[:, 0] = xs
        coords[:, 1] = ys
        coords[:, 2] = zs
        coords[:, 3] = ms
        coords[:, 4] = lengths
        self._coordinates: 'ndarray' = coords
    # End init built-in

    @classmethod
    def from_coordinates_2d(cls, coordinates: 'ndarray',
                            start_length: float = 0.) -> 'MeasuredLine':
        """
        From Coordinates stored in array and using 2D length
        """
        return cls(
            xs=coordinates[:, 0], ys=coordinates[:, 1], zs=coordinates[:, 2],
            ms=coordinates[:, 3], is_2d=True, start_length=start_length)
    # End from_coordinates method

    @property
    def coordinates(self) -> 'ndarray':
        """
        Coordinates
        """
        return self._coordinates[:, :4]
    # End coordinates property

    @property
    def measures(self) -> 'ndarray':
        """
        Measures
        """
        return self._coordinates[:, 3]
    # End measures property

    def _prepare_measures(self, values: Optional[VALUES], *,
                          xs: VALUES, ys: VALUES, zs: VALUES,
                          is_2d: bool, validate: bool,
                          start: float = 0.) -> VALUES:
        """
        Prepare Measures / Lengths
        """
        if values is None:
            return self._calculate_measures(xs, ys, zs, is_2d=is_2d) + start
        if validate:
            self._validate_measures(values)
        return values
    # End _prepare_measures method

    @staticmethod
    def _validate_inputs(xs: VALUES, ys: VALUES, zs: VALUES,
                         ms: Optional[VALUES],
                         lengths: Optional[VALUES]) -> None:
        """
        Validate length of inputs
        """
        length = len(xs)
        msg = 'Input coordinates have different lengths'
        has_same_length = length == len(ys) == len(zs)
        if not has_same_length:
            raise ValueError(msg)
        for values in (ms, lengths):
            if values is None:
                continue
            if length != len(values):
                raise ValueError(msg)
    # End _validate_inputs method

    @staticmethod
    def _validate_measures(ms: VALUES) -> None:
        """
        Validate that there are no repeated measures
        """
        if len(ms) != len(set(ms)):
            raise ValueError('Found repeated measure values')
        if (diff(ms) < 0).any():
            raise ValueError('Found non-monotonic measure values')
    # End _validate_measures method

    def _calculate_measures(self, xs: VALUES, ys: VALUES, zs: VALUES,
                            is_2d: bool) -> VALUES:
        """
        Calculate measures
        """
        lengths = self._calculate_segment_lengths(xs, ys)
        if is_2d:
            return lengths
        mask = ~isfinite(zs)
        if mask.all():
            zs = zeros_like(zs, dtype=float)
        elif mask.any():
            zs = array(zs, dtype=float)
            zs[mask] = interp(flatnonzero(mask), flatnonzero(~mask), zs[~mask])
        return self._calculate_segment_lengths(lengths, zs)
    # End _calculate_measures method

    @staticmethod
    def _calculate_segment_lengths(a: VALUES, b: VALUES) -> VALUES:
        """
        Calculate Segment Lengths
        """
        lengths = zeros_like(a, dtype=float)
        lengths[1:] = cumsum(hypot(diff(a), diff(b)))
        return lengths
    # End _calculate_segment_lengths method

    def _check_measure(self, measure: float) -> bool:
        """
        Check Measure against all Measures
        """
        if measure < min(self.measures):
            return False
        if measure > max(self.measures):
            return False
        return True
    # End _check_measure method

    def _snap_to_bounds(self, measure: float) -> float:
        """
        Snap the measure value to the begin or end measure value
        """
        min_m = min(self.measures)
        if measure < min_m:
            return min_m
        max_m = max(self.measures)
        if measure > max_m:
            return max_m
        return measure
    # End _snap_to_bounds method

    def _find_segment(self, measure: float) \
            -> tuple[Optional['ndarray'], Optional['ndarray']]:
        """
        Find Segment on which the measure falls
        """
        is_valid = self._check_measure(measure)
        if not is_valid:
            return None, None
        index = bisect_left(self.measures, measure)
        if index:
            index -= 1
        return self.coordinates[index], self.coordinates[index + 1]
    # End _find_segment method

    def _get_start_end(self, measure: float, snap: bool = False) \
            -> Optional[tuple[Optional['ndarray'], Optional['ndarray']]]:
        """
        Get Start and End
        """
        if snap:
            measure = self._snap_to_bounds(measure)
        start, end = self._find_segment(measure)
        if start is None or end is None:
            return None
        return start, end
    # End _get_start_end method

    def find_z(self, measure: float, snap: bool = False) -> float | None:
        """
        Find Z from Measure
        """
        if (result := self._get_start_end(measure=measure, snap=snap)) is None:
            return None
        start, end = result
        _, _, start_z, start_m = start
        _, _, end_z, end_m = end
        return interp(measure, (start_m, end_m), (start_z, end_z))
    # End find_z method

    def find_xyz(self, measure: float, snap: bool = False) \
            -> Optional[tuple[float, float, float]]:
        """
        Find XYZ from Measure
        """
        if (result := self._get_start_end(measure=measure, snap=snap)) is None:
            return None
        start, end = result
        start_x, start_y, start_z, start_m = start
        end_x, end_y, end_z, end_m = end
        x = interp(measure, (start_m, end_m), (start_x, end_x))
        y = interp(measure, (start_m, end_m), (start_y, end_y))
        z = interp(measure, (start_m, end_m), (start_z, end_z))
        return x, y, z
    # End find_xyz method

    def interpolate(self, values: VALUES, use_length: bool = False) -> 'ndarray':
        """
        Find Coordinates for values along the line. By default, the values are
        interpolated using the measures otherwise they are interpolated using
        the geometric length which may be 2D or 3D depending on the inputs used
        during initialization.  Return all coordinates for the values in same
        order as input values.
        """
        count = len(values)
        coords = full((count, 4), fill_value=nan, dtype=float)
        if not count:
            return coords
        index = 3 + int(use_length)
        # NOTE use the internal property to access length too
        coordinates = self._coordinates
        kwargs = dict(xp=coordinates[:, index], left=nan, right=nan)
        coords[:, 0] = interp(values, fp=coordinates[:, 0], **kwargs)
        coords[:, 1] = interp(values, fp=coordinates[:, 1], **kwargs)
        coords[:, 2] = interp(values, fp=coordinates[:, 2], **kwargs)
        if use_length:
            coords[:, 3] = values
        else:
            coords[:, 3] = interp(values, fp=self.measures, **kwargs)
        return coords
    # End interpolate method
# End MeasuredLine class


if __name__ == '__main__':  # pragma: no cover
    pass
