#!/usr/bin/env python3

import re

def parse_lines(header_original, header, line_r, line_w):
	
	def parse(line):
		stats = line.split()
		stats[0] = stats[0].strip('s') # get rid of "s" after time
		stats = stats[:-1] # get rid of "read" or "write"
		stats = [float(s) for s in stats]

		return stats

	read_stats = parse(line_r)
	write_stats = parse(line_w)

	result = dict(zip(header, read_stats + write_stats))
	return result


def parse_file(filename):

	lines = []
	with open(filename, "r") as f:
		lines = f.readlines()
	
	header_original = re.split('_+', lines[0].strip().strip('_'))
	header_r = [field + "-r" for field in header_original]
	header_w = [field + "-w" for field in header_original]
	header = header_r + header_w

	lines = lines[:-11] # get rid of end stats

	data = []
	i = 0
	while i < len(lines):
		line = lines[i]

		# get rid of header printing
		if "elapsed" in line:
			i += 1
			continue

		line_r = lines[i]
		line_w =  lines[i+1]
		i += 2

		datum = parse_lines(header_original, header, line_r, line_w)
		data.append(datum)

	return data


def main():

	filename = "../all_gateway/kv-skew/skew-0/bench_out_0.txt"
	print(parse_file(filename))


if __name__ == "__main__":
	main()
