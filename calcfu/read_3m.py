import datetime
import pandas as pd
import numpy as np

from calcfu.calc_config import CalcConfig


# https://stackoverflow.com/a/64100245/16065715
def split_given_size(a, size):
    # arange args are start, stop, step
    # 2nd arg of split allows sections. if [3,7] will split [:3], [3:7], [7:]
    return np.split(a, np.arange(size, len(a), size))


def main():
    """

    :return:
    """
    df = pd.read_csv(CalcConfig.FPATH_3M, sep="\t")
    df = df.loc[:, ["Date/Time of Image", "Red Raw Count"]]
    # Remove hyphens (error) as count
    df = df[df["Red Raw Count"] != "-"]
    # Cast count col to int.
    # Convert date and times to datetimes.
    df = df.astype({"Red Raw Count": np.int64})
    df["Date/Time of Image"] = pd.to_datetime(df["Date/Time of Image"], format="%m/%d/%Y %H:%M:%S %p")

    # dt attr allows access to dt properties of a series.
    dates = df["Date/Time of Image"].dt.date.unique()

    for date in dates:
        query = df[df["Date/Time of Image"].dt.date == date]

        # if even, print query.
        if query.shape[0] % 2 == 0:
            pairs = split_given_size(query["Red Raw Count"], 2)
            for pair in pairs:
                print(pair)
    # print(df)
    # print(df.dtypes)


if __name__ == "__main__":
    main()
