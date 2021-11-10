import unittest
from plate import Plate
from calculator import CalCFU


class TestCalc(unittest.TestCase):

    def setUp(self):
        self.plt_1 = Plate("PAC", 35, -3, False, 1)
        self.plt_2 = Plate("PAC", 212, -2, False, 1)

        self.plt_3 = Plate("RAC", 12, -2, True, 1)
        self.plt_4 = Plate("RAC", 13, -1, True, 1)

        self.plt_5 = Plate("CPC", 152, -2, True, 3)
        self.plt_6 = Plate("CPC", 134, -1, True, 3)

        self.plt_7 = Plate("HSCC", 81, 0, True, 1)
        self.plt_8 = Plate("HSCC", 85, 0, True, 1)

        self.plt_9 = Plate("SPC", 19, -2, False, 1)
        self.plt_10 = Plate("SPC", 521, -1, False, 1)

    def test_create_plt(self):
        with self.assertRaises(AssertionError):
            plt_invalid_count_type = Plate(plate_type="PAC", count="12", dilution=-2, weighed=True, num_plts=1)
            plt_invalid_dilution_type = Plate(plate_type="PAC", count=12, dilution="-2", weighed=True, num_plts=1)
            plt_invalid_weighed = Plate(plate_type="PAC", count=12, dilution=-2, weighed="True", num_plts=1)
            plt_invalid_num_plts_type = Plate(plate_type="PAC", count=12, dilution=-2, weighed=True, num_plts="1")

            # Not highlighted because error not due to explicit typing
            plt_invalid_dilution_num = Plate(count=12, plate_type="PAC", dilution=-20, weighed=True, num_plts=1)
            plt_invalid_plate_categ = Plate(count=12, plate_type="3M PAC", dilution=-2, weighed=True, num_plts=1)

    def test_setup_calc(self):

        with self.assertRaises(AssertionError):
            calc_invalid_plates = CalCFU(plates={})
            calc_invalid_num_plates = CalCFU(plates=[self.plt_1])

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
        self.assertEqual(self.calc_1.calculate(), "22000 PAC / mL")

        # Plates 3 & 4.
        self.calc_2 = CalCFU(plates=[self.plt_3, self.plt_4])
        # 13 is closer to 250. 13 / 0.1 = 130
        self.assertEqual(self.calc_2.calculate(report_count=False), "<2500")
        self.assertEqual(self.calc_2.calculate(), "<2500 eRAC / g")

        # Plates 5 & 6
        self.calc_3 = CalCFU(plates=[self.plt_5, self.plt_6])
        print(self.calc_3.calculate(report_count=False))
        print(self.calc_3.calculate())

        # Plates 7 & 8
        self.calc_4 = CalCFU(plates=[self.plt_7, self.plt_8])
        print(self.calc_4.calculate(report_count=False))
        print(self.calc_4.calculate())

        # Plates 9 & 10
        self.calc_5 = CalCFU(plates=[self.plt_9, self.plt_10])
        print(self.calc_5.calculate(report_count=False))
        print(self.calc_5.calculate())

    def test_plate_operations(self):
        test_1 = {"one": Plate("PAC", 12, -1, True, 1), "one_copy": Plate("PAC", 12, -1, True, 1)}
        self.assertTrue(test_1["one"] == test_1["one_copy"])


if __name__ == "__main__":
    unittest.main()
