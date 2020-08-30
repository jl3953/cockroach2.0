#!/usr/bin/env python3

import argparse
import operator
import os

import bash_imitation
import exp_lib
import lib
import plotlib

FPATH = os.path.dirname(os.path.realpath(__file__))
LT_GNUPLOT = os.path.join(FPATH, "lt.gp")


def parse_config_file(baseline_file, lt_file):
  exp, skews = exp_lib.create_experiment(FPATH, baseline_file)
  variation_config = exp_lib.read_variation(lt_file)
  variation_config["skews"] = skews

  return exp, variation_config


def last_adjustments(max_concurrency):
  """ Returns:
	Final stage tinkering with the concurrency.
	"""

  return max_concurrency - 1


def sample_lt(start, end, step_size, exp, skew):
  data = []
  for concurrency in range(start, end, step_size):
    exp["benchmark"]["run_args"]["concurrency"] = [concurrency]
    original_outdir = exp["out_dir"]
    exp["out_dir"] += "_" + str(concurrency)
    skew_list_with_one_item = [skew]
    exps = lib.vary_zipf_skew(exp, skew_list_with_one_item)

    for e in exps:
      lib.cleanup_previous_experiment(exp)
      lib.init_experiment(exp)
      lib.warmup_cluster(e)
      lib.run_bench(e)

    temp_dir = os.path.join(exp["out_dir"], "skew-0")
    temp_csv = os.path.join(temp_dir, "lt.csv")
    datum = {"concurrency": concurrency}
    datum.update(plotlib.accumulate_workloads_per_skew(exp, temp_dir)[0])
    data.append(datum)
    exp["out_dir"] = original_outdir

    # plotting data for viewing
    report_csv_args = {"filename": temp_csv}
    report_csv_data(data, report_csv_args, mode="a")

    bash_imitation.gnuplot(LT_GNUPLOT, temp_csv, temp_dir, 214, skew)

  return data


def find_optimal_concurrency(exp, variations, skew, is_view_only):
  """ Returns:
	Max concurrency, csv data
	"""

  start = variations["variation"]["concurrency"][0]
  step_size = variations["variation"]["step_size"]
  end = variations["variation"]["concurrency"][1] + step_size

  # print(sample_lt(start, end, step_size, exp, skew))

  data = []
  max_concurrency = -1
  while step_size > 0:
    for concurrency in range(start, end, step_size):
      exp["benchmark"]["run_args"]["concurrency"] = [concurrency]
      original_outdir = exp["out_dir"]
      exp["out_dir"] += "_" + str(concurrency)
      skew_list_with_one_item = [skew]
      exps = lib.vary_zipf_skew(exp, skew_list_with_one_item)

      for e in exps:
        lib.cleanup_previous_experiment(exp)
        lib.init_experiment(exp)
        lib.warmup_cluster(e)
        if not is_view_only:
          lib.run_bench(e)

      datum = {"concurrency": concurrency}
      datum.update(plotlib.accumulate_workloads_per_skew(exp, os.path.join(exp["out_dir"], "skew-0"))[0])
      data.append(datum)
      exp["out_dir"] = original_outdir

    max_concurrency = max(data, key=operator.itemgetter("ops/sec(cum)"))["concurrency"]
    concurrency = max_concurrency
    start = concurrency - step_size
    end = concurrency + step_size
    step_size = int(step_size / 2)

  max_concurrency = last_adjustments(max_concurrency)
  return max_concurrency, data
  return None


def report_csv_data(csv_data, args, mode="w"):
  """ Outputs csv data to file storage.

	Args:
		csv_data
		args (dict): metadata for path of csv file, driver nodes, etc.
	  mode (str): "w" or "a"

	Returns:
		None.

	"""
  data = sorted(csv_data, key=lambda i: i["concurrency"])
  _ = plotlib.write_out_data(data, args["filename"], mode)


def report_optimal_parameters(max_concurrency, args):
  """ Outputs optimal concurrency to file storage as
	an override.ini file, readable by driver script.

	Args:
		max_concurrency (int)
		args (dict): metadata for path of file, etc.

	Returns:
		None.

	"""

  with open(args["filename"], "w") as f:
    f.write("[benchmark]\n")
    f.write("concurrency = " + str(max_concurrency) + "\n")


def run_single_trial(find_concurrency_args, report_params_args,
                     report_csv_args, skew, is_view_only):
  set_params, variations = parse_config_file(find_concurrency_args["baseline_file"],
                                             find_concurrency_args["lt_file"])

  max_concurrency, csv_data = find_optimal_concurrency(set_params,
                                                       variations, skew, is_view_only)
  report_csv_data(csv_data, report_csv_args, skew)

  report_optimal_parameters(max_concurrency, report_params_args)
  print(max_concurrency)


def main():
  parser = argparse.ArgumentParser(description="find latency throughput graph")
  parser.add_argument('baseline_file', help="baseline_file, original param file")
  parser.add_argument('lt_file', help="lt_file, for example lt.ini")
  parser.add_argument('params_output', help="abs path of output param file")
  parser.add_argument('csv_output', help="abs path of output csv file")
  parser.add_argument('skew', type=float, help="skew with which latency throughput is run")
  parser.add_argument('--is_view_only', action='store_true',
                      help='only runs warmup for short testing')
  args = parser.parse_args()

  find_concurrency_args = {
    "baseline_file": args.baseline_file,
    "lt_file": args.lt_file,
  }
  report_csv_args = {
    "filename": args.csv_output,
  }

  print(report_csv_args)

  report_params_args = {
    "filename": args.params_output,
  }

  run_single_trial(find_concurrency_args, report_params_args, report_csv_args,
                   args.skew, args.is_view_only)


if __name__ == "__main__":
  main()
