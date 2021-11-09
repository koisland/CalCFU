from collections.abc import Iterable


class CalcConfig:
    VALID_DILUTIONS = (0, -1, -2, -3, -4)
    PLATE_RANGES = {
        "SPC": (25, 250),
        "PAC": (25, 250),
        "RAC": (25, 250),
        "CPC": (1, 154),
        "HSCC": (1, 154),
        "PCC": (1, 154),
        "YM": (),
        "RYM": ()
    }
    WEIGHED_UNITS = {True: " / g", False: " / mL"}

    INPUT_VALIDATORS = {
        # count must be an integer and greater than 0
        "plate_type": lambda plate_type: plate_type in CalcConfig.PLATE_RANGES,
        "count": lambda count: isinstance(count, int) and count > 0,
        # dilution must be in valid dilutions
        "dilution": lambda dilution: dilution in CalcConfig.VALID_DILUTIONS,
        # num_plts must be an integer and greater than 0
        "num_plts": lambda num_plts: isinstance(num_plts, int) and num_plts > 0,
        # plates must all be an instance of the Plate dataclass
        "plates": lambda plates, plt_cls: all(isinstance(plate, plt_cls) for plate in plates)
    }
