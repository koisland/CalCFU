# CalCFU

---
This Python script calculates reportable counts for plating methods outlined in the NCIMS 2400 using two custom classes.
* `Plate` for storing plate characteristics.
* `CalCFU` for the calculator logic.

While the calculation can be performed easily in most cases,
this script allows for bulk-automated calculations where any dilution and number of plates can be used. 

The code below outlines the entire process and references the NCIMS 2400s.
* [NCIMS 2400a: SPC - Pour Plate (Oct 2013)](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf)
* [NCIMS 2400a-4: SPC - Petrifilm (Nov 2017)](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf)

---

## `Plate`
Plates are set up via the `Plate` dataclass.

```python
from calcfu.plate import Plate

# 1 PAC plate with a 10^-2 dilution of a weighed sample yielding a total count of 234.
plates_1 = Plate(plate_type="PAC", count=234, dilution=-2, weighed=True, num_plts=1)
# 1 PAC plate with a 10^-3 dilution of a weighed sample yielding a total count of 53.
plates_2 = Plate(plate_type="PAC", count=53, dilution=-3, weighed=True, num_plts=1)
```

### Fields
Each instance of the dataclass is created with five arguments which are set as fields.

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
    weighed: bool
    num_plts: int = 1
```

### Class Variables
When an instance of the `Plate` or `CalCFU` class is created, it inherits from the `CalcConfig` class which stores
all necessary configuration variables for the calculator.

* `PLATE_RANGES` [ *dict* ]
    * Acceptable counts for each plate type.
        * [SPC - NCIMS 2400a.16.e](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf#page=7)
        * [CPC - NCIMS 2400a.17.e](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf#page=9)
        * [PAC/RAC - NCIMS 2400a-4.16.e](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf#page=10)
        * [PCC/HSCC - NCIMS 2400a-4.17.e](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf#page=11)

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
    # Logging/File Path Variables
    ...
    
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
def in_between(self):
    if self.cnt_range[0] <= self.count <= self.cnt_range[1]:
        return True
    else:
        return False

@property
def sign(self):
    if 0 <= self.count < self.cnt_range[0]:
        return "<"
    elif self.count > self.cnt_range[1]:
        return ">"
    else:
        return ""

@property
def _bounds_abs_diff(self):
    # Dict of bounds and their abs difference between the number of colonies.
    return {bound: abs(self.count - bound) for bound in self.cnt_range}

@property
def hbound_abs_diff(self):
    return abs(self.count - self.cnt_range[1])

@property
def closest_bound(self):
    # return closest bound based on min abs diff between count and bound
    return min(self._bounds_abs_diff, key=self._bounds_abs_diff.get)
```
* `cnt_range` [ *tuple: 2* ]
    * Countable colony numbers for a plate type.
* `in_between` [ *bool* ]
    * If `count` within countable range.
* `sign` [ *str* ]
    * Sign for reported count if all `count` values are outside the acceptable range.
    * Used in `CalCFU._calc_no_dil_valid`.
* `_bounds_abs_diff` [ *dict* ]
    * Absolute differences of `count` and low and high `cnt_ranges`.
* `hbound_abs_diff` [ *int* ]
    * Absolute difference of `count` and high of `cnt_range`.
    * Used in 
* `closest_bound` [ *int* ]
    * Closest count in `cnt_range` to `count`.
    * Based on minimum absolute difference between `count` and `cnt_range`s\. 
      The smaller the difference, the closer the `count` is to a bound.
---

## `CalCFU`
The calculator is contained in the `CalCFU` dataclass.
Using the previously created `Plate` instances, a `CalCFU` instance is created.

```python
from calcfu.calculator import CalCFU

# Setup calculator with two PAC plates that contain a weighed sample.
calc = CalCFU(plates=[plates_1, plates_2])
```

### Fields
Each instance of CountCalculator is initialized with a list of the plates to be calculated:

Arguments:
* `plates` [ *list* ]
    * Contains Plate instances. 
    * Validated via `__post_init__` method.
    
```python
@dataclass(frozen=True, order=True)
class CalCFU(CalcConfig):
    plates: List
```

### Properties

```python
@property
def valid_plates(self):
    return [plate for plate in self.plates if plate.in_between]

@property
def reported_units(self):
    # grab first plate and use plate type. should be all the same
    return f"{self.plates[0].plate_type}{self.WEIGHED_UNITS.get(self.plates[0].weighed)}"
```

* `valid_plates` [ *list* ]
    * Plates that have acceptable counts for their plate type.
* `reported_units` [ *str* ]
    * Units based on plate type and if weighed.
    * Estimated letter added in `self.calculate()`

### Methods

---

Two methods are available for use with the CountCalculator instance: 
* `calculate`
* `bank_round`


### `calculate(self)`

