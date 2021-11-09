# Introduction
This script calculates reportable counts for the. While the calculation is simple in most cases (in the NCIMS program),
this script allows for more robust calculations where any dilution and number of plates can be used.

The code below outlines the entire process and references the NCIMS 2400s.
* [2400a: SPC - Pour Plate](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf)
* [2400a-4: SPC - Petrifilm](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf)

# Plate Class
Plates are set up via the Plate class.

```python
from plate import Plate

# 1 plate with a 10^-2 dilution yielding a total count of 234.
plates_1 = Plate(count=234, dilution="-2", num_plts=1)
# 1 plate with a 10^-3 dilution yielding a total count of 53
plates_2 = Plate(count=53, dilution="-3", num_plts=1)
```

### Instance Variables
Each instance of the class is created with three arguments which are set as instance variables.

Arguments:

* ```count``` [ *int* ]
    * Raw plate counts.
* ```dilution``` [ *str* ]
    * Dilution used to plate.
* ```num_plts``` [ *int* ]
    * Number of plates for each dilution.

Other instance variables are also declared and are later updated and referenced during calculation.

* ```in_between``` [ *bool* ] 
    * If count is within the accepted count range for plate type.
* ```sign``` [ *str* ]
    * If greater than or equal to minimum or maximum count.
* ```closest_bound``` [ *int* ]
    * Minimum or maximum count.
* ```abs_diff``` [ *int* ]
    * The absolute difference between the count and the closest_bound.

```python
class Plate:
    def __init__(self, count, dilution, num_plts):
        self._count = count
        self._dilution = dilution
        self._num_plts = num_plts

        self._in_between = False
        self._sign = ""
        self._closest_bound = 0
        self._abs_diff = 0
```

### Getters and Setters
Getter and setter methods are also defined to allow for alteration and validation of input arguments.

```python
@property
def dilution(self):
    if self._dilution == "1:1":
        return 0
    else:
        return int(self._dilution)

@dilution.setter
def dilution(self, dilution):
    self._dilution = dilution
```

Here, when the variable is retrieved from the Plate instance in the calculation steps,
it is converted to an integer. If it is "1:1", then 0 is returned instead.

# Count Calculator
The calculator is contained in the CountCalculator class.
Using the previously created plates, a CountCalculator instance is created.

```python
from calculator import CountCalculator

# Setup calculator with two HSCC plates that have weighed product.
calc = CountCalculator(weighed=True, plate_type="HSCC", plates=[plates_1, plates_2])
```

### Class variables
Two class variables are set for the class. 

* ```PLATE_RANGES``` [ *dict* ]
    * Acceptable count ranges for each plate type.
* ```WEIGHED_UNITS``` [ *dict* ]
    * Units for if weighed or not.

```python
class CountCalculator:
    PLATE_RANGES = {
        "SPC": (25, 250),
        "PAC": (25, 250),
        "RAC": (25, 250),
        "CPC": (1, 154),
        "HSCC": (1, 154),
        "PCC": (1, 154)
    }

    WEIGHED_UNITS = {
        True: " / g",
        False: " / mL"
    }
```


### Instance variables
Each instance of CountCalculator is initialized with three arguments:

* ```weighed``` [ *bool* ]
    * If product plated was weighed or not.
* ```plate_type```[ *str* ]
    * Plate types. Valid items in ```PLATE_RANGES``` keys.
    * If invalid, throws ValueError.
* ```plates``` [ *list* ]
    * Contains Plate instances.

Using the above arguments, other instance variables are defined.

* ```main_dil``` [ *int* ]
    * Finds the lowest dilution among the plates.
    * ```max(-2, -3)``` would return ```-2```.
* ```reported_units``` [ *str* ]
    * Formats units based on plate type and if product plated was weighed.
* ```cnt_range``` [ *tuple* ]
    * The acceptable colony range for a given plate type.
    * The method ```_set_bounds``` returns the result. See "Methods" section below.

```python
def __init__(self, weighed, plate_type, plates):
    self.weighed = weighed
    self.plate_type = plate_type
    self.plates = plates

    self.main_dil = max(plate.dilution for plate in plates)
    self.reported_units = f"{plate_type}{self.UNITS.get(self.weighed)}"

    self.cnt_range = self._set_bounds()
    self._check_in_between()
    self._check_closer_to()
```


