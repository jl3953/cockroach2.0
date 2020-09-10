import os
import shlex
import subprocess

import constants
import system_utils

EXE = os.path.join(constants.COCKROACHDB_DIR, "cockroach")


def set_cluster_settings_on_single_node(node):
  cmd = ('echo "'
         # 'set cluster setting kv.range_merge.queue_enabled = false;'
         # 'set cluster setting kv.range_split.by_load_enabled = false;'
         'set cluster setting kv.raft_log.disable_synchronization_unsafe = true;'
         'alter range default configure zone using num_replicas = 1;'
         '" | {0} sql --insecure '
         '--url="postgresql://root@{0}?sslmode=disable"').format(EXE, node["ip"])
  system_utils.call_remote(node["ip"], cmd)


def build_cockroachdb_commit_on_single_node(node, commit_hash):
  cmd = ("ssh {0} 'export GOPATH=/usr/local/temp/go "
         "&& set -x && cd {1} && git fetch origin {2} && git checkout {2} && git pull origin {2} && git submodule "
         "update --init "
         "&& (export PATH=$PATH:/usr/local/go/bin && echo $PATH && make build ||"
         " (make clean && make build)) && set +x'") \
    .format(node["ip"], constants.COCKROACHDB_DIR, commit_hash)

  return subprocess.Popen(shlex.split(cmd))


def build_cockroachdb_commit(nodes, commit_hash):
  processes = [build_cockroachdb_commit_on_single_node(node, commit_hash) for node in nodes]
  for process in processes:
    process.wait()


def start_cockroach_node(node, join=None):
  ip = node["ip"]
  store = node["store"]
  region = node["region"]

  cmd = ("{0} start --insecure "
         "--advertise-addr={1} "
         "--store={2} "
         "--locality=region={3} "
         "--cache=.25 "
         "--max-sql-memory=.25 "
         "--log-file-verbosity=2 "
         "--background"
         ).format(EXE, ip, store, region)

  if join:
    cmd = "{0} --join={1}:26257".format(cmd, join)

  cmd = "ssh -tt {0} '{1}' && stty sane".format(ip, cmd)
  print(cmd)
  return subprocess.Popen(cmd, shell=True)


def start_cluster(nodes):
  first = nodes[0]
  start_cockroach_node(first).wait()

  processes = []
  for node in nodes[1:]:
    processes.append(start_cockroach_node(node, join=first["ip"]))

  for process in processes:
    process.wait()


def set_cluster_settings(nodes):
  for node in nodes:
    set_cluster_settings_on_single_node(node)


def setup_hotnode(node):
  print("JENN DID YOU SET UP THE HOT NODE ON {} YET???".format(node))


def kill_hotnode(node):
  print("JENN GO KILL THE HOT NODE ON {}!!!".format(node))


def disable_cores(nodes, cores):
  modify_cores(nodes, cores, is_enable_cores=False)


def enable_cores(nodes, cores):
  modify_cores(nodes, cores, is_enable_cores=True)


def modify_cores(nodes, cores, is_enable_cores=False):
  processes = []
  for node in nodes:
    for i in range(1, cores + 1):
      processes.append(system_utils.modify_core(node["ip"], i, is_enable_cores))

  for p in processes:
    p.wait()


def kill_cockroachdb_node(node):
  ip = node["ip"]

  if "store" in node:
    store = node["store"]
  else:
    store = None

  cmd = ("PID=$(! pgrep cockroach) "
         "|| (sudo pkill -9 cockroach; while ps -p $PID;do sleep 1;done;)")

  if store:
    cmd = "({0}) && {1}".format(
      cmd, "sudo rm -rf {0}".format(os.path.join(store, "*")))

  cmd = "ssh {0} '{1}'".format(ip, cmd)
  print(cmd)
  return subprocess.Popen(shlex.split(cmd))


