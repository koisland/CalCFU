import unittest
from calcfu.plate import Plate
from calcfu.calculator import CalCFU
from calcfu.exceptions import *


class TestCalc(unittest.TestCase):

    def setUp(self):
        self.plt_1 = Plate("PAC", 35, -3, False, 1)
        self.plt_2 = Plate("PAC", 212, -2, False, 1)

        self.plt_3 = Plate("RAC", 12, -2, True, 1)
        self.plt_4 = Plate("RAC", 13, -1, True, 1)

        self.plt_5 = Plate("SPC", 19, -3, False, 1)
        self.plt_6 = Plate("SPC", 521, -2, False, 1)
        
        self.plt_7 = Plate("PAC", 0, -3, False, 1)
        self.plt_8 = Plate("PAC", 0, -2, False, 1)
        
        self.plt_9 = Plate("PAC", 999, -3, False, 1)
        self.plt_10 = Plate("PAC", 999, -2, False, 1)

    def test_create_plt(self):
        with self.assertRaises(PlateError):
            plt_invalid_count_type = Plate(plate_type="PAC", count="12", dilution=-2, weighed=True, num_plts=1)
            plt_invalid_dilution_type = Plate(plate_type="PAC", count=12, dilution="-2", weighed=True, num_plts=1)
            plt_invalid_weighed = Plate(plate_type="PAC", count=12, dilution=-2, weighed="True", num_plts=1)
            plt_invalid_num_plts_type = Plate(plate_type="PAC", count=12, dilution=-2, weighed=True, num_plts="1")

            # Not highlighted because error not due to explicit typing
            plt_invalid_dilution_num = Plate(count=12, plate_type="PAC", dilution=-20, weighed=True, num_plts=1)
            plt_invalid_plate_categ = Plate(count=12, plate_type="3M PAC", dilution=-2, weighed=True, num_plts=1)

    def test_plt_prop(self):
        # all the other properties are simple and not worth testing.
        # closest_bound is the most complicated property, I guess?
        self.assertEqual(self.plt_1.closest_bound, 25)
        self.assertEqual(self.plt_3.closest_bound, 25)
        self.assertEqual(self.plt_10.closest_bound, 250)

    def test_setup_calc(self):

        with self.assertRaises(CalCFUError):
            calc_invalid_plates = CalCFU(plates={})
            calc_invalid_num_plates = CalCFU(plates=[self.plt_1])
            # plt_1 is weighed but plt_3 is not.
            calc_invalid_weigh_plates = CalCFU(plates=[self.plt_1, self.plt_3])

            # Not highlighted because error not due to explicit typing
            calc_invalid_plates_type = CalCFU(plates=[self.plt_1, "self.plt_2"])

    def test_bank_round(self):
        with self.assertRaises(ValueError):
            CalCFU.bank_round(25.0, 1)
            CalCFU.calc_1.bank_round(25, "1")

        # first digit to left is 1, second digit is 2, and so on.
        self.assertEqual(CalCFU.bank_round(147, 2), 150)
        self.assertEqual(CalCFU.bank_round(2637, 2), 2600)
        self.assertEqual(CalCFU.bank_round(24553, 2), 24000)
        self.assertEqual(CalCFU.bank_round(25556, 2), 26000)
        self.assertEqual(CalCFU.bank_round(3555, 2), 3600)

    def test_calculate(self):
        # Plates 1 & 2.
        self.calc_1 = CalCFU(plates=[self.plt_1, self.plt_2])
        # 35 + 212 = 247 / 0.011 = 22454.5454
        self.assertEqual(self.calc_1.calculate(report_count=False), 22454)
        self.assertEqual(self.calc_1.calculate(), "22,000 PAC / mL")

        # Plates 3 & 4.
        self.calc_2 = CalCFU(plates=[self.plt_3, self.plt_4])
        # Plate 4 (13) is closer to 250. 13 / 0.1 = 130
        self.assertEqual(self.calc_2.calculate(report_count=False), 130)
        self.assertEqual(self.calc_2.calculate(), "<250 eRAC / g")

        # Plates 5 & 6
        self.calc_3 = CalCFU(plates=[self.plt_5, self.plt_6])
        # Plate 5 (19) is closer to 250. 19 / 0.001 = 19000
        self.assertEqual(self.calc_3.calculate(report_count=False), 19000)
        self.assertEqual(self.calc_3.calculate(), "<25,000 eSPC / mL")

        # Plates 7 & 8
        self.calc_4 = CalCFU(plates=[self.plt_7, self.plt_8])
        # Both Plate 7 (0) and Plate 8 (0) are below the countable range and are equidistant from 250. 
        # Therefore, take lowest dilution plate, Plate 8. 0 / 0.01 = 0
        self.assertEqual(self.calc_4.calculate(report_count=False), 0)
        self.assertEqual(self.calc_4.calculate(), "<25,000 ePAC / mL")

        # Plates 9 & 10
        self.calc_5 = CalCFU(plates=[self.plt_9, self.plt_10])
        # Both Plate 9 (0) and Plate 10 (0) are above the countable range and are equidistant from 250. 
        # Therefore, take highest dilution plate, Plate 9. 999 / 0.001 = 999000
        self.assertEqual(self.calc_5.calculate(report_count=False), 999000)
        self.assertEqual(self.calc_5.calculate(), ">250,000 ePAC / mL")
        
    def test_plate_operations(self):
        test_1 = {"one": Plate("PAC", 12, -1, True, 1), 
                  "one_copy": Plate("PAC", 12, -1, True, 1)}
        self.assertTrue(test_1["one"] == test_1["one_copy"])

