#!/usr/bin/env python3

import argparse
import collections
import configparser
import csv
import datetime
import enum
import json
import os
import sys

import numpy

import bash_imitation
import exp_lib
import lib

FPATH = os.path.dirname(os.path.realpath(__file__))
COPYALL_SH = os.path.join(FPATH, "copyall.sh")
LT_EXECUTABLE = os.path.join(FPATH, "lt_driver.py")
DRIVER_EXECUTABLE = os.path.join(FPATH, "driver.py")
LT_GNUPLOT = os.path.join(FPATH, "lt.gp")
DRIVER_GNUPLOT = os.path.join(FPATH, "plot.gp")
BOX_AND_WHISKERS_GNUPLOT = os.path.join(FPATH, "box_and_whiskers.gp")


class Stage(enum.Enum):
  """ Represents the stages of the pipeline."""

  CREATE_NEW_DIRS = "create_new_dirs"
  METADATA = "metadata"
  LATENCY_THROUGHPUT = "latency_throughput"
  DRIVER = "driver"
  COPY_OVER = "copy_over"
  END = "end"

  def __str__(self):
    return self.value

  @staticmethod
  def next(stage):
    if stage == Stage.CREATE_NEW_DIRS:
      return Stage.METADATA
    elif stage == Stage.METADATA:
      return Stage.LATENCY_THROUGHPUT
    elif stage == Stage.LATENCY_THROUGHPUT:
      return Stage.DRIVER
    elif stage == Stage.DRIVER:
      return Stage.COPY_OVER
    elif stage == Stage.COPY_OVER:
      return Stage.END


def extract_human_tag(config_file):
  """ Reads the human tag from the config file.

	Args:
		config_file (str): .ini file
	
	Returns:
		human tag
	"""

  config = configparser.ConfigParser()
  config.read(config_file)

  return config["DEFAULT"]["LOGS_DIR"]


def extract_skews(config_file):
  """ Reads the skews from the config file.

	Args:
		config_file (str): .ini file

	Returns:
		list of skews
	"""

  config = configparser.ConfigParser()
  config.read(config_file)

  skews = json.loads(config["benchmark"]["skews"])

  return skews


def generate_testrun_name(suffix):
  """ Creates a test run directory's name in the format
	test_<timestamp>_<suffix>.

	Args:
		suffix (str): human readable tag
	
	Returns:
		generated name.
	"""

  timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
  name = "test_{0}_{1}".format(timestamp, suffix)

  return name


def create_directories(location, suffix):
  """ Creates the run's directories.

	Args:
		suffix (str): appending dir name with a human readable tag.
	
	Returns:
		Name of all created directories
	"""

  overall_dir = bash_imitation.create_dir(location, generate_testrun_name(suffix))
  graph_dir = bash_imitation.create_dir(overall_dir, "graphs")
  raw_out_dir = bash_imitation.create_dir(overall_dir, "raw_out")
  csv_dir = bash_imitation.create_dir(overall_dir, "csv_files")

  return overall_dir, graph_dir, raw_out_dir, csv_dir


def reconstruct_directories(location, existing_directory):
  """ Reconstructs the structure of the existing directory and returns
	the inner directories.

	Args:
		location (str): location of existing directory
		existing_directory (str): name of existing directory

	Return:
		Name of all directories.
	"""

  overall_dir = os.path.join(location, existing_directory)
  graph_dir = os.path.join(overall_dir, "graphs")
  raw_out_dir = os.path.join(overall_dir, "raw_out")
  csv_dir = os.path.join(overall_dir, "csv_files")

  return overall_dir, graph_dir, raw_out_dir, csv_dir


