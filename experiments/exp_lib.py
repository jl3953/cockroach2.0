#!/usr/bin/env python3 
import configparser
import os
import json

OVERRIDE_INI = "override.ini" 


def find_log_dir(fpath, config_file): 
	
	config = configparser.ConfigParser() 
	config.read(config_file) 
	base_dir = os.path.join(fpath, "..")
	log_dir = os.path.join(base_dir, config["DEFAULT"]["LOGS_DIR"])
	return log_dir


def read_variation(variation_file):
	config = configparser.ConfigParser()
	config.read(variation_file)

	exp = {
		"variation": {
			"concurrency": json.loads(config["variation"]["concurrency"]),
			"step_size": int(config["variation"]["step_size"]),
			"skew": float(config["variation"]["skew"]),
		}
	}

	return exp


def override_params(exp, skews, config, fpath, override_file=None):

	override = configparser.ConfigParser()
	override.read(override_file)

	if "DEFAULT" in override:
		if "LOGS_DIR" in override["DEFAULT"] and "OUT_DIR" in override["DEFAULT"]:
			exp["out_dir"] = create_out_dir(fpath, override["DEFAULT"]["LOGS_DIR"], override["DEFAULT"]["OUT_DIR"])
		elif "LOGS_DIR" in override["DEFAULT"]:
			exp["out_dir"] = create_out_dir(fpath, override["DEFAULT"]["LOGS_DIR"], config["DEFAULT"]["OUT_DIR"])
		elif "OUT_DIR" in override["DEFAULT"]:
			exp["out_dir"] = create_out_dir(fpath, config["DEFAULT"]["LOGS_DIR"], override["DEFAULT"]["OUT_DIR"])

	if "cluster" in override:
		override_cluster = override["cluster"]
		if "cockroach_commit" in override_cluster:
			exp["cockroach_commit"] = override_cluster["cockroach_commit"]
		if "workload_nodes" in override_cluster:
			exp["workload_nodes"] = json.loads(override_cluster["workload_nodes"])
		if "hot_nodes" in override_cluster:
			exp["hot_nodes"] = json.loads(override_cluster["hot_nodes"])
		if "warm_nodes" in override_cluster:
			exp["warm_nodes"] = json.loads(override_cluster["warm_nodes"])

	if "benchmark" in override:
		override_benchmark = override["benchmark"]
		exp_benchmark = exp["benchmark"]
		if "name" in override_benchmark:
			exp_benchmark["name"] = override_benchmark["name"]
		if "init_args" in override_benchmark:
			exp_benchmark["init_args"] = json.loads(override_benchmark["init_args"])

		run_args = exp_benchmark["run_args"]
		if "concurrency" in override_benchmark:
			run_args["concurrency"] = json.loads(override_benchmark["concurrency"])
		if "warmup_duration" in override_benchmark:
			run_args["warmup_duration"] = int(override_benchmark["warmup_duration"])
		if "duration" in override_benchmark:
			run_args["duration"] = int(override_benchmark["duration"])
		if "read_percent" in override_benchmark:
			run_args["read_percent"] = int(override_benchmark["read_percent"])
		if "n_keys_per_statement" in override_benchmark:
			run_args["n_keys_per_statement"] = int(override_benchmark["n_keys_per_statement"])
		if "use_original_zipfian" in override_benchmark:
			run_args["use_original_zipfian"] = bool(override_benchmark["use_original_zipfian"])
		if "distribution_type" in override_benchmark:
			run_args["distribution"]["type"] = override_benchmark["distribution_type"]
		exp_benchmark["run_args"] = run_args

		if "skews" in override_benchmark:
			skews = json.loads(override_benchmark["skews"])

		exp["benchmark"] = exp_benchmark

	return exp, skews

def create_out_dir(fpath, logs_dirname, out_dirname):
	base_dir = os.path.join(fpath, "..")
	logs_dir = os.path.join(base_dir, logs_dirname)
	out_dir = os.path.join(logs_dir, out_dirname)

	return out_dir


def create_experiment(fpath, config_filename, override=None):

	config = configparser.ConfigParser()
	config.read(config_filename)
	print("jenndebug", config_filename)

	exp = {
		"out_dir": create_out_dir(fpath, config["DEFAULT"]["LOGS_DIR"], config["DEFAULT"]["OUT_DIR"]),
		"trials": 1,
		"cockroach_commit": config["cluster"]["cockroach_commit"],
		"workload_nodes": json.loads(config["cluster"]["workload_nodes"]),
		"hot_nodes": json.loads(config["cluster"]["hot_nodes"]),
		"warm_nodes": json.loads(config["cluster"]["warm_nodes"]),
		"benchmark": {
			"name": config["benchmark"]["name"],
			"init_args": {},
			"run_args": {
				"concurrency": json.loads(config["benchmark"]["concurrency"]),
				"warmup_duration": int(config["benchmark"]["warmup_duration"]),
				"duration": int(config["benchmark"]["duration"]),
				"read_percent": int(config["benchmark"]["read_percent"]),
				"n_keys_per_statement": int(config["benchmark"]["n_keys_per_statement"]),
				"distribution": {
					"type": config["benchmark"]["distribution_type"],
					"params": {}
				}
			}
		}
	}

	if "use_original_zipfian" in config["benchmark"]:
		try:
			exp["benchmark"]["run_args"]["use_original_zipfian"] = json.loads(config["benchmark"]["use_original_zipfian"])
		except BaseException:
			exp["benchmark"]["run_args"]["use_original_zipfian"] = (config["benchmark"]["use_original_zipfian"] == "True")

	if "trials" in config["DEFAULT"]:
		exp["trials"] = int(config["DEFAULT"]["trials"])

	if "use_hot_nodes_as_gateways" in config["cluster"]:
		exp["use_hot_nodes_as_gateways"] = json.loads(config["cluster"]["use_hot_nodes_as_gateways"])
	else:
		exp["use_hot_nodes_as_gateways"] = False

	if "hot_key" in config["cluster"]:
		exp["hot_key"] = int(config["cluster"]["hot_key"])
	else:
		exp["hot_key"] = 1

	if "should_create_partition" in config["cluster"]:
		exp["should_create_partition"] = json.loads(config["cluster"]["should_create_partition"])
	else:
		exp["should_create_partition"] = False

	if "keyspace" in config["benchmark"]:
		exp["benchmark"]["run_args"]["keyspace"] = json.loads(config["benchmark"]["keyspace"])
	else:
		exp["benchmark"]["run_args"]["keyspace"] = 1000000

	skews = json.loads(config["benchmark"]["skews"])
	
	if override:
		exp, skews = override_params(exp, skews, config, fpath, override)
	
	return exp, skews


if __name__ == "__main__":
	exp, skews = create_experiment(os.path.dirname(os.path.realpath(__file__)), "new_zipfian_match.ini", override=False)
	print(exp)
	print(skews)

	print(read_variation("lt.ini"))
