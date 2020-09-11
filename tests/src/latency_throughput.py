import datetime
import operator
import os

import config_io
import csv_utils
import gather
import run_single_data_point


def last_adjustments(max_throughput_concurrency):
  return max_throughput_concurrency - 1


def insert_csv_data(data, csv_fpath):
  if len(data) <= 0:
    return None

  existing_rows = csv_utils.read_in_data(csv_fpath)
  all_data = existing_rows + data
  all_data = sorted(all_data, key=lambda i: i["concurrency"])

  _ = csv_utils.write_out_data(all_data, csv_fpath)

  return csv_fpath


def latency_throughput(config, lt_config, log_dir):
  # read lt config file
  start, end = lt_config["concurrency"]
  step_size = lt_config["step_size"]

  # create latency throughput dir, if not running recovery
  lt_dir = os.path.join(log_dir, "latency_throughput")
  lt_logs_dir = os.path.join(lt_dir, "logs")
  if not os.path.exists(lt_logs_dir):
    # not running recovery
    os.makedirs(lt_logs_dir)

  # honing in on increasingly smaller ranges
  max_throughput_concurrency = -1  # placeholder
  data = []
  while step_size > 0:
    for concurrency in range(start, end, step_size):
      # run trial for this concurrency
      config["concurrency"] = concurrency

      # make directory for this specific concurrency, unique by timestamp
      specific_logs_dir = os.path.join(lt_logs_dir, "{0}_{1}".format(
        str(concurrency), datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")))

      # run trial
      os.makedirs(specific_logs_dir)
      bench_logs = run_single_data_point.run(config, specific_logs_dir)

      # gather data from this run
      datum = {"concurrency": concurrency}
      more_data, has_data = gather.gather_data_from_raw_kv_logs(bench_logs)
      if has_data:
        datum.update(more_data)
      data.append(datum)

    # find max throughput and hone in on it
    max_throughput_concurrency = max(data, key=operator.itemgetter("ops/sec(cum)"))["concurrency"]
    concurrency = last_adjustments(max_throughput_concurrency)
    start = concurrency - step_size
    end = concurrency + step_size
    step_size = int(step_size / 2)

    # checkpoint, and also write out csv values every round of honing in
    checkpoint = os.path.join(lt_dir, "checkpoint.csv")
    insert_csv_data(data, checkpoint)

  max_throughput_concurrency = last_adjustments(max_throughput_concurrency)
  return max_throughput_concurrency, data


def main():
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("ini_file")
  parser.add_argument("lt_ini_file")
  args = parser.parse_args()

  config = config_io.read_config_from_file(args.ini_file)
  lt_config = config_io.read_config_from_file(args.lt_ini_file)

  unique_suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
  import constants
  log_dir = os.path.join(constants.COCKROACHDB_DIR, "tests", "help_{}".format(unique_suffix))
  latency_throughput(config, lt_config, log_dir)


if __name__ == "__main__":
  main()
