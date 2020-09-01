#!/usr/bin/env python3

import os
import subprocess

import lib


def create_dir(location, dir_name):
  """ Creates a directory at location.

	Args:
		location (str): absolute path name, directory location of new dir
		dir_name (str): name of new directory.
	
	Returns:
		Absolute path of new directory.
	"""

  new_dir = os.path.join(location, dir_name)
  lib.call_remote("localhost", "mkdir {0}".format(new_dir), "unable to make new dir")

  return new_dir


def git_commit_hash():
  """ Returns current commit hash on current branch.
	
	Args:
		None.
	
	Returns:
		Commit hash (str)
	"""

  hash_byte = subprocess.check_output("git rev-parse HEAD".split())
  git_commit = hash_byte.decode("utf-8").strip()

  return git_commit


def git_submodule_commit_hash(submodule):
  """ Returns current commit hash of submodule.

	Args:
		submodule (str): name of submodule
	
	Returns:
		commit hash.
	"""

  hash_byte = subprocess.check_output("git rev-parse @:{0}".format(submodule).split())
  commit = hash_byte.decode("utf-8").strip()

  return commit


def move_logs(src_logs, dest_logs):
  """ Moves logs from src to dest.

	Args:
		src_logs (str)
		dest_logs (str)

	Returns:
		None.
	"""

  lib.call_remote("localhost", "mv {0} {1}".format(src_logs, dest_logs),
                  "unable to move logs")


def gnuplot(gnuplot_script, *args):
  """ Calls gnuplot script on input csv and dumps generated graphs
	in output_graph_dir.

	Args:
		gnuplot_script (str): abs path of gnuplot script
		args (str): args of the script

	Returns:
		None.
	"""

  cmd = "gnuplot -c {0}".format(gnuplot_script)
  for arg in args:
    cmd += " " + str(arg)

  lib.call(cmd, "gnuplot script failed bash_imitation")


def disable_core(core_num, hostname):
  """ Disables core with core_num on specified node.

  :param core_num: core number to disable
  :param hostname: specified node
  :returns none
  """

  if core_num >= 16:
    raise AssertionError("Cannot specify core larger than 15")
  elif core_num <= 0:
    raise AssertionError("Cannot specify core 0 or under")

  lib.call_remote(hostname, "echo 0 | tee /sys/devices/system/cpu/cpu{0}/online".format(core_num),
                  "could not disable core {0} on host {1}".format(core_num, hostname))


def enable_core(core_num, hostname):
  """Enables core with core_num on specified node.

  :param core_num: core number to disable
  :param hostname: specified node
  :returns none
  """

  if core_num >= 16:
    raise AssertionError("Cannot specify core larger than 15")
  elif core_num <= 0:
    raise AssertionError("Cannot specify core 0 or under")

  lib.call_remote(hostname, "echo 1 | tee /sys/devices/system/cpu/cpu{0}/online".format(core_num),
                  "could not enable core {0} on host {1}".format(core_num, hostname))


def main():
  try:
    disable_core(0, "node-1")
  except AssertionError as e:
    print("Disable core check worked for 0, err:{0}".format(e))

  try:
    disable_core(16, "node-1")
  except AssertionError as e:
    print("Disable core check worked for 16, err:{0}".format(e))

  disable_core(15, "node-1")
  _ = input("disabled core 15 on node-1, hit enter to continue.")
  enable_core(15, "node-1")
  _ = input("enabled core 15 on node-1, hit enter to continue.")

  try:
    enable_core(0, "node-1")
  except AssertionError as e:
    print("Enable core check worked for 0, err:{0}".format(e))

  try:
    enable_core(16, "node-1")
  except AssertionError as e:
    print("Enable core check worked for 16, err:{0}".format(e))
