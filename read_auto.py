import logging
import pathlib
import traceback
import argparse
import itertools
import pandas as pd
import numpy as np

from calcfu.calc_config import CalcConfig
from calcfu.calculator import CalCFU
from calcfu.plate import Plate
from calcfu.exceptions import CalCFUError, PlateError, ReaderError
from calcfu.utils import split_given_size

logger = logging.getLogger(__name__)

# Colony count columns needed for result.
PLT_COL_KEY = {"PAC" : ["Red Raw Count"], 
               "RAC": ["Red Raw Count", "Blue Raw Count"], 
               "PCC": ["Red with Gas Raw Count"]}
    

def load_3m_csv(input_path):
    """
    Load 3M results csv file.
    Paired with R shiny app so columns (not values) are immutable.
    :param input_path: Input path to 3M results csv.
    :return: pd.DataFrame with cleaned and filtered results.
    """
    df = pd.read_csv(input_path, dtype = str)
    
    # Remove rows with x in Sample ID or plate type is ve (verification)
    df = df.loc[(df["Sample ID"] != "x") & (df["Plate Type"] != "VE")]
    
    # Replace AC with PAC for plate type.
    df["Plate Type"] = df["Plate Type"].str.replace("^AC$", "PAC", regex = True)
    
    # Replace "1:1" with "0" for calculation.
    df["Dilution"] = df["Dilution"].str.replace("1:1", "0", regex = True)
    
    # Get all columns that contain "Count".
    count_cols = df.loc[:, df.columns.str.contains('Count')].replace("-", "0")

    # Convert cnts to int raising error if cannot coerce.
    valid_counts = count_cols.apply(lambda x: x.str.isnumeric())

    if not np.ravel(valid_counts).all():
        invalid_plt_ids = df[~valid_counts]["Sample ID"].values
        raise ReaderError(f"{invalid_plt_ids} have invalid counts.")
    else:
        count_cols = count_cols.apply(pd.to_numeric, errors ='raise').astype('int')

        # Set df "Count" columns to modified columns.
        df.loc[:, df.columns.str.contains('Count')] = count_cols
    
    
    # Validate plate type and dilution column
    valid_plt_types = df["Plate Type"].isin(PLT_COL_KEY.keys())
    valid_dils = df["Dilution"].isin(str(n) for n in CalcConfig.VALID_DILUTIONS)
    
    if not valid_plt_types.all():
        invalid_plt_ids = df[~valid_plt_types]["Sample ID"].values
        raise ReaderError(f"{invalid_plt_ids} have invalid plate types.")
    if not valid_dils.all():
        invalid_plt_ids = df[~valid_dils]["Sample ID"].values
        raise ReaderError(f"{invalid_plt_ids} have invalid dilutions.")
    else:
        # If all in valid dilutions, safe to convert to int.
        df["Dilution"] = df["Dilution"].astype('int')
    
    return df

def get_3m_group_cnts(plt: pd.DataFrame, plt_type: str):
    """
    Aggregate counts of single plate based on plate type.
    :param plt: DataFrame row for single plate.
    :param plt_type: Plate type. "None" (use col val) or one of allowed plate types.
    :return:
    """
    if plt_type == "None":
        cnt = plt.loc[PLT_COL_KEY[plt["Plate Type"]]].sum()
    else:
        cnt = plt.loc[PLT_COL_KEY[plt_type]].sum()
    return cnt
    

def create_3m_groups(groups: pd.DataFrame, weighed: bool, plt_type: str, dils: str):
    """
    Creates groups of Plate instances from a group of dataframes containing 3M plate results.
    :param groups: Dataframe with 3M results.
    :param weighed: Weighed sample?
    :param plt_type: Plate type or "None"
    :param dils: Dilutions in format ("'#/#'") or "None"
    :return:
    """
    
    if dils != ["None"]:
        dils = [int(dil) for dil in dils]
        
    plt_groups = []
    plt_groups_ids = []
    
    for group in groups:
        plt_group = []
        plt_group_ids = []
        
        # Number of rows in group.
        n_plates = group.shape[0]
        
        # Zip plate indices of group and dilutions, 
        #   cycling through dilutions if number of plates not a multiple of dils.
        # dil will be ignored if dils equal to "None".
        for i, dil in zip(range(n_plates), itertools.cycle(dils)):
            # grab row in df
            plt = group.iloc[i]

            plt_obj = Plate(plate_type=(plt["Plate Type"] if plt_type == "None" else plt_type), 
                            count=get_3m_group_cnts(plt, plt_type),
                            dilution=(plt["Dilution"] if dils == ["None"] else dil),
                            weighed=weighed,
                            num_plts=1)
                
            plt_group.append(plt_obj)
            plt_group_ids.append(plt["Sample ID"])

        # add groups to plates groups and plate id groups
        plt_groups.append(plt_group)
        plt_groups_ids.append(plt_group_ids)
        
    return plt_groups, plt_groups_ids
    
def r_auto_results(input_path: str, output_path: str, weighed: bool, group_n: str, plt_type: str, dils: str):
    """

    """
    df = load_3m_csv(input_path)

    if int(group_n) == 0:
        # Group by matching ID
        df = df.assign(abbrID=df["Sample ID"].str.split("-").str[0],
                       pltNum=df["Sample ID"].str.split("-").str[1])
                       
        ids = df.abbrID.dropna().unique()
       
        # split into groups by unique ids and sort by plate number
        groups = [df[df.abbrID == i].sort_values(by="pltNum") for i in ids]
        
    else:  # by num
        groups = split_given_size(df, int(group_n))


    plt_groups, plt_groups_ids = create_3m_groups(groups, weighed, plt_type, dils)
    
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
    ap.add_argument("--dilution", "-d", default = "None", nargs = "*", help="Dilutions (None to use recorded vals).")
    args = vars(ap.parse_args()).values()
    try:
        out = r_auto_results(*args)
        return out
    # print to stdout for bash
    except (ReaderError, CalCFUError, PlateError) as e:
        # custom error.
        print(e)
    except Exception as e:
        
        print(f"{traceback.format_exc(limit = 3)}")


if __name__ == "__main__":
    main()
