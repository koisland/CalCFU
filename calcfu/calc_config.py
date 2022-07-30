import numpy as np
import pathlib
import datetime


class CalcConfig:
    FPATH_WD = pathlib.Path(__file__).parents[1]
    FPATH_DATA = pathlib.Path.joinpath(FPATH_WD, "data")
    FPATH_LOG = pathlib.Path.joinpath(
        FPATH_WD,
        "logs",
        f"calcfu_log_{datetime.datetime.strftime(datetime.datetime.now(), '%m_%d_%y')}.log",
    )
    DEF_COLS_3M = {"Date/Time of Image", "Red Raw Count"}
    DEF_SAVE_OUTPUT = {"csv": ".csv", "excel": ".xlsx"}

    VALID_DILUTIONS = (0, -1, -2, -3, -4)
    PLATE_RANGES = {
        "SPC": (25, 250),
        "PAC": (25, 250),
        "RAC": (25, 250),
        "CPC": (1, 154),
        "HSCC": (1, 154),
        "PCC": (1, 154),
        "YM": (),
        "RYM": (),
    }
    WEIGHED_UNITS = {True: " / g", False: " / mL"}
    INPUT_VALIDATORS = {
        # count must be an integer and greater than 0
        "plate_type": lambda plate_type: plate_type in CalcConfig.PLATE_RANGES,
        "count": lambda count: (
            isinstance(count, int) or isinstance(count, np.int64) and count >= 0
        ),
        # dilution must be in valid dilutions
        "dilution": lambda dilution: dilution in CalcConfig.VALID_DILUTIONS,
        "weighed": lambda weighed: isinstance(weighed, bool),
        # num_plts must be an integer and greater than 0
        "num_plts": lambda num_plts: (
            isinstance(num_plts, int) or isinstance(num_plts, np.int64) and num_plts > 0
        ),
        # plates (>=2) must all be an instance of the Plate dataclass and must be all the same plate_type
        "plates": lambda plates, plt_cls: all(
            [
                all(
                    isinstance(plt, plt_cls) and plt.plate_type == plates[0].plate_type
                    for plt in plates
                ),
                len(plates) >= 2,
            ]
        ),
        "all_weighed": lambda plates: all(
            plates[0].weighed == plate.weighed for plate in plates
        ),
    }
