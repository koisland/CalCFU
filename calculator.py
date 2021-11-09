from typing import List
from functools import reduce
from dataclasses import dataclass

from plate import Plate
from calc_config import CalcConfig


@dataclass(frozen=True, order=True)
class CFUCalculator(CalcConfig):
    weighed: bool
    plates: List[Plate]

    def __post_init__(self):
        assert self.INPUT_VALIDATORS["plates"](self.plates, Plate), "Invalid plate list."

    @property
    def reported_units(self):
        # grab first plate and use plate type. should be all the same
        return f"{self.plates[0].plate_type}{self.WEIGHED_UNITS.get(self.weighed)}"

    def _calc_multi_dil_valid(self, valid_plates):
        total = sum(plate.count for plate in valid_plates)
        main_dil = max(plate.dilution for plate in self.plates)
        # If all plates have the same dilution.
        if all(plate.dilution == valid_plates[0].dilution for plate in valid_plates):
            div_factor = 1
        else:
            dil_weights = []
            for plate in valid_plates:
                if plate.dilution == main_dil:
                    dil_weights.append(1 * plate.num_plts)
                else:
                    abs_diff_dil = abs(main_dil) - abs(plate.dilution)
                    dil_weights.append((10 ** abs_diff_dil) * plate.num_plts)
            div_factor = sum(dil_weights)

        return int(total / (div_factor * (10 ** main_dil)))

    def _calc_no_dil_valid(self):
        hbound_plates = [plate for plate in self.plates if plate.closest_bound == plate.cnt_range[1]]
        if len(hbound_plates) == 0:
            # if neither close to hbound:
            #   take any plate's closest bound, multiply by reciprocal of dil, and add sign to calc
            return f"{self.plates[0].sign}{self.plates[0].closest_bound * (10 ** abs(self.plates[0].dilution))}"
        else:
            # Use reduce to reduce hbound_plates to a single plate:
            #   plate with the lowest absolute difference between the hbound and value
            closest_to_hbound = reduce(lambda p1, p2: min(p1, p2, key=lambda x: x.abs_diff), hbound_plates)
            return f"{closest_to_hbound.count * (10 ** abs(closest_to_hbound.dilution))}"

    def calculate(self, round_to=2, report_count=True):
        valid_plates = [plate for plate in self.plates if plate.in_between]
        if len(valid_plates) == 0:
            adj_count = self._calc_no_dil_valid()
        elif len(valid_plates) == 1:
            valid_plate = valid_plates[0]
            adj_count = valid_plate.count * (10 ** abs(valid_plate.dilution))
        else:
            adj_count = self._calc_multi_dil_valid(valid_plates)
        if report_count:
            if isinstance(adj_count, int):
                return f"{self.bank_round(adj_count, round_to)} {self.reported_units}"
            else:
                # string = no valid dil result. add estimated to units
                return f"{adj_count} e{self.reported_units}"
        else:
            return adj_count

    @staticmethod
    def bank_round(value, place_from_left):
        if isinstance(value, int) and isinstance(place_from_left, int):
            # Length of unrounded value.
            value_len = len(str(value))
            # remove digits that would alter rounding only allowing 1 digit before desired place
            str_abbr_value = str(value)[0:place_from_left + 1]
            # pad with 0's equal to number of removed digits
            str_padded_value = str_abbr_value + ("0" * (value_len - len(str_abbr_value)))
            adj_value = int(str_padded_value)
            # reindex place_from_left for round function.
            # place_from_left = 2 for 2(5)553. to round, needs to be -3 so subtract length by place and multiply by -1.
            adj_place_from_left = -1 * (value_len - place_from_left)
            final_val = round(adj_value, adj_place_from_left)
            return int(final_val)
        else:
            raise ValueError("Invalid value or place (Not an integer).")
