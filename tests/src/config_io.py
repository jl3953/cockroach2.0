import configparser


def write_config_to_file(config_dict, ini_fpath):
  """ Writes a configuration to an ini file.

  :param config_dict: (Dict) config to write
  :param ini_fpath: (str) fpath to ini file
  :return: (str) ini_file written to
  """
  config = configparser.ConfigParser()
  config["DEFAULT"] = config_dict
  with open(ini_fpath, "w") as ini:
    config.write(ini)
  return ini_fpath


def read_config_from_file(ini_fpath):
  """
  Reads a config file

  :param ini_fpath:
  :return: a dictionary of config parameters
  """
  config = configparser.ConfigParser()
  config.read(ini_fpath)
  return config["DEFAULT"]