def copy_and_create_metadata(location, config_file):
  """ Copies config file as params.ini, creates a metadata file of
	current git hash.

	Args:
		location (str): location in which all files are copied / created
		config_file (str): config file to be copied.
	
	Return: 
		None.
	"""

  # copy parameter file
  cmd = "cp {0} {1}".format(config_file, os.path.join(location, "params.ini"))
  lib.call(cmd, "could not copy params file.")

  # copy "copyall.sh" script
  cmd = "cp {0} {1}".format(COPYALL_SH, os.path.join(location, "copyall.sh"))
  lib.call(cmd, "could not copy copyall.sh")

  # create git hash file
  with open(os.path.join(location, "git_commit_hash.txt"), "w") as f:
    git_commit_hash = bash_imitation.git_commit_hash()
    f.write("commit_hash: " + git_commit_hash)

    submodule = "vendor"
    git_submodule_hash = bash_imitation.git_submodule_commit_hash(submodule)
    f.write("\nsubmodule_commit_hash: " + git_submodule_hash)


def call_latency_throughput(baseline_file, lt_file, params_file, csv_file, skew, use_manual_sampling):
  """ Calls the latency throughput script.

	Args:
		location (str): absolute path of location directory.
		baseline_file (str): original params config file, abs path
		lt_file (str): latency throughput params config, abs path
		params_file (str): abs path of param output file
		csv_file (str): abs path of csv file
		skew (double)
	
	Returns:
		None.
	"""

  # call lt script
  cmd = "{0} {1} {2} {3} {4} {5} {6}".format(
    LT_EXECUTABLE, baseline_file, lt_file, params_file, csv_file, skew, use_manual_sampling)
  lib.call(cmd, "lt_driver script failed")


def move_logs(baseline_file, dest):
  """ Moves logs generated by a run of the latency throughput script.

	Args:
		baseline_file (str): original params config file, abs path, used to
			construct source log directory.
		dest (str): abs path of new log directory.

	Returns:
		None.
	"""

  # move the generated logs
  src_logs = exp_lib.find_log_dir(FPATH, baseline_file)
  bash_imitation.move_logs(src_logs, dest)


def construct_checkpoint_file(trial):
  return "checkpoint_trial_{0}.csv".format(trial)


def calculate_and_output_final_override(trials, overall_dir, override_file):
  """ Calculates the median concurrency (in param files) and outputs into
	override_file.

	Args:
	  trials (int)
	  overall_dir(str)
		override_file (str): output override file

	Returns:
		None.
	"""

  concurrencies_over_trials = []
  skews = []
  for trial in range(1, trials + 1):
    checkpoint = os.path.join(overall_dir, construct_checkpoint_file(trial))
    skews, concurrencies = exp_lib.read_skew_concurrency_pairs(checkpoint)
    concurrencies_over_trials.append(concurrencies)

  median_concurrencies = [int(m) for m in numpy.median(concurrencies_over_trials, axis=0)]

  exp_lib.write_skew_concurrency_overrides(skews, median_concurrencies, override_file)

  # print("jenndebug", skews, concurrencies_over_trials)

  # with open(override_file, "w") as f:
  #   f.write("[benchmark]\n")
  #   medians = numpy.median(concurrencies_over_trials, axis=0)
  #   write_out = [int(m) for m in medians]
  #   f.write("concurrency = " + str(write_out))


def driver(baseline_file, override_file, csv_dir, csv_file):
  """ Calls driver script."""

  cmd = ("{0} --benchmark --driver_node localhost "
         "--ini_files {1} "
         "--override {2} "
         "--csv_path {3} "
         "--csv_file {4}").format(
    DRIVER_EXECUTABLE, baseline_file, override_file, csv_dir, csv_file)
  lib.call(cmd, "driver script failed")


def write_box_and_whiskers(output_csv, curve):
  """ Writes out box and whiskers plot."""

  with open(output_csv, "w") as f:
    writer = csv.DictWriter(f, fieldnames=curve[0].keys(), delimiter="\t")
    writer.writeheader()

    for box_and_whisker in curve:
      writer.writerow(box_and_whisker)


