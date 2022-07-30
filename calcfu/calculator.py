import logging
import numpy as np
from typing import List, Optional
from dataclasses import dataclass
from typing import Tuple, Union

from .plate import Plate
from .calc_config import CalcConfig
from .exceptions import CalCFUError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, order=True)
class CalCFU(CalcConfig):
    plates: List
    plate_ids: Optional[List] = None

    def __post_init__(self) -> None:
        # check if plate first and then if all samples were/were not weighed
        if not self.INPUT_VALIDATORS["plates"](self.plates, Plate):
            raise CalCFUError(
                f"Invalid plate list. Not Plate instances, the same plate type, or <2 Plates.\n{self.plate_ids}"
            )
        if not self.INPUT_VALIDATORS["all_weighed"](self.plates):
            raise CalCFUError(
                f"Invalid plate list. Must be all weighed or not all weighed.\n{self.plate_ids}"
            )

    @property
    def valid_plates(self) -> List[Plate]:
        """
        Valid plates based on if between bounds for plate type.
        :return: valid plates
        """
        return [plate for plate in self.plates if plate.in_between]

    @property
    def reported_units(self) -> str:
        """
        Units for plate.
        :return: units
        """
        # grab first plate and use plate type. should be all the same
        return f"{self.plates[0].plate_type}{self.WEIGHED_UNITS.get(self.plates[0].weighed)}"

    def _calc_multi_dil_valid(self) -> int:
        """
        Calculate case where multiple dilutions are valid and and adjustment is needed.

        :return: adjusted count for valid plates.
        """
        valid_plates = self.valid_plates
        total = sum(plate.count for plate in valid_plates)
        main_dil = max(plate.dilution for plate in valid_plates)
        # If all plates have the same dilution.
        if all(plate.dilution == valid_plates[0].dilution for plate in valid_plates):
            # each plates is equally weighed because all the same dil
            div_factor = sum(1 * plate.num_plts for plate in valid_plates)
        else:
            dil_weights = []
            for plate in valid_plates:
                if plate.dilution == main_dil:
                    dil_weights.append(1 * plate.num_plts)
                else:
                    # calculate dil weight relative to main_dil
                    abs_diff_dil = abs(main_dil) - abs(plate.dilution)
                    dil_weights.append((10 ** int(abs_diff_dil)) * plate.num_plts)

            div_factor = sum(dil_weights)

        return int(total / (div_factor * (10 ** int(main_dil))))

    def _calc_no_dil_valid(self, report_count: bool) -> Tuple[str, int]:
        """
        Case where no dilutions are valid ex. SPC where <25 or > 250.
        :param report_count: reported count where only bounds returned not raw count.

        :return: sign and count
        """
        # If all plates have same absolute diff, take plate with highest dilution.
        if all(
            plt.hbound_abs_diff == self.plates[0].hbound_abs_diff for plt in self.plates
        ):
            closest_to_hbound = min(self.plates, key=lambda x: x.dilution)
        else:
            # Find plate with the lowest absolute difference between the hbound and value
            closest_to_hbound = min(self.plates, key=lambda x: x.hbound_abs_diff)

        # if reporting, use closest bound; otherwise, use count.
        value = (
            closest_to_hbound.closest_bound if report_count else closest_to_hbound.count
        )

        return closest_to_hbound.sign, value * (10 ** abs(closest_to_hbound.dilution))

    def calculate(
        self, round_to: int = 2, report_count: bool = True
    ) -> Union[str, int]:
        """
        Calculate the adjusted CFU value given the plates initialized to an instance of CalCFU.
        :param round_to: n-digits to round to
        :report reported_count: return formatted string with units instead of raw int CFU

        :return: integer CFU or string, labeled CFU
        """
        valid_plates = self.valid_plates
        # assign empty str to sign var. will be default unless no plate valid
        sign = ""
        # track if estimated i.e. no plate is valid.
        estimated = False

        if len(valid_plates) == 0:
            sign, adj_count = self._calc_no_dil_valid(report_count)
            estimated = True
        elif len(valid_plates) == 1:
            # only one plate is valid so multiple by reciprocal of dil.
            valid_plate = valid_plates[0]
            adj_count = valid_plate.count * (10 ** abs(valid_plate.dilution))
        else:
            adj_count = self._calc_multi_dil_valid()

        if report_count:
            units = f"{('' if not estimated else 'e')}{self.reported_units}"
            # add sign, thousands separator, and units
            return (
                f"{sign}{'{:,}'.format(self.bank_round(adj_count, round_to))} {units}"
            )
        else:
            return adj_count

    @staticmethod
    def bank_round(value: Union[int, np.int64], place_from_left: int) -> int:
        """
        Perform bank rounding per NCIMS 2400 standards.
        :param value: CFU value
        :place_from_left: Round to this place from left side of value.

        :return: rounded value
        """
        value_is_int = isinstance(value, int) or isinstance(value, np.int64)
        if value_is_int and isinstance(place_from_left, int):
            # Length of unrounded value.
            value_len = len(str(value))
            # remove digits that would alter rounding only allowing 1 digit before desired place
            str_abbr_value = str(value)[0 : place_from_left + 1]
            # pad with 0's equal to number of removed digits
            str_padded_value = str_abbr_value + (
                "0" * (value_len - len(str_abbr_value))
            )
            adj_value = int(str_padded_value)
            # reindex place_from_left for round function.
            # place_from_left = 2 for 2(5)553. to round, needs to be -3 so subtract length by place and multiply by -1.
            adj_place_from_left = -1 * (value_len - place_from_left)
            final_val = round(adj_value, adj_place_from_left)
            return final_val
        else:
            raise ValueError("Invalid value or place (Not an integer).")
