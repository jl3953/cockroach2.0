import datetime
import itertools
import os

import config_io
import constants
import node

TEST_PATH = os.path.join(constants.COCKROACHDB_DIR, "tests")
TEST_CONFIG_PATH = os.path.join(TEST_PATH, "config")


class ConfigObject:
  """Represents different combinations of configuration parameters."""

  def __init__(self):

    # default
    self.logs_dir = ["test"]
    self.store_dir = ["kv-skew"]
    self.trials = [1]

    # cluster
    self.cockroach_commit = ["master"]
    self.num_warm_nodes = [4]
    self.num_workload_nodes = [6]
    self.driver_node_ip_enum = [1]

    # self.workload_nodes = [] # to be populated
    # self.warm_nodes = [] # to be populated
    # self.hot_node = []
    self.hot_key_threshold = [-1]
    self.should_create_partition = [False]
    self.disable_cores = [2, 4, 6]

    # benchmark
    self.name = ["kv"]
    self.keyspace = [1000000]
    # self.concurrency = [] # to be populated
    self.warm_up_duration = [10]  # in seconds
    self.duration = [2]  # in seconds
    self.read_percent = [100]  # percentage
    self.n_keys_per_statement = [6]
    self.use_original_zipfian = [False]
    self.distribution_type = ["zipf"]
    self.skews = [0, 0.9]

  def generate_config_combinations(self):
    """Generates the trial configuration parameters for a single run, lists all in a list of dicts.

    :return: a list of dictionaries of combinations
    """
    temp_dict = vars(self)

    all_field_values = list(temp_dict.values())
    values_combinations = list(itertools.product(*all_field_values))

    combinations = []
    for combo in values_combinations:
      config_dict = dict(zip(temp_dict.keys(), combo))
      combinations.append(config_dict)

    for config_dict in combinations:
      driver_node_ip_enum = config_dict["driver_node_ip_enum"]
      num_workload_nodes = config_dict["num_workload_nodes"]
      num_warm_nodes = config_dict["num_warm_nodes"]

      workload_nodes = ConfigObject.enumerate_workload_nodes(driver_node_ip_enum, num_workload_nodes)
      config_dict["workload_nodes"] = [vars(n) for n in workload_nodes]

      warm_nodes = ConfigObject.enumerate_warm_nodes(num_warm_nodes, driver_node_ip_enum, num_workload_nodes)
      config_dict["warm_nodes"] = [vars(n) for n in warm_nodes]

    return combinations

  def generate_all_config_files(self):
    """Generates all configuration files with different combinations of parameters.
    :return: None
    """
    config_combos = self.generate_config_combinations()
    for config_dict in config_combos:
      ini_filename = ConfigObject.generate_ini_filename(suffix=config_dict["logs_dir"])
      _ = config_io.write_config_to_file(config_dict, ini_filename)

  @staticmethod
  def generate_ini_filename(suffix=None, custom_unique_prefix=None):
    """Generates a filename for ini using datetime as unique id.

    :param suffix: (str) suffix for human readability
    :param custom_unique_prefix: use a custom prefix. If none, use datetime.
    :return: (str) full filepath for config file
    """

    unique_prefix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    if custom_unique_prefix:
      unique_prefix = custom_unique_prefix
    ini = unique_prefix + "_" + suffix + ".ini"
    return os.path.join(TEST_CONFIG_PATH, ini)

  @staticmethod
  def enumerate_workload_nodes(driver_node_ip_enum, num_workload_nodes):
    """ Populates workload nodes.
    :rtype: List(Node)
    :param driver_node_ip_enum: (int) enum that driver node starts at
    :param num_workload_nodes: (int) number of workload nodes wanted
    :return: list of Node objects
    """
    start_ip = driver_node_ip_enum
    result = []
    for i in range(num_workload_nodes):
      ip_enum = i + start_ip
      n = node.Node(ip_enum)
      result.append(n)

    return result

  @staticmethod
  def enumerate_warm_nodes(num_warm_nodes, driver_node_ip_enum, num_already_enumerated_nodes):
    """ Populates warm nodes.

    :param num_warm_nodes: (int)
    :param driver_node_ip_enum: (int)
    :param num_already_enumerated_nodes: (int)
    :return: list of Node objects, the first couple of which have regions
    """

    start_ip_enum = driver_node_ip_enum + num_already_enumerated_nodes

    # regioned nodes
    regioned_nodes = [node.Node(start_ip_enum, "newyork", "/data")]
    if num_warm_nodes >= 2:
      regioned_nodes.append(node.Node(start_ip_enum + 1, "london", "/data"))
    if num_warm_nodes >= 3:
      regioned_nodes.append(node.Node(start_ip_enum + 2, "tokyo", "/data"))

    # nodes that don't have regions
    remaining_nodes_start_ip = start_ip_enum + 3
    remaining_num_warm_nodes = num_warm_nodes - 3
    remaining_nodes = []
    for i in range(remaining_num_warm_nodes):
      ip_enum = i + remaining_nodes_start_ip
      n = node.Node(ip_enum, "singapore", "/data")
      remaining_nodes.append(n)

    return regioned_nodes + remaining_nodes


def main():
  config_object = ConfigObject()
  config_object.generate_all_config_files()


if __name__ == "__main__":
  main()