def calculate_box_and_whiskers(csvs, x_axis, y_axis):
  """ Calculates box and whiskers plot.

	Args:
		csvs (list[str]): list of csv files.
		x_axis (str): attribute that serves as x_axis
		y_axis (str): attribute that serves as the y_axis

	Returns:
		None.
	"""

  group_by_x = collections.defaultdict(lambda: [])
  for csv_file in csvs:
    with open(csv_file, "r") as f:
      reader = csv.DictReader(f, delimiter='\t')
      for row in reader:
        x = float(row[x_axis])
        point = float(row[y_axis])
        group_by_x[x].append(point)

  print("jenndebug bawp", group_by_x)

  plot = []
  for x, points in group_by_x.items():
    box_and_whisker = {
      x_axis: x,
      "whisker_min": min(points),
      "box_min": numpy.percentile(points, 25),
      "median": numpy.median(points),
      "box_high": numpy.percentile(points, 75),
      "whisker_high": max(points),
    }
    plot.append(box_and_whisker)

  sorted(plot, key=lambda box_and_whisker: box_and_whisker[x_axis])

  return plot


def calculate_and_plot_box_and_whiskers(csvs, csv_dir, graph_dir):
  """ Calculates and plots box and whiskers plot for driver csv files.

	Args:
		csvs (list[str]): csv files (with p50, tp, etc.)

	Returns:
		None.
	"""

  # throughput box and whiskers plot (bawp)
  tp_bawp_csv = os.path.join(csv_dir, "tp_box_and_whiskers.csv")
  tp_bawp_png = os.path.join(graph_dir, "tp_box_and_whiskers.png")
  tp_curve = calculate_box_and_whiskers(csvs, "skew", "ops/sec(cum)")
  print("jenndebug", csv_dir)
  write_box_and_whiskers(tp_bawp_csv, tp_curve)
  bash_imitation.gnuplot(BOX_AND_WHISKERS_GNUPLOT, tp_bawp_png, tp_bawp_csv,
                         "'throughput(txns/sec)'")


# p50 box and whiskers plot
# p50_bawp_csv = os.path.join(csv_dir, "p50_box_and_whiskers.csv")
# calculate_box_and_whiskers(p50_bawp, csvs, "skew", "p50(ms)")
# bash_imitation.gnuplot(BOX_AND_WHISKERS_GNUPLOT, p50_bawp, graph_dir)


def copy_to_permanent_storage(overall_dir):
  """ Calls script within directory to copy all files in directory to permanent
	storage.

	Args:
		overall_dir (str): overall directory where everything is located.

	Return:
		None.
	"""

  """
	copy_executable = os.path.join(overall_dir, "copyall.sh")
	lib.call("{0}".format(copy_executable), "could not copy to permanent storage {}".format(overall_dir))
	"""
  return "unimplemented"


