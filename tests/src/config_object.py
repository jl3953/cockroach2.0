import configparser
import datetime
import itertools
import os

COCKROACHDB_DIR = "/usr/local/temp/go/src/github.com/cockroachdb/cockroach"
TEST_PATH = os.path.join(COCKROACHDB_DIR, "tests")
TEST_CONFIG_PATH = os.path.join(TEST_PATH, "config")


class Node:

  """Represents information about a node."""

  def __init__(self, ip_enum, region=None, store=None):
    """

    :param ip_enum: (int) enumerated node
    :param region: (str) newyork, london, tokyo, etc
    :param store: (str) usually just /data
    """

    self.ip = "192.168.1." + str(ip_enum)
    if region:
      self.region = region
    if store:
      self.store = store

  def __str__(self):
    return str(vars(self))


class ConfigObject:
  """Represents different combinations of configuration parameters."""

  def __init__(self):

    # default
    self.logs_dir = ["test"]
    self.store_dir = ["kv-skew"]
    self.trials = [1]

    # cluster
    self.cockroach_commit = ["master"]
    self.__num_warm_nodes = [4]
    self.__num_workload_nodes = [6]
    self.__driver_node_ip_enum = [1]

    # self.workload_nodes = [] # to be populated
    # self.warm_nodes = [] # to be populated
    self.hot_key_threshold = [-1]
    self.should_create_partition = [False]
    self.disable_cores = [2, 4, 6]

    # benchmark
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

    all_field_values = temp_dict.values()
    values_combinations = list(itertools.product(*all_field_values))

    combinations = []
    for combo in values_combinations:
      config_dict = dict(zip(temp_dict.keys(), combo))
      combinations.append(config_dict)

    for config_dict in combinations:
      driver_node_ip_enum = config_dict["__driver_node_ip_enum"]
      num_workload_nodes = config_dict["__num_workload_nodes"]
      num_warm_nodes = config_dict["__num_warm_nodes"]
      config_dict["workload_nodes"] = ConfigObject.enumerate_workload_nodes(driver_node_ip_enum, num_workload_nodes)
      config_dict["warm_nodes"] = ConfigObject.enumerate_warm_nodes(num_warm_nodes, driver_node_ip_enum,
                                                                    num_workload_nodes)

    return combinations

  def generate_all_config_files(self):
    """Generates all configuration files with different combinations of parameters.
    :return: None
    """
    config_combos = self.generate_config_combinations()
    for config_dict in config_combos:
      ini_filename = ConfigObject.generate_ini_filename(suffix=config_dict["logs_dir"])
      _ = ConfigObject.write_config_to_file(config_dict, ini_filename)

  @staticmethod
  def generate_ini_filename(suffix=None):
    """ Generates a filename for ini using datetime as unique id

    :param suffix: (str) suffix for human readability
    :return: (str) full filepath for config file
    """

    unique_prefix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(TEST_CONFIG_PATH, unique_prefix + suffix)

  @staticmethod
  def write_config_to_file(config_dict, ini_filename):
    """ Writes a configuration to an ini file.

    :param config_dict: (Dict) config to write
    :param ini_filename: (str) fpath to ini file
    :return: (str) ini_file written to
    """
    config = configparser.ConfigParser()
    config["DEFAULT"] = config_dict
    with open(ini_filename, "w") as ini:
      config.write(ini)
    return ini_filename

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
      node = Node(ip_enum)
      result.append(node)

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
    regioned_nodes = [Node(start_ip_enum, "newyork", "/data")]
    if num_warm_nodes >= 2:
      regioned_nodes.append(Node(start_ip_enum + 1, "london", "/data"))
    if num_warm_nodes >= 3:
      regioned_nodes.append(Node(start_ip_enum + 2, "tokyo", "/data"))

    # nodes that don't have regions
    remaining_nodes_start_ip = start_ip_enum + 3
    remaining_num_warm_nodes = num_warm_nodes - 3
    remaining_nodes = []
    for i in range(remaining_num_warm_nodes):
      ip_enum = i + remaining_nodes_start_ip
      node = Node(ip_enum, "singapore", "/data")
      remaining_nodes.append(node)

    return regioned_nodes + remaining_nodes
