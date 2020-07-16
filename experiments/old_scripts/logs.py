import collections
import csv
import itertools
import json
import lib
import os
import random
import re


def extract_exp_summary(params):
    result = {}
    result["commit"] = params["cockroach_commit"]
    result["n_workload_nodes"] = len(params["workload_nodes"])
    result["n_warm_nodes"] = len(params["warm_nodes"])
    result["n_hot_nodes"] = len(params["hot_nodes"])

    b = params["benchmark"]

    result["benchmark_name"] = b["name"]

    if "init_args" in b:
        init_args = b["init_args"]
    else:
        init_args = {}

    if "run_args" in b:
        run_args = b["run_args"]
    else:
        run_args = {}

    if "n_clients" in run_args:
        result["n_clients_per_workload_node"] = run_args["n_clients"]

    if "duration" in run_args:
        result["exp_duration"] = run_args["duration"]

    if "splits" in run_args:
        result["n_splits"] = run_args["splits"]
    
    if "read_percent" in run_args:
        result["read_percent"] = run_args["read_percent"]

    if "n_statements_per_txn" in run_args:
        result["n_statements_per_txn"] = run_args["n_statements_per_txn"]

    if "n_keys_per_statement" in run_args: 
        result["n_keys_per_statement"] = run_args["n_keys_per_statement"]

    if "distribution" in run_args:
        d = run_args["distribution"]
        result["key_dist"] = d["type"]

        if d["type"] == "zipf":
            p = d["params"]
            result["key_dist_skew"] = p["skew"]

    if "hot_keys" in init_args:
        result["n_hot_keys"] = len(init_args["hot_keys"])
    else:
        result["n_hot_keys"] = 0

    return result


def parse_kvbench_log(path):
    result = collections.defaultdict(list)

    sample_type = "interval"
    with open(path, "r") as log:
        for line in log:
            # Parse headers
            match = re.match(r"^_+elapsed", line)
            if match:
                headers = line.replace("_", " ").split()
                last_header = headers[len(headers)-1]
                if last_header == "total":
                    sample_type = "total"
                elif last_header == "result":
                    sample_type = "total_aggregate"

            # Parse data lines
            match = re.match(r"^\s+([\d\.]+)s\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]*)\s*(\w*)", line)
            if match:
                result["time_secs"].append(float(match.group(1)))
                result["errors"].append(float(match.group(2)))

                if sample_type == "interval":
                    result["ops/sec"].append(float(match.group(3)))
                    result["p50_ms"].append(float(match.group(5)))
                    result["p95_ms"].append(float(match.group(6)))
                    result["p99_ms"].append(float(match.group(7)))
                    result["pmax_ms"].append(float(match.group(8)))
                    result["op_type"].append(match.group(9))

                elif sample_type == "total" or sample_type == "total_aggregate":
                    result["ops/sec"].append(float(match.group(4)))
                    result["p50_ms"].append(float(match.group(6)))
                    result["p95_ms"].append(float(match.group(7)))
                    result["p99_ms"].append(float(match.group(8)))
                    result["pmax_ms"].append(float(match.group(9)))

                    if match.group(10):
                        result["op_type"].append(match.group(10))
                    else:
                        result["op_type"].append("aggregate")

                result["sample_type"].append(sample_type)

    # Check result for consistency
    for k1,k2 in itertools.combinations(result.keys(), 2):
        assert(len(result[k1]) == len(result[k2]))

    return result


def parse_kvbench_logs(out_dir):
    results = collections.defaultdict(list)

    for root, dirs, files in os.walk(out_dir):
        dirname = os.path.basename(root)

        if any([re.match(r"bench_out_\d+\.txt", file) for file in files]):
            dirname = os.path.basename(os.path.split(root)[0])

            for file in files:
                if re.match(r"bench_out_\d+\.txt", file):
                    fpath = os.path.join(root, file)
                    result = parse_kvbench_log(fpath)

                    assert(len(result.keys()) != 0)
                    k = random.choice(list(result.keys()))
                    l = len(result[k])

                    match = re.match(r"bench_out_(\d+)\.txt", file)
                    client_nums = [match.group(1) for l in range(l)]
                    result["client_num"] += client_nums

                    params = lib.read_params(root)
                    summ = extract_exp_summary(params)
                    # print(summ)

                    for k,v in summ.items():
                        result[k] += [v for l in range(l)]

                    # print(result)
                    for k,v in result.items():
                        results[k] += v

    # Check aggregate results for consistency
    for k1,k2 in itertools.combinations(results.keys(), 2):
        assert(len(results[k1]) == len(results[k2]))

    path = os.path.join(out_dir, "kvbench_results.csv")
    with open(path, "w+") as f:
        writer = csv.writer(f, delimiter=",")

        # Write headers
        keys = sorted(results.keys())
        writer.writerow(keys)

        # Write rows
        k = random.choice(list(results.keys()))
        l = len(results[k])
        for i in range(l):
            writer.writerow(list(map(lambda k: results[k][i], keys)))