def main():
  parser = argparse.ArgumentParser(description="coordinator script for pipeline")
  parser.add_argument("config", help=".ini file with config params, params.ini")
  parser.add_argument("lt_config", help=".ini file with latency throughput params")
  parser.add_argument("--lt_trials", type=int, default=1,
                      help="number of trials to run latency throughput.")
  parser.add_argument("--driver_trials", type=int, default=1,
                      help="number of trials to run driver script.")
  parser.add_argument("--start_stage", type=Stage, default=Stage.CREATE_NEW_DIRS,
                      choices=[stage for stage in Stage],
                      help="which stage to start running at. Useful for testing.")
  parser.add_argument("--end_stage", type=Stage, default=Stage.LATENCY_THROUGHPUT,
                      choices=[stage for stage in Stage],
                      help="which stage to stop running after. Useful for testing.")
  parser.add_argument("--existing_directory",
                      help="existing directory to use. Useful for testing.")
  parser.add_argument("--use_manual_sampling", action='store_true',
                      help="requires babysitting the sampling process.")

  args = parser.parse_args()
  args.config = os.path.join(FPATH, args.config)  # replace with abs path
  args.lt_config = os.path.join(FPATH, args.lt_config)

  if args.start_stage is not Stage.CREATE_NEW_DIRS and not args.existing_directory:
    print("You must provide an existing test run directory with this stage.")
    parser.print_help()
    return -1

  # Starting pipeline
  stage = args.start_stage
  overall_dir, graph_dir, raw_out_dir, csv_dir = None, None, None, None

  # stage creating new directories
  if stage == Stage.CREATE_NEW_DIRS:
    human_tag = extract_human_tag(args.config)
    overall_dir, graph_dir, raw_out_dir, csv_dir = create_directories(
      os.path.join(FPATH, ".."), human_tag)
    if stage == args.end_stage:
      return 0
    stage = Stage.next(stage)
  else:
    overall_dir, graph_dir, raw_out_dir, csv_dir = reconstruct_directories(
      os.path.join(FPATH, ".."), args.existing_directory)

  # stage metadata
  if stage == Stage.METADATA:
    copy_and_create_metadata(overall_dir, args.config)
    if stage == args.end_stage:
      return 0
    stage = Stage.next(stage)

  # file locations
  override_file = os.path.join(overall_dir, "override.ini")

  # stage latency throughput
  if stage == stage.LATENCY_THROUGHPUT:

    # param_outputs = []
    for trial in range(1, args.lt_trials + 1):
      # skews_for_trial = []

      # checkpoint file for durable storage, since lt process takes the longest
      checkpoint = os.path.join(overall_dir, construct_checkpoint_file(trial))

      for s in extract_skews(args.config):
        param_output = os.path.join(overall_dir, "param_trial_{0}_{1}.ini".format(trial, s))
        # skews_for_trial.append(param_output)
        lt_csv = os.path.join(csv_dir, "lt_trial_{0}_{1}.csv".format(trial, s))
        lt_logs = os.path.join(raw_out_dir, "lt_logs_trial_{0}_{1}".format(trial, s))

        call_latency_throughput(args.config, args.lt_config,
                                param_output, lt_csv, s, args.use_manual_sampling)

        # checkpointing
        concurrency = exp_lib.read_concurrency(param_output)
        exp_lib.write_skew_concurrency_pair(s, concurrency, checkpoint)

        move_logs(args.config, lt_logs)
        bash_imitation.gnuplot(LT_GNUPLOT, lt_csv, graph_dir, trial, s)

      # param_outputs.append(skews_for_trial)

    calculate_and_output_final_override(args.lt_trials, overall_dir, override_file)

    if stage == args.end_stage:
      return 0
    stage = Stage.next(stage)

  # stage driver
  if stage == stage.DRIVER:

    csvs = []
    for trial in range(1, args.driver_trials + 1):
      driver_logs = os.path.join(raw_out_dir, "driver_logs_trial_{0}".format(trial))
      driver_file = "driver_trial_{0}.csv".format(trial)
      driver_csv = os.path.join(csv_dir, driver_file)
      csvs.append(driver_csv)

      # warning: driver script has too many dependencies on the csv_dir
      # and csv_file being separated for me to bother right now. Implicitly
      # assume that the abs path is just the joining of the dir and filename.
      driver(args.config, override_file, csv_dir, driver_file)
      move_logs(args.config, driver_logs)
      bash_imitation.gnuplot(DRIVER_GNUPLOT, driver_csv, graph_dir, trial)

    calculate_and_plot_box_and_whiskers(csvs, csv_dir, graph_dir)

    if stage == args.end_stage:
      return 0
    stage = Stage.next(stage)

  # copy over to permanent storage
  if stage == stage.COPY_OVER:
    copy_to_permanent_storage(overall_dir)

    if stage == args.end_stage:
      return 0
    stage = Stage.next(stage)

  return 0


if __name__ == "__main__":
  sys.exit(main())
