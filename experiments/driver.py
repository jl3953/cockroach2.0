#!/usr/bin/env python3

import argparse
import exp_lib
import lib
import os
import plotlib
import configparser
import copy


FPATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_LIST = [
	# "new_zipfian_read95.ini",
	# "new_zipfian_write.ini"
	# "new_zipfian_overload.ini"
	# "baseline.ini",
	# "read100.ini",
	 "beep.ini",
]
EXP, SKEWS = exp_lib.create_experiment(FPATH, CONFIG_LIST[0])
DB_QUERY_NODE = "192.168.1.2"


def gather_statistics(exp, skews, collect_only=False):
	""" Warms up cluster to a stable state and gathers statistics.

		Args:
			exp: experimental configuration
			skews: self explanatory
			collect_only: if set, do not warm up machines, assume
				that logs are already generated, and only collect the
				results from them.

		Return:
			None.
	"""

	exps = lib.vary_zipf_skew(exp, skews)
	if not collect_only:
		for e in exps:
			lib.cleanup_previous_experiment(exp)
			lib.init_experiment(exp)
			lib.warmup_cluster(e)
			lib.query_for_shards(DB_QUERY_NODE, e)
			lib.grep_for_term(e, "jenndebug bumped")
			lib.run_bench(e)

	plotlib.plot_shards(exp, skews)
	plotlib.plot_bumps(exp, skews)
		

def generate_skew_curve(exp, skews, view=False, collect=False, prepopulate=False):

	""" Warms up cluster and generates curve over skew space.

		Args:
			exp: experimental configuration
			skews: self-explanatory
			view: if set, only run benchmarks, do not record logs.

		Returns:
			None.
	"""

	exps = lib.vary_zipf_skew(exp, skews)
	for e in exps:
		lib.cleanup_previous_experiment(exp)
		lib.init_experiment(exp)
		
		# insert writes, or just warm up
		if prepopulate:
			lib.prepopulate_cluster(e)
		else:
			lib.warmup_cluster(e)

		if collect:
			lib.query_for_shards(DB_QUERY_NODE, e)
			lib.grep_for_term(e, "jenndebug bumped")
		if not view:
			lib.run_bench(e)
			

def plot(exp, skews, driver_node, csv_path, csv_file, 
		view=False, collect=False, take_over_time=False):

	if take_over_time:
		plotlib.gather_over_time(exp)
		if len(skews) > 1:
			print ("over_time takes only one skew!!")

	if collect:
		plotlib.plot_shards(exp, skews)
		plotlib.plot_bumps(exp, skews)
	if not view:
		plotlib.gnuplot(exp, skews, driver_node, csv_path, csv_file)


def create_trial_outdir(config_filename, i):

	""" Appends number to log directory per trial.
	
	Args:
		config_filename: filename of .ini file.
		i: nth trial
		
	Returns:
		Directory name with trial number appended.
	"""

	config = configparser.ConfigParser()
	config.read(config_filename)
	logs_dir = config["DEFAULT"]["LOGS_DIR"]

	if i > 0:
		logs_dir += "_" + str(i)

	return exp_lib.create_out_dir(FPATH, logs_dir, config["DEFAULT"]["OUT_DIR"])


def main():
	
	parser = argparse.ArgumentParser(description='Start script for cockroach.')
	parser.add_argument('--start', action='store_true', help='starts, or restarts, the cluster.')
	parser.add_argument('--obliterate', action='store_true', help='kills cluster and cleans up, if specified')
	parser.add_argument('--benchmark', action='store_true', help='runs specified benchmark, assumes db is already started')
	parser.add_argument('--ini_files', nargs='*', help='.ini file to read from')
	parser.add_argument('--driver_node')
	parser.add_argument('--csv_path', help="where the generated csv file will go")
	parser.add_argument('--csv_file', help="name of generated csv file")
	parser.add_argument('--override', help='overrides parameters according provided .ini,'
			' only valid when running benchmark')
	parser.add_argument('--view', action='store_true', help='only runs warmup for short testing')
	# parser.add_argument('--logs', action='store_true', help='parses benchmark logs')
	parser.add_argument('--stats', action='store_true', help='gathers statistics on benchmark instead of generating curve')

	parser.add_argument('--collect', action='store_true', help='collects statistics without running the benchmark')
	parser.add_argument('--prepopulate', action='store_true')
	parser.add_argument('--over_time', action='store_true', help='collects stats over time')
	
	args = parser.parse_args()
	if args.obliterate:
		lib.cleanup_previous_experiment(EXP)
	elif args.benchmark:
		if not args.driver_node or not args.ini_files:
			print("missing --driver_node and/or --ini_files when used with --benchmark option")
			parser.print_help()
			return -1
		elif args.view is False and (not args.csv_path or not args.csv_file):
			print ("when --view is False / not specified, must include --csv_path and --csv_file")
			parser.print_help()
			return -1

		for config_file in args.ini_files:
			exp, skews = exp_lib.create_experiment(FPATH, config_file, args.override)
			for i in range(exp["trials"]):
				exp["out_dir"] = create_trial_outdir(config_file, i)
				generate_skew_curve(exp, skews, args.view, args.collect, args.prepopulate)
				plot(exp, skews, args.driver_node, args.csv_path, args.csv_file,
						args.view, args.collect, args.over_time)
	elif args.stats:
		for config_file in args.ini_files:
			exp, skews = exp_lib.create_experiment(FPATH, config_file, args.override)
			for i in range(exp["trials"]):
				exp["out_dir"] = create_trial_outdir(config_file, i)
				gather_statistics(exp, skews, args.collect) 
	elif args.start:
		lib.cleanup_previous_experiment(EXP)
		lib.init_experiment(EXP)
	else:
		parser.print_help()

if __name__ == "__main__":
    main()