## Methods
Three methods are called during initialization:

* ```_set_bounds()```
    * Returns the acceptable plate range for the provided plate type.
    
```python 
def _set_bounds(self):
    if cnt_range := self.PLATE_RANGES.get(self.plate_type, None):
        return cnt_range
    else:
        raise ValueError("Invalid plate type.")
```

* ```_check_in_between()```
    * Validates plate counts and updates Plate instance variables ```in_between``` and ```sign```.
    * Conditional statements compare if counts are in between acceptable ranges.
    * Pour Plates 
        * SPC ([NCIMS 2400a-16e-f](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf#page=7))
        * CPC ([NCIMS 2400a-17e](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf#page=9))
    * Petrifilm
        * PAC / RAC ([NCIMS 2400a-4-16e-f](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf#page=10))
        * PCC / HSCC ([NCIMS 2400a-17e](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf#page=11))

```python
def _check_in_between(self):
    for plate in self.plates:
        count = plate.count
        if count < 0:
            raise ValueError("Invalid number of colonies (Less than 0).")
        elif 0 < count < self.cnt_range[0]:
            plate.in_between = False
            plate.sign = "<"
        elif self.cnt_range[0] <= count <= self.cnt_range[1]:
            plate.in_between = True
            plate.sign = ""
        elif count > self.cnt_range[1]:
            plate.in_between = False
            plate.sign = ">"
```

* ```_check_closer_to()```
    * Updates Plate instance variables ```closest_bound``` and ```abs_diff```.
    *  ```bounds_abs_diff``` [ *dict* ]
        * Keys: Accepted colony count for plate
        * Value: Absolute difference of count.
   
    *  ```closest_bound``` [ *int* ]
        * Lowest acceptable colony count bound from ```bound_abs_diff```.
        * Closer counts will have a smaller absolute difference.
        * |27 - 25| = 2 and |27 - 250| = 223. So, 27 is closer to 25.

```python
def _check_closer_to(self):
    for plate in self.plates:
        # Dict of bounds and their abs difference between the number of colonies.
        bounds_abs_diff = {bound: abs(plate.count - bound) for bound in self.cnt_range}
        # return closest bound based on min abs diff between count and bound
        closest_bound = min(bounds_abs_diff, key=bounds_abs_diff.get)
        # set plate closest bound and abs diff
        plate.closest_bound = closest_bound
        plate.abs_diff = bounds_abs_diff[closest_bound]
```

Two methods are available for use with the CountCalculator instance: ```bank_round``` and ```calc_result```

### calc_result()

This method is the "meat-and-potatoes" of the script. 
It calculates the reported/adjusted count based on the plates given. 

Optional arguments:

* ```round_to``` [ *int* ]
    * Digit to round to. Default is 1.
        * Relative to leftmost digit (0). *Python is 0 indexed*.
    * ex. Round to 1: 2(5),666 
    * ex. Round to 3: 25,6(6)6
* ```report_count``` [ *bool* ]
    * Option to return reported count or non-rounded, unlabeled adjusted count.
    
First, each plate is checked to see if its count is in between the accepted count range.
Based on the number of valid plates, different methods will be used to calculate the result.

```python
def calc_result(self, round_to=1, report_count=True):
    valid_plates = [plate for plate in self.plates if plate.in_between]
    if len(valid_plates) == 0:
        adj_count = self._calc_no_dil_valid()
    elif len(valid_plates) == 1:
        valid_plate = valid_plates[0]
        adj_count = valid_plate.count * (10 ** abs(valid_plate.dilution))
    else:
        adj_count = self._calc_multi_dil_valid(valid_plates)
    if report_count:
        if isinstance(adj_count, int):
            return f"{self.bank_round(adj_count, round_to)} {self.reported_units}"
        else:
            # string = no valid dil result. add estimated to units
            return f"{adj_count} e{self.reported_units}"
    else:
        return adj_count
```



#### calc_no_dil_valid() 
This code runs when *no plates have valid counts*.

Procedure:
1. Plates that have the highest acceptable count bound are taken.
    * [NCIMS 2400a-16e-f](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf#page=10))
2. Reduce the list of plates down by checking adjacent plates' ```abs_diff```
  and returning the one with lowest value. 
    * Final plate is the closest to the highest acceptable bound.
3. Finally, format with ```sign``` and multiply the closest bound by the reciprocal of the dilution.
    * NCIMS 2400s
    
```python
from functools import reduce

def _calc_no_dil_valid(self):
    hbound_plates = [plate for plate in self.plates if plate.closest_bound == self.cnt_range[1]]
    # Use reduce to reduce hbound_plates to a single plate:
    #   plate with the lowest absolute difference between the hbound and value
    closest_to_hbound = reduce(lambda p1, p2: min(p1, p2, key=lambda x: x.abs_diff), hbound_plates)
    return f"{closest_to_hbound.sign}{closest_to_hbound.closest_bound * (10 ** abs(closest_to_hbound.dilution))}"
```

#### calc_multi_dil_valid()
This method runs if *multiple plates have valid counts*.

Required Arguments
* ```valid_plates``` [ *list* ]
    *  Plates that have acceptable counts for their plate type.

Variables
* ```dil_weights``` [ *list* ]
    * The weights each dilution/plate contributes to the total count.
* ```div_factor``` [ *int* ]
    * The sum of ```dil_weights```. Part of the denominator of the weighted averaged. 
    
Procedure:
1. First, sum counts from all valid plates.

![](figures/total.png)

2. If all plates are the same dilution, set ```div_factor``` to 1.
    * NCIMS 2400s
3. Otherwise, we will take a weighted average taking into account how each dilution contributes to the ```div_factor```.

![](figures/div_factor.png)

4. Each dilution will have a *weight* of how much it contributes to the total count (via the ```div_factor```)
    * If the plate dilution is the ```main_dil```, set the dilution's weight to 1. 
        * **This value is the ```main_dil```'s weight towards the total count.** 
        * Remember, the least diluted plate contributes the largest number of colonies 
          to the overall count. It will always be 1 and used to normalize the other dilutions.
        * NCIMS 2400s
    * If it is not, subtract the absolute value of ```main_dil``` by the absolute value of ```plate.dilution```.
        * By raising 10 to the power of ```abs_diff_dil```, **the plate dilution's weight - relative to ```main_dil``` - is calculated.** 
5. Each dilution weight is then multiplied by the number of plates used for that dilution. 
6. The sum of all dilution weights in ```dil_weights``` is the division weight, ```div_factor```.
7. Dividing the ```total``` by the product of ```div_factor``` and ```main_dil``` yields the adjusted count.
   
![](figures/adj_count.png)



```python
def _calc_multi_dil_valid(self, valid_plates):
    total = sum(plate.count for plate in valid_plates)
    # If all plates have the same dilution. 
    if all(plate.dilution == valid_plates[0].dilution for plate in valid_plates):
        div_factor = 1
    else:
        dil_weights = []
        for plate in valid_plates:
            if plate.dilution == self.main_dil:
                dil_weights.append(1 * plate.num_plts)
            else:
                abs_diff_dil = abs(self.main_dil) - abs(plate.dilution)
                dil_weights.append((10 ** abs_diff_dil) * plate.num_plts)
        div_factor = sum(dil_weights)

    return int(total / (div_factor * (10 ** self.main_dil)))
```

#### Once a value is returned...

### bank_round() 

This method rounds values using banker's rounding. 
```python
@staticmethod
def bank_round(value, place):
    if isinstance(value, int) and isinstance(place, int):
        # Length of unrounded value ex. 295
        # -1 to val len because if a fraction - 0.855 rather than 8.55 - , will not round up to correct value of 9.
        value_len = len(str(value)) - 1
        # weight to divide by to turn value into float.
        div_factor = 10 ** value_len
        # +3 in substring of value for 0.#
        str_adj_value = str(value / div_factor)[0:place+3]
        flt_adj_value = float(str_adj_value)
        final_val = round(flt_adj_value, place) * div_factor
        return int(final_val)
    else:
        raise ValueError("Invalid value or place (Not an integer).")
```

# Some Test Cases












