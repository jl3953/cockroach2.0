import datetime
import os
import sqlite3

import config_io
import config_object
import constants
import generate_configs
import latency_throughput
import run_single_data_point
import system_utils

######## configuring the main file ###########

# configuration objec generators matched to the latency throughput files
CONFIG_OBJ_LIST = [
  (config_object.ConfigObject(), os.path.join(constants.TEST_CONFIG_PATH, "override.ini")),
]

# location of the entire database run
unique_suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
DB_DIR = os.path.join(constants.SCRATCH_DIR, "db_{0}".format(unique_suffix))

######## end of configs #############


def generate_dir_name(config_fpath):
  config_file = os.path.basename(config_fpath)
  config_name = config_file.split('.')[0]

  return config_name


def main():

  # create the database and table
  # conn = sqlite3.connect(os.path.join(DB_DIR, "trials.db"))
  # c = conn.cursor()
  # c.execute("CREATE TABLE")

  for cfg_obj, lt_fpath in CONFIG_OBJ_LIST:

    # generate config objects
    cfg_fpath_list = cfg_obj.generate_all_config_files()
    cfgs = generate_configs.generate_config_files_and_add_fields(cfg_fpath_list)

    # generate lt_config objects that match those config objects
    lt_cfg = config_io.read_config_from_file(lt_fpath)

    for cfg in cfgs:
      try:
        # make directory in which trial will be run
        logs_dir = generate_dir_name(cfg["config_fpath"])
        os.makedirs(logs_dir)

        # copy over config into directory
        system_utils.call("cp {0} {1}".format(cfg["config_fpath"], logs_dir))

        # generate latency throughput trials
        lt_fpath_csv = latency_throughput.run(cfg, lt_cfg, logs_dir)

        # run trial
        cfg["concurrency"] = latency_throughput.find_optimal_concurrency(lt_fpath_csv)
        results_fpath_csv = run_single_data_point.run(cfg, logs_dir)

        # TODO insert into sqlite database

      except BaseException as e:
        print("Config {0} failed to run, continue with other configs. e:[{1}]"
              .format(cfg["config_fpath"], e))


if __name__ == "__main__":
  main()
