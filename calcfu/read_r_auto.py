import logging
import pathlib
import argparse
import itertools
import pandas as pd
import numpy as np

from calculator import CalCFU
from plate import Plate
from exceptions import CalCFUError, PlateError
from utils import split_given_size

logger = logging.getLogger(__name__)


def load_3m_csv(input_path):
    df = pd.read_csv(input_path)
    
    # r read csv replaces space with .
    df.columns = df.columns.str.replace(".", " ", regex = False)
    
    # Get all columns that contain "Count".
    count_cols = df.loc[:, df.columns.str.contains('Count')]
    
    # Replace mult nondigit chars and convert cnts to int.
    count_cols = count_cols.replace("\D+", "", regex = True)
    count_cols = count_cols.apply(pd.to_numeric, errors ='raise').fillna(0).astype('int')
    
    # Set df "Count" columns to modified columns.
    df.loc[:, df.columns.str.contains('Count')] = count_cols
    
    # Replace AC with PAC for plate type.
    df["Plate Type"] = df["Plate Type"].str.replace("^AC$", "PAC", regex = True)
    
    # Remove rows with x in Sample ID or plate type is ve (verification)
    df = df.loc[(df["Sample ID"] != "x") & (df["Plate Type"] != "VE")]
    
    return df

def create_3m_groups(groups, weighed, group_n, plt_type, dils):
    # TODO: If dils == None
    if dils != "None":
        # strip ', replace 1:1 with 0 and split str
        dils = dils.strip("'").replace("1:1", "0").split("/")
        dils = [int(dil) for dil in dils]
    else:
        dils = [-2, -3]
        
    if plt_type != "None":
        pass
    
    plt_groups = []
    plt_groups_ids = []
    
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
        
    return plt_groups, plt_groups_ids
    
def r_auto_results(input_path, output_path, weighed, group_n, plt_type, dils):
    """

    """
    df = load_3m_csv(input_path)

    if int(group_n) == 0:
        # Group by matching ID
        df = df.assign(abbrID=df["Sample ID"].str.split("-").str[0],
                       pltNum=df["Sample ID"].str.split("-").str[1])
                       
        ids = df.abbrID.dropna().unique()
       
        # TODO: sort based on pltNum
        # split into groups by unique ids
        groups = [df[df.abbrID == i] for i in ids]
        
    else:  # by num
        groups = split_given_size(df, int(group_n))


    plt_groups, plt_groups_ids = create_3m_groups(groups, weighed, group_n, plt_type, dils)
    
    cfus = [CalCFU(grp, grp_ids).calculate() for grp, grp_ids in zip(plt_groups, plt_groups_ids)]
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
    ap.add_argument("--group_n", "-g", default = 0, help="Number to group by (0 for id).")
    ap.add_argument("--plate", "-p", default = "None", help="Plate type (None to use recorded vals).")
    ap.add_argument("--dilution", "-d", default = "None", help="Dilution group (None to use recorded vals).")
    args = vars(ap.parse_args()).values()
    try:
        out = r_auto_results(*args)
        return out
    except Exception as e:
        # print to stdout for bash
        print(e)


if __name__ == "__main__":
    main()
