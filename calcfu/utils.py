import numpy as np


# https://stackoverflow.com/a/64100245/16065715
def split_given_size(a, size):
    # arange args are start, stop, step
    # 2nd arg of split allows sections. if [3,7] will split [:3], [3:7], [7:]
    return np.split(a, np.arange(size, len(a), size))