This method is the "meat-and-potatoes" of the script. 
It calculates the reported/adjusted count based on the plates given. 

Optional arguments:

* `round_to` [ *int* ]
    * Digit to round to. Default is 1.
        * Relative to leftmost digit (0). *Python is 0 indexed*.
    * ex. Round to 1: 2(5),666 
    * ex. Round to 3: 25,6(6)6
* `report_count` [ *bool* ]
    * Option to return reported count or unrounded, unlabeled adjusted count.
    
First, each plate is checked to see if its count is in between the accepted count range.
Based on the number of valid plates, a different method is used to calculate the result.

```python
def calculate(self, round_to=2, report_count=True):
    valid_plates = self.valid_plates
    # assign empty str to sign var. will be default unless no plate valid
    sign = ""
    # track if estimated i.e. no plate is valid.
    estimated = False

    if len(valid_plates) == 0:
        sign, adj_count = self._calc_no_dil_valid()
        estimated = True
    elif len(valid_plates) == 1:
        # only one plate is valid so multiple by reciprocal of dil.
        valid_plate = valid_plates[0]
        adj_count = valid_plate.count * (10 ** abs(valid_plate.dilution))
    else:
        adj_count = self._calc_multi_dil_valid()

    if report_count:
        units = f"{('' if not estimated else 'e')}{self.reported_units}"
        # add sign, thousands separator, and units
        return f"{sign}{'{:,}'.format(self.bank_round(adj_count, round_to))} {units}"
    else:
        return adj_count
```


### `calc_no_dil_valid(self, report_count)`
This function runs when *no plates have valid counts*.

Arguments:
* `report_count` [ *bool* ]
    * Same as `calculate`.    

