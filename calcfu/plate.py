import logging
from dataclasses import dataclass, asdict

from .calc_config import CalcConfig
from .exceptions import PlateError

logger = logging.getLogger(__name__)


# frozen for read-only
@dataclass(frozen=True, order=True)
class Plate(CalcConfig):
    plate_type: str
    count: int
    dilution: int
    weighed: bool
    num_plts: int = 1

    # post init dunder method for validation
    def __post_init__(self):
        for key, value in asdict(self).items():
            if not self.INPUT_VALIDATORS[key](value):
                raise PlateError(f"Invalid Plate argument ({key}: {value} [{type(value)}]). Check calc_config.py.")

    @property
    def cnt_range(self):
        # self.cnt_range[0] is min, self.cnt_range[1] is max
        return self.PLATE_RANGES.get(self.plate_type, None)

    @property
    def in_between(self):
        if self.cnt_range[0] <= self.count <= self.cnt_range[1]:
            return True
        else:
            return False

    @property
    def sign(self):
        if 0 <= self.count < self.cnt_range[0]:
            return "<"
        elif self.count > self.cnt_range[1]:
            return ">"
        else:
            return ""

    @property
    def _bounds_abs_diff(self):
        # Dict of bounds and their abs difference between the number of colonies.
        return {bound: abs(self.count - bound) for bound in self.cnt_range}

    @property
    def hbound_abs_diff(self):
        return abs(self.count - self.cnt_range[1])

    @property
    def closest_bound(self):
        # return closest bound based on min abs diff between count and bound
        return min(self._bounds_abs_diff, key=self._bounds_abs_diff.get)