def cleanup_previous_experiments(server_nodes, client_nodes, hot_node):
  # kill all client nodes
  client_processes = [kill_cockroachdb_node(node) for node in client_nodes]
  for cp in client_processes:
    cp.wait()

  # kill at server nodes
  server_processes = [kill_cockroachdb_node(node) for node in server_nodes]
  for sp in server_processes:
    sp.wait()

  # kill the hot node
  if hot_node:
    kill_hotnode(hot_node)
    enable_cores([hot_node], 15)

  # re-enable ALL cores again, regardless of whether they were previously disabled
  enable_cores(server_nodes, 15)


def run_kv_workload(client_nodes, server_nodes, concurrency, keyspace, warm_up_duration, duration, read_percent,
                    n_keys_per_statement, skew, log_dir):
  server_urls = ["postgresql://root@{0}:26257?sslmode=disable".format(n["ip"])
                 for n in server_nodes]
  args = [" --concurrency {}".format(concurrency), " --read-percent={}".format(read_percent),
          " --batch={}".format(n_keys_per_statement), " --zipfian --s={}".format(skew),
          " --keyspace={}".format(keyspace)]
  cmd = "{0} workload run kv {1} {2}".format(EXE, " ".join(server_urls), " ".join(args))

  # run warmup
  warmup_cmd = cmd + " --duration={}s".format(warm_up_duration)
  warmup_processes = []
  for node in client_nodes:
    cmd = "sudo ssh {0} '{1}'".format(node["ip"], warmup_cmd)
    print(cmd)
    warmup_processes.append(subprocess.Popen(shlex.split(cmd)))

  for wp in warmup_processes:
    wp.wait()

  # run trial
  trial_cmd = cmd + " --duration={}s".format(duration)
  trial_processes = []
  for node in client_nodes:
    cmd = "sudo ssh {0} '{1}'".format(node["ip"], trial_cmd)
    print(cmd)
    # logging output for each node
    log_fpath = os.path.join(log_dir, "bench_{}.txt".format(node["ip"]))
    with open(log_fpath, "w") as f:
      trial_processes.append(subprocess.Popen(shlex.split(cmd), stdout=f))

  for tp in trial_processes:
    tp.wait()


def run(config, log_dir):
  server_nodes = config["warm_nodes"]
  client_nodes = config["workload_nodes"]
  commit_hash = config["cockroach_commit"]
  hot_node = config["hot_node"] if "hot_node" in config else None
  # hotkeys = config["hotkeys"]

  # clear any remaining experiments
  cleanup_previous_experiments(server_nodes, client_nodes, hot_node)

  # disable cores, if need be
  cores_to_disable = config["disable_cores"]
  if cores_to_disable > 0:
    disable_cores(server_nodes, cores_to_disable)
    if hot_node:
      disable_cores([hot_node], cores_to_disable)

  # start hot node
  if hot_node:
    setup_hotnode(hot_node)

  # build and start crdb cluster
  build_cockroachdb_commit(server_nodes, commit_hash)
  start_cluster(server_nodes)
  set_cluster_settings(server_nodes)

  # build and start client nodes
  build_cockroachdb_commit(client_nodes, commit_hash)
  os.makedirs(log_dir)

  if config["name"] == "kv":
    keyspace = config["keyspace"]
    warm_up_duration = config["warm_up_duration"]
    duration = config["duration"]
    read_percent = config["read_percent"]
    n_keys_per_statement = config["n_keys_per_statement"]
    skew = config["skews"]
    concurrency = config["concurrency"]
    run_kv_workload(client_nodes, server_nodes, concurrency, keyspace, warm_up_duration, duration,
                    read_percent, n_keys_per_statement, skew, log_dir)

  # re-enable cores
  cores_to_enable = cores_to_disable
  if cores_to_enable > 0:
    enable_cores(server_nodes, cores_to_enable)
    if hot_node:
      enable_cores([hot_node], cores_to_enable)


def main():
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("ini_file")
  args = parser.parse_args()


  import config_io
  config = config_io.read_config_from_file(args.ini_file)
  config["concurrency"] = 16
  log_dir = os.path.join(constants.COCKROACHDB_DIR, "tests", "help")

  run(config, log_dir)


if __name__ == "__main__":
  main()
