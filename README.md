# CalCFU

---
This script calculates reportable counts for plating methods outlined in the NCIMS 2400s. While the calculation is simple in most cases (in the NCIMS program),
this script allows for more robust calculations where any dilution and number of plates can be used.

The code below outlines the entire process and references the NCIMS 2400s.
* [2400a: SPC - Pour Plate](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf)
* [2400a-4: SPC - Petrifilm](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf)

## Plate Class
Plates are set up via the `Plate` dataclass.

```python
from plate import Plate

# 1 PAC plate with a 10^-2 dilution of a weighed sample yielding a total count of 234.
plates_1 = Plate(plate_type="PAC", count=234, dilution=-2, weighed=True, num_plts=1)
# 1 PAC plate with a 10^-1 dilution of a weighed sample yielding a total count of 790.
plates_2 = Plate(plate_type="PAC",count=790, dilution=-1, weighed=True, num_plts=1)
```

### Fields
Each instance of the dataclass is created with three arguments which are set as fields.

Arguments:
* `plate_type` [ *str* ]
    * Plate type. 
* `count` [ *int* ]
    * Raw plate counts.
* `dilution` [ *str* ]
    * Dilution used to plate.
* `weighed` [ *bool* ]
    * Sample was weighed or not.
* `num_plts` [ *int* ]
    * Number of plates for each dilution.
    * By default, this is set to 1.

```python
@dataclass(frozen=True, order=True)
class Plate(CalcConfig):
    plate_type: str
    count: int
    dilution: int
    num_plts: int = 1
```

### Class variables
When an instance of the `Plate` or `CalCFU` class is created, it inherits from the `CalcConfig` class which stores
all necessary configuration variables for the calculator.

* `PLATE_RANGES` [ *dict* ]
    * Acceptable counts for each plate type.
    * NCIMS 2400s
* `WEIGHED_UNITS` [ *dict* ]
    * Units for if weighed or not.
* `VALID_DILUTIONS` [ *tuple* ]
    * Acceptable dilutions for each plate type.
* `INPUT_VALIDATORS` [ *dict* ]
    * A dictionary of anonymous functions used to validate input arguments.

```python
@dataclass(frozen=True, order=True)
class Plate(CalcConfig):
    ...

@dataclass(frozen=True, order=True)
class CalCFU(CalcConfig):
    ...
```

```python
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
        "RYM": ()}
    WEIGHED_UNITS = {True: " / g", False: " / mL"}
    INPUT_VALIDATORS = {
        # count must be an integer and greater than 0
        "plate_type": lambda plate_type: plate_type in CalcConfig.PLATE_RANGES,
        "count": lambda count: isinstance(count, int) and count > 0,
        # dilution must be in valid dilutions
        "dilution": lambda dilution: dilution in CalcConfig.VALID_DILUTIONS,
        "weighed": lambda weighed: isinstance(weighed, bool),
        # num_plts must be an integer and greater than 0
        "num_plts": lambda num_plts: isinstance(num_plts, int) and num_plts > 0,
        
        # plates must all be an instance of the Plate dataclass and must be all the same plate_type
        "plates": lambda plates, plt_cls: all(isinstance(plate, plt_cls) and plate.plate_type == plates[0].plate_type
                                              for plate in plates),
        "all_weighed": lambda plates: all(plates[0].weighed == plate.weighed for plate in plates)}
 
 
 ```

### Argument Validation
Arguments are validated via a `__post_init__` method where each key is checked 
against conditions in `self.INPUT_VALIDATORS`
```python
# post init dunder method for validation
def __post_init__(self):
    for key, value in asdict(self).items():
        assert self.INPUT_VALIDATORS[key](value), \
            "Invalid value. Check calc_config.py."

```

### Properties
Properties are also defined to allow for read-only calculation of attributes from the input arguments.

```python
@property
def cnt_range(self):
    # self.cnt_range[0] is min, self.cnt_range[1] is max
    return self.PLATE_RANGES.get(self.plate_type, None)

@property
def sign(self):
    if 0 < self.count < self.cnt_range[0]:
        return "<"
    elif self.count > self.cnt_range[1]:
        return ">"
    else:
        return ""
```

Here, a sign of a plate is returned based on if a plate count is above or below the max or min place count, respectively. 

```python
# 1 plate with a 10^-2 dilution of a weighed sample yielding a total count of 234.
plates_1 = Plate(plate_type="PAC", count=234, dilution=-2, weighed=True, num_plts=1)
# 1 plate with a 10^-1 dilution of a weighed sample yielding a total count of 790.
plates_2 = Plate(plate_type="PAC",count=790, dilution=-1, weighed=True, num_plts=1)

print(plates_1.sign) # ""
print(plates_2.sign) # "<"
```

# CalCFU
The calculator is contained in the `CalCFU` dataclass.
Using the previously created plates, a `CalCFU` instance is created.

```python
from calculator import CalCFU

# Setup calculator with two PAC plates that contain a weighed sample.
calc = CalCFU(plates=[plates_1, plates_2])
```

### Fields
Each instance of CountCalculator is initialized with the plates to be calculated:

* ```plates``` [ *list* ]
    * Contains Plate instances. 
    * Validated via `__post_init__` method.
    
```python
@dataclass(frozen=True, order=True)
class CalCFU(CalcConfig):
    plates: List
```

### Properties

## Methods

Two methods are available for use with the CountCalculator instance: ```bank_round``` and ```calc_result```

### `calc_result()`

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












