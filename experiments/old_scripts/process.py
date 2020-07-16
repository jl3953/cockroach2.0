#!/usr/bin/env python3

import argparse
import csv

def main():

    parser = argparse.ArgumentParser(description="I don't give a shit.")
    parser.add_argument("logs", nargs="+", help="Figure it out yourself.")
    parser.add_argument("--csv", type=str, required=True, help="Keep trying.")

    args = parser.parse_args()
    with open(args.csv, "w") as w:
        writer = csv.writer(w, delimiter=",")
        for f in args.logs:
            print(f.split("-"))
            skew = float(f.split("-")[1])
            with open(f, "r") as stats:
                last_line = stats.readlines()[-1]
                writer.writerow([skew] + last_line.split()[2:])

    

if __name__=="__main__":
    main()
