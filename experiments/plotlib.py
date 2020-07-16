import collections
import csv
import os
import lib
import re
import over_time

DRIVER_NODE = "192.168.1.19"

def extract_data(last_eight_lines):

	def parse(header_line, data_line, suffix=""):
		if "elapsed" not in header_line:
			return {}

		fields = data_line.strip().split()
		if "read" in fields[-1]:
			suffix = "-r"
		elif "write" in fields[-1]:
			suffix = "-w"
		else:
			suffix = ""

		header = [w + suffix for w in re.split('_+', header_line.strip().strip('_'))]
		data = dict(zip(header, fields))
		return data

	read_data = {}
	try:
		read_data = parse(last_eight_lines[0], last_eight_lines[1], "-r")
	except BaseException:
		print("write only")

	write_data = {}
	try:
		write_data = parse(last_eight_lines[3], last_eight_lines[4], "-w")
		read_data.update(write_data)
	except BaseException:
		print ("read only")

	data = parse(last_eight_lines[6], last_eight_lines[7])

	read_data.update(data)

	return read_data


	 
def write_out_data_wrapper(data, out_dir, outfile_name="gnuplot.csv"):

	filename = os.path.join(out_dir, outfile_name)
	return write_out_data(data, filename)


def write_out_data(data, outfile):

	if len(data) <= 0:
		return ""

	with open(outfile, "w") as csvfile:
		writer = csv.DictWriter(csvfile, delimiter='\t', fieldnames=data[0].keys())
		writer.writeheader()

		for datum in data:
			try:
				writer.writerow(datum)
			except BaseException:
				print("failed on {0}".format(datum))
				continue

	return outfile


def aggregate(acc):

	""" Aggregates data across workload nodes.

	Args:
	acc (list[dict])

	Returns:
	one final data point (dict).
	"""

	final_datum = collections.defaultdict(float)
	for datum in acc:
		for k, v in datum.items():
			try:
				final_datum[k] += float(v)
			except BaseException:
				print("could not add to csv file key:[{0}], value:[{1}]".format(k, v))
				continue
			
	for k in final_datum:
		if "ops" not in k:
			final_datum[k] /= len(acc)

	return final_datum


def is_output_okay(tail):

	try:
		if not ("elapsed" in tail[3] and "elapsed" in tail[6]):
			return False

		return True
	except BaseException:
		return False


def accumulate_workloads_per_skew(config, dir_path):
	""" Aggregating data for a single skew point across all workload nodes.

		Returns:
		extracted datum, success or not
	"""

	acc = []
	for j in range(len(config["workload_nodes"])):
		path = os.path.join(dir_path, "bench_out_{0}.txt".format(j))

		with open(path, "r") as f:
			# read the last eight lines of f
			print(path)
			tail = f.readlines()[-8:]
			if not is_output_okay(tail):
				print ("{0} missing some data lines".format(path))
				return None, False

			try: 
				datum = extract_data(tail)
				acc.append(datum)
			except BaseException:
				print("failed to extract data: {0}".format(path))
				return None, False

	final_datum = aggregate(acc)
	return final_datum, True


def extract_shard_data(lines):

	def to_int(key):
		if key == "NULL":
			return 0
		else:
			all_nums = key.split("/")
			last = int(all_nums[-1])
			if last == 0:
				return int(all_nums[-2])
			else:
				return last

	point = lines[0]
	print(point)
	point["start_key"] = to_int(point["start_key"])
	point["end_key"] = to_int(point["end_key"])
	point["range_id"] = int(point["range_id"])
	point["range_size_mb"] = float(point["range_size_mb"])

	return point


def accumulate_shard_per_skew(config, dir_path):

	acc = []
	path = os.path.join(dir_path, "shards.csv")
	with open(path, "r") as f:
		reader = csv.DictReader(f, delimiter='\t')
		for row in reader:
			acc.append(row)

	datum = extract_shard_data(acc)
	return datum, True


def accumulate_greps_per_skew(config, dir_path):
	bumps = 0
	path = os.path.join(dir_path, "bumps.csv")
	with open(path, "r") as f:
		for line in f:
			bumps += int(line.strip())

	return {"bumps": bumps}, True


def gather_over_time(config):

	def write_out_stats(stats, out):

		with open(out, "w") as f:
			writer = csv.DictWriter(f, delimiter='\t', fieldnames=stats[0].keys())

			writer.writeheader()
			for stat in stats:
				writer.writerow(stat)

		return out

	out_dir = os.path.join(config["out_dir"])
	print("jenndebug", out_dir)
	dir_path = os.path.join(out_dir, "skew-0")

	for i in range(len(config["workload_nodes"])):
		path = os.path.join(dir_path, "bench_out_{0}.txt".format(i))
		stats = over_time.parse_file(path)
		sorted(stats, key=lambda stat: stat["elapsed-r"])
		filename = write_out_stats(stats, os.path.join(out_dir, "stats_over_time_{0}.csv".format(i)))
		print(filename)

		csv_file = os.path.basename(os.path.dirname(out_dir)) + "_stats_{0}.csv".format(i)
		print(csv_file)
		cmd = "mv {0} /usr/local/temp/go/src/github.com/cockroachdb/cockroach/gnuplot/{1}".format(filename, csv_file)
		lib.call_remote(DRIVER_NODE, cmd, "gather_time_err") 


def generate_csv_file(config, skews, accumulate_fn, suffix, driver_node=DRIVER_NODE,
		csv_path="/usr/local/temp/go/src/github.com/cockroachdb/cockroach/gnuplot",
		csv_file=None):

	""" Generates csv file from skews.
	
	Args:
		config: experimental config
		skews: take a guess buddy
		
	Returns:
		None.
	"""

	out_dir = os.path.join(config["out_dir"])
	data = []
	for i in range(len(skews)):

		dir_path = os.path.join(out_dir, "skew-{0}".format(i))
		datum, succeeded = accumulate_fn(config, dir_path)
		if succeeded:
			datum_with_skew = {"skew": skews[i]}
			datum_with_skew.update(datum)
			data.append(datum_with_skew)
		else:
			print("failed on skew[{0}]".format(skews[i]))
			continue

	filename = write_out_data_wrapper(data, out_dir, suffix+".csv")
	print(filename)

	if csv_file is None:
		csv_file = os.path.basename(os.path.dirname(out_dir)) + "_" + suffix + ".csv"
	print(csv_file)
	cmd = "cp {0} {1}/{2}".format(filename, csv_path, csv_file)
	lib.call_remote(driver_node, cmd, "i like to move it move it")


def plot_bumps(config, skews):

	generate_csv_file(config, skews, accumulate_greps_per_skew, "bumps")


def plot_shards(config, skews):

	generate_csv_file(config, skews, accumulate_shard_per_skew, "shard")


def gnuplot(config, skews, driver_node, 
		csv_path="/usr/local/temp/go/src/github.com/cockroachdb/cockroach/gnuplot",
		csv_file=None):

	generate_csv_file(config, skews, accumulate_workloads_per_skew, "skew",
			driver_node=driver_node, csv_path=csv_path, csv_file=csv_file)

