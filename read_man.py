import pathlib
import argparse
import pandas as pd

from calcfu.calculator import CalCFU
from calcfu.plate import Plate
from calcfu.utils import split_given_size 


def r_man_results(input_path, output_path):
    """
    
    """
    df = pd.read_csv(input_path)
    # Convert columns to correct datatype.
    df = df.astype({"Count": int, "Dilution": int, "NumberPlates": int})

    # split df into smaller dfs with 2 rows each
    pairs = split_given_size(df, 2)

    plates = []
    pair_ids = []
    for df in pairs:
        # sep the two sep dfs
        df1, df2 = df.iloc[0], df.iloc[1]
        # init the plate cls.
        plt_pair = [Plate(df1["Type"], df1["Count"], df1["Dilution"], False, df1["NumberPlates"]),
                    Plate(df2["Type"], df2["Count"], df2["Dilution"], False, df2["NumberPlates"])]
        plates.append(plt_pair)
        # merge labels to string with both labels
        pair_ids.append(f"{df1['Label']} & {df2['Label']}")

    cfus = [CalCFU(pair).calculate() for pair in plates]

    # Construct result df and save as csv
    res_df = pd.DataFrame({"CFU": cfus, "Plates": pair_ids})
    res_df.to_csv(output_path, index=False)
    return output_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", "-i", required=True, help="Input path.")
    ap.add_argument("--output", "-o", required=True, help="Output path.")
    args = vars(ap.parse_args()).values()
    out = r_man_results(*args)
    return out


if __name__ == "__main__":
    main()
