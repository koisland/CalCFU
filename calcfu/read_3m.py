import re
import logging
import pathlib
import datetime
import pandas as pd
import numpy as np

from plate import Plate
from calculator import CalCFU
from exceptions import ReaderError
from calc_config import CalcConfig

logger = logging.getLogger(__name__)


# https://stackoverflow.com/a/64100245/16065715
def split_given_size(a, size):
    # arange args are start, stop, step
    # 2nd arg of split allows sections. if [3,7] will split [:3], [3:7], [7:]
    return np.split(a, np.arange(size, len(a), size))


class Results3M(CalcConfig):
    def __init__(self, path: str,  cols: list, sep: str = "\t"):
        self.path = path
        self.cols = set(cols)
        self.sep = sep
        self.df = self.load()

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        pl_path = pathlib.Path(value)
        if pl_path.exists() and pl_path.is_file():
            self._path = pl_path
        else:
            raise ReaderError("Invalid path to 3M results.")

    @property
    def dates(self):
        # dt attr allows access to dt properties of a series.
        if "Date/Time of Image" in self.df.columns:
            return self.df["Date/Time of Image"].dt.date.unique()

    def load(self):
        if ".xls" in self.path.name:
            df = pd.read_excel
        else:
            df = pd.read_csv(self.path, sep=self.sep)

        col_diff = set.difference(self.cols, set(df.columns))
        if len(col_diff) != 0:
            raise ReaderError(f"Columns ({col_diff}) not in data.")

        if self.cols == {"all"}:
            df = df.loc[:, :]
            self.cols = df.columns
        else:
            cols = set.union(self.cols, self.DEF_COLS_3M)
            df = df.loc[:, cols]

        for col in self.cols:
            if re.search("count", col, flags=re.IGNORECASE):
                # Remove hyphens (error) as count
                df = df[df[col] != "-"]
                # Cast count col to int.
                # Convert date and times to datetimes.
                df = df.astype({col: np.int64})

        if "Date/Time of Image" in self.cols:
            df["Date/Time of Image"] = pd.to_datetime(df["Date/Time of Image"], format="%m/%d/%Y %H:%M:%S %p")

        return df

    def save_as(self, path=None, fname="3M_Results", output_type="csv"):
        if output_type not in self.DEF_SAVE_OUTPUT.keys():
            raise ReaderError("Invalid save output type.")
        if path is None:
            # default to dir 3m text file exists
            path = self.path.parents[0]
        else:
            path = pathlib.Path(path)
            if not path.exists():
                raise ReaderError("Invalid save output path.")

        if path.is_dir():
            path = path / f"{fname}{self.DEF_SAVE_OUTPUT.get(output_type)}"

        if output_type == "excel":
            self.df.to_excel(path)
        elif output_type == "csv":
            self.df.to_csv(path)

    def query(self, col, value, date_time="na"):
        try:
            if date_time == "na":
                col_vals = self.df[col]
            elif date_time == "date":
                col_vals = self.df[col].dt.date
            elif date_time == "time":
                col_vals = self.df[col].dt.time
            else:
                col_vals = self.df[col]

            return self.df[col_vals == value]

        except AttributeError as ex:
            raise ReaderError(f"Selected column ({col}) doesn't have date/time. {ex}")
        except KeyError as ex:
            raise ReaderError(f"Invalid column ({col}).")


def main():
    results_3M_path = pathlib.Path(CalcConfig.FPATH_DATA) / "3M_Results_Raw.txt"
    results = Results3M(path=results_3M_path,
                        cols=['Technician', 'Date/Time of Image', 'Plate Type', 'Dilution', 'Red Raw Count', 'Comment'])
    results.save_as(output_type="csv")

    for date in results.dates:
        query = results.query('Date/Time of Image', date, date_time="date")
        # if even, print query.
        if query.shape[0] % 2 == 0:
            pairs = split_given_size(query["Red Raw Count"], 2)
            sorted_pairs = [sorted(pair, reverse=True) for pair in pairs]
            sorted_plates = [[Plate("PAC", pair[0], -2, False, 1), Plate("PAC", pair[1], -3, False)]
                             for pair in sorted_pairs]
            cfus = [CalCFU(pair).calculate() for pair in sorted_plates]
            print(f"Date: {date} | Pairs: {len(sorted_pairs)} | Total Plates: {len(sorted_pairs) * 2}")
            [print(f"{pair}\n{res}") for pair, res in zip(sorted_pairs, cfus)]


if __name__ == "__main__":
    main()