Procedure:
1. Reduce the `self.plates` down to one plate by checking adjacent plates' `hbound_abs_diff`. 
   * **The plate with the smallest difference is closest to the highest acceptable count bound.**
       * [NCIMS 2400a.16.h](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf#page=8) | [NCIMS 2400a-4.17.h](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf#page=11)
   * `Ex. |267 - 250| = 17 and |275 - 250| = 25` 
   * `17 < 25 so 267 is closer to 250 than 275.`
2. Set throwaway variable `value` to `count` or `closest_bound` based on if reported count needed.
3. Finally, return `sign` and multiply the closest bound by the reciprocal of the dilution.
    * [NCIMS 2400a.16.l](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf#page=8) | [NCIMS 2400a-4.17.h](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf#page=11)
    
``` python
def _calc_no_dil_valid(self, report_count):     
    # Use reduce to reduce plates to a single plate:
    #   plate with the lowest absolute difference between the hbound and value
    closest_to_hbound = reduce(lambda p1, p2: min(p1, p2, key=lambda x: x.hbound_abs_diff), self.plates)

    # if reporting, use closest bound; otherwise, use count.
    value = closest_to_hbound.closest_bound if report_count else closest_to_hbound.count
    
    return closest_to_hbound.sign, value * (10 ** abs(closest_to_hbound.dilution))
```

### `calc_multi_dil_valid(self)`
This method runs if *multiple plates have valid counts*.

Variables:
* `main_dil` [ *int* ]
    * The lowest dilution of the `valid_plates`. 
* `dil_weights` [ *list* ]
    * The weights each dilution/plate contributes to the total count.
* `div_factor` [ *int* ]
    * The sum of `dil_weights`. Part of the denominator of the weighted averaged.

Procedure:
1. First, sum counts from all valid plates (`plates_1` and `plates_2`).

![](docs/figures/total.png)

2. If all plates are the same dilution, set `div_factor` to the total number of valid plates.
    * Each plate has equal weight in `div_dactor`.
    * [NCIMS 2400a.16.l.1](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf#page=8) | 
      [NCIMS 2400a-4.17.e](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf#page=11)
3. Otherwise, we will take a weighted average taking into account how each dilution contributes to the ```div_factor```.

![](docs/figures/div_factor.png)

4. Each dilution will have a *weight* of how much it contributes to the total count (via the ```div_factor```)
    * If the plate dilution is the ```main_dil```, set the dilution's weight to 1. 
        * **This value is the ```main_dil```'s weight towards the total count.** 
        * The least diluted plate contributes the largest number of colonies 
          to the overall count. It will always be 1 serves to normalize the effect of the other dilutions.
        * [NCIMS 2400a.16.l.1](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf#page=8) |
          [NCIMS 2400a-4.17.e](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf#page=11)
    * If it is not, subtract the absolute value of ```main_dil``` by the absolute value of ```plate.dilution```.
        * By raising 10 to the power of ```abs_diff_dil```, **the plate dilution's weight - relative to ```main_dil``` - is calculated.** 
5. Each dilution weight is then multiplied by the number of plates used for that dilution. 
6. The sum of all dilution weights in ```dil_weights``` is the division weight, ```div_factor```.
7. Dividing the ```total``` by the product of ```div_factor``` and ```main_dil``` yields the adjusted count.
   
![](docs/figures/adj_count.png)


```python
def _calc_multi_dil_valid(self):
    valid_plates = self.valid_plates
    total = sum(plate.count for plate in valid_plates)
    main_dil = max(plate.dilution for plate in valid_plates)
    # If all plates have the same dilution.
    if all(plate.dilution == valid_plates[0].dilution for plate in valid_plates):
        # each plates is equally weighed because all the same dil
        div_factor = sum(1 * plate.num_plts for plate in valid_plates)
    else:
        dil_weights = []
        for plate in valid_plates:
            if plate.dilution == main_dil:
                dil_weights.append(1 * plate.num_plts)
            else:
                # calculate dil weight relative to main_dil
                abs_diff_dil = abs(main_dil) - abs(plate.dilution)
                dil_weights.append((10 ** abs_diff_dil) * plate.num_plts)

        div_factor = sum(dil_weights)

    return int(total / (div_factor * (10 ** main_dil)))
```

### Once a value is returned...

### `bank_round(value, place_from_left)` 

This method rounds values using banker's rounding. 
String manipulation was used rather than working with floats to [avoid rounding errors](https://docs.python.org/3/tutorial/floatingpoint.html#tut-fp-issues). 

Arguments:
* `value` [ *int* ]
    * Value to be rounded.
* `place_from_left` [ *int* ]
    * Digit to round to. **Leftmost digit is 1 (NOT 0)**.
    * See `calculate()` for examples.

Variables:
* `value_len` [ *int* ]
    * Len of *string value*.
* `str_abbr_value` [ *str* ]
    * Abbreviated value as string. 
    * Sliced to only allow 1 digit before rounded digit.
        * Python rounding behavior changes based on digits after.
            * [Built-in Functions - round()](https://docs.python.org/3/library/functions.html?highlight=round#round)
        * [NCIMS 2400a.19.c.1.a-b](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf#page=10) | 
          [NCIMS 2400a-4.19.d.1.a-b](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf#page=13)
* `str_padded_value` [ *str* ]
    * Zero-padded value as string.
* `adj_value` [ *int* ]
    * Abbreviated, padded value as integer.
* `adj_place_from_left`
    * Adjusted index for base python `round()`. Needs to be ndigits from decimal point.
    * `Ex. round(2(1)5., -1) -> 220`   
* `final_val` [ *int* ]
    * Rounded value.
    
```python
@staticmethod
def bank_round(value, place_from_left):
    if isinstance(value, int) and isinstance(place_from_left, int):
        # Length of unrounded value.
        value_len = len(str(value))
        # remove digits that would alter rounding only allowing 1 digit before desired place
        str_abbr_value = str(value)[0:place_from_left + 1]
        # pad with 0's equal to number of removed digits
        str_padded_value = str_abbr_value + ("0" * (value_len - len(str_abbr_value)))
        adj_value = int(str_padded_value)
        # reindex place_from_left for round function.
        # place_from_left = 2 for 2(5)553. to round, needs to be -3 so subtract length by place and multiply by -1.
        adj_place_from_left = -1 * (value_len - place_from_left)
        final_val = round(adj_value, adj_place_from_left)
        return final_val
    else:
        raise ValueError("Invalid value or place (Not an integer).")
```

Example:
```python 
result = bank_round(value=24553, place_from_left=2)
```

1. Find the length of the value as a string. 
    * `value_len=5` 
2. Abbreviate value as string. 
    * `str_abbr_value="245"`
3. Pad value as string out to original length. 
    * `str_padded_value="24500"`
4. Convert padded value back to a number. 
    * `adj_value=24500`
5. Reindex `place_from_left` for the `round` function. 
    * `adj_place_from_left=-3`
6. Round `adj_value` with `place_from_left`, the new index. 
    * `result=24000`
---

### For full examples and tests, view [test_calc.py](test_calc.py)...

---

## References
1. [NCIMS 2400a: SPC - Pour Plate (Oct 2013)](http://ncims.org/wp-content/uploads/2017/01/2400a-Standard-and-Coliform-Plate-Count-rev.-10-13.pdf)
2. [NCIMS 2400a-4: SPC - Petrifilm (Nov 2017)](http://ncims.org/wp-content/uploads/2017/12/2400a-4-Petrifilm-Aerobic-Coliform-Count-Rev.-11-17-1.pdf)
3. [Built-in Functions - round()](https://docs.python.org/3/library/functions.html?highlight=round#round)
4. [Floating Point Arithmetic: Issues and Limitations](https://docs.python.org/3/tutorial/floatingpoint.html#tut-fp-issues)









