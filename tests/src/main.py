import os

import config_io
import config_object
import constants
import generate_configs
import latency_throughput
import run_single_data_point

config_object_list = [
  (config_object.ConfigObject(), os.path.join(constants.TEST_CONFIG_PATH, "override.ini")),
  ]


def main():

  for cfg_obj, lt_fpath in config_object_list:

    # generate config objects
    cfg_fpath_list = cfg_obj.generate_all_config_files()
    cfgs = generate_configs.generate_configs_from_files_and_add_fields(cfg_fpath_list)

    # generate lt_config objects that match those config objects
    lt_cfg = config_io.read_config_from_file(lt_fpath)

    for cfg in cfgs:
      try:
        logs_dir = generate_configs.generate_dir_name(cfg["config_fpath"])
        os.makedirs()
        optimal_concurrency, _ = latency_throughput.latency_throughput(cfg, lt_cfg, logs_dir)
        cfg["concurrency"] = optimal_concurrency
        run_single_data_point.run(cfg, logs_dir)
      except BaseException as e:
        print("Config {0} failed to run, continue with other configs. e:[{1}]"
              .format(cfg["config_fpath"], e.printStack()))
