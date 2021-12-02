import pathlib
import argparse
from calcfu.calculator import CalCFU
from calcfu.plate import Plate


def read_r_results(path):
  """
  
  
  """
  
  sorted_plates = [[Plate("PAC", pair[0], -2, False, 1), Plate("PAC", pair[1], -3, False)]
                             for pair in sorted_pairs]
  cfus = [CalCFU(pair).calculate() for pair in sorted_plates]
  print(f"Date: {date} | Pairs: {len(sorted_pairs)} | Total Plates: {len(sorted_pairs) * 2}")
  [print(f"{pair}\n{res}") for pair, res in zip(sorted_pairs, cfus)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument()



if __name__ == "__main__":
    main()
