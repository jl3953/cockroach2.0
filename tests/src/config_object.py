import configparser
import itertools


class Node:

  def __init__(self, ip_enum, region=None, store=None):
    """

    :param ip_enum: (int) enumerated node
    :param region: (str) newyork, london, tokyo, etc
    :param store: (sr) /data
    """

    self.ip = "192.168.1." + str(ip_enum)
    self.region = region
    self.store = store





class ConfigObject:

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

  def enumerate_configs(self):
    """

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
      config_dict["workload_nodes"] = self.enumerate_workload_nodes(driver_node_ip_enum, num_workload_nodes)
      config_dict["warm_nodes"] = self.enumerate_warm_nodes(num_warm_nodes, driver_node_ip_enum, num_workload_nodes)

    return combinations

  @staticmethod
  def output_config(config_dict, ini_filename):
    config = configparser.ConfigParser()
    config["DEFAULT"] = config_dict
    with open(ini_filename, "w") as ini:
      config.write(ini)
    return ini_filename

  @staticmethod
  def enumerate_workload_nodes(driver_node_ip_enum, num_workload_nodes):
    """ Populates workload nodes
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
    """

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
