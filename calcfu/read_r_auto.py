import logging
import pathlib
import argparse
import itertools
import pandas as pd
import numpy as np

from calculator import CalCFU
from plate import Plate
from exceptions import CalCFUError, PlateError
from read_3m import split_given_size

logger = logging.getLogger(__name__)

def r_auto_results(input_path, output_path, weighed, group, group_n, dils):
    """

    """
    df = pd.read_csv(input_path)
    # r read csv replaces space with .
    df.columns = df.columns.str.replace(".", " ", regex = False)
    
    # replace mult nondigit chars with NA, convert cnts to int, and AC plate type to PAC
    df["Red Raw Count"] = df["Red Raw Count"].str.replace("\D+", "", regex = True)
    df["Red Raw Count"] = pd.to_numeric(df["Red Raw Count"], errors ='raise').fillna(0).astype('int')
    df["Plate Type"] = df["Plate Type"].str.replace("^AC$", "PAC", regex = True)

    # TODO: For now, just stick to red raw count since PAC is only plate approved.
    df = df[["DateTime", "Sample ID", "Red Raw Count", "Dilution", "Plate Type"]]

    plt_groups = []
    plt_groups_ids = []
    
    # replace 1:1 with 0 and split str
    dils = [int(dil) for dil in dils.replace("1:1", "0").split(" / ")]

    if group == "id":
        # Group by matching ID
        df = df.assign(abbrID=df["Sample ID"].str.split("-").str[0],
                       pltNum=df["Sample ID"].str.split("-").str[1])
                       
        # ID Must be numeric. Otherwise, ignored.
        uniq_ids = pd.to_numeric(df.abbrID, errors="coerce").unique()
        ids = uniq_ids[~np.isnan(uniq_ids)]

        # split into groups by unique ids
        groups = [df[df.abbrID == str(i)] for i in ids]

    else:  # by num
        # remove verification obs.
        df = df[df["Plate Type"] != "VE"]
        groups = split_given_size(df, int(group_n))

    for group in groups:
        plt_group = []
        plt_group_ids = []
        
        # zip plate index and dilution cycling through dilutions if plates not multiple of two.
        for i, dil in zip(range(group.shape[0]), itertools.cycle(dils)):
            # grab row in df
            plt = group.iloc[i]

            plt_obj = Plate(plate_type=plt["Plate Type"], 
                            count=plt["Red Raw Count"],
                            dilution=dil,
                            weighed=weighed,
                            num_plts=1)
                
            plt_group.append(plt_obj)
            plt_group_ids.append(plt["Sample ID"])

        # add groups to plates groups and plate id groups
        plt_groups.append(plt_group)
        plt_groups_ids.append(plt_group_ids)
    
    
    cfus = [CalCFU(grp).calculate() for grp in plt_groups]
    cnts = [[plt.count for plt in grp] for grp in plt_groups]
    
    # Construct result df and save as csv
    res_df = pd.DataFrame({"CFU": cfus, "Counts": cnts, "Plates": plt_groups_ids})

    res_df.to_csv(output_path, index=False)
    return output_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", "-i", required=True, help="Input path.")
    ap.add_argument("--output", "-o", required=True, help="Output path.")
    ap.add_argument("--weighed", "-w", action="store_true", help="Weighed plate?")
    ap.add_argument("--group", "-g", default="id", help="Group by num or id.")
    ap.add_argument("--group_n", "-gn", default = 2, help="Number to group by (If -g provided).")
    ap.add_argument("--dilution", "-d", default = "-2 / -3", help="Dilution group.")
    args = vars(ap.parse_args()).values()
    try:
        out = r_auto_results(*args)
        return out
    except Exception as e:
        # print to stdout for bash
        print(e)


if __name__ == "__main__":
    main()
