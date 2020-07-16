import copy
import csv
import json
import os
import shlex
import subprocess
import sys

# Constants
COCKROACH_DIR = "/usr/local/temp/go/src/github.com/cockroachdb/cockroach"
EXE = os.path.join(COCKROACH_DIR, "cockroach")
STORE_DIR = "/data"

FPATH = os.path.dirname(os.path.realpath(__file__))
BASE_DIR = os.path.join(FPATH, '..')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')


def call(cmd, err_msg):
    print(cmd)
    p = subprocess.run(cmd, universal_newlines=True, shell=True)
    if p.returncode:
        print(p.stderr)
        print(err_msg)
        sys.exit(1)
    else:
        return p.stdout


def call_remote(host, cmd, err_msg):
    cmd = "sudo ssh {0} '{1}'".format(host, cmd)
    return call(cmd, err_msg)


def call_remote_redirect_stdout(host, cmd, err_msg, path):
	cmd = "sudo ssh {0} '{1}'".format(host, cmd)
	print(cmd)
	print(path)
	with open(path, "w") as f:
		return subprocess.Popen(shlex.split(cmd), stdout=f)


def init_store(node):
    ip = node["ip"]

    cmd = "if [[ ! -e {0} ]]; then mkdir {0}; fi".format(STORE_DIR)
    call_remote(ip, cmd, "Failed to initialize store")

    cmd = ("if [[ $(! mount -l | grep {0}) != *{0}* ]]; "
           "then mount -t tmpfs -o size=32g tmpfs {0}; fi").format(STORE_DIR)
    call_remote(ip, cmd, "Failed to initialize store")


def kill_cockroach_node(node):
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


def query_for_shards(ip, config):

	cmd = '/usr/local/temp/go/src/github.com/cockroachdb/cockroach/cockroach sql --insecure --execute "show experimental_ranges from table kv.kv"'
	# cmd = "sudo ssh {0} '{1}'".format(ip, cmd)

	out_dir = config["out_dir"]
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
		
	save_params(config, out_dir)

	outfile = os.path.join(out_dir, "shards.csv")

	p = call_remote_redirect_stdout(ip, cmd, "query_shard_err", outfile)
	p.wait()


def set_cluster_settings(node):
    ip = node["ip"]
    cmd = ('echo "'
           # 'set cluster setting kv.range_merge.queue_enabled = false;'
           # 'set cluster setting kv.range_split.by_load_enabled = false;'
           'set cluster setting kv.raft_log.disable_synchronization_unsafe = true;'
           'alter range default configure zone using num_replicas = 1;'
           '" | {0} sql --insecure '
           '--url="postgresql://root@{1}?sslmode=disable"').format(EXE, ip)

    call_remote(ip, cmd, "Failed to set cluster settings.")


def grep_for_term(config, term):

	nodes = config["hot_nodes"] + config["warm_nodes"]

	out_dir = config["out_dir"]
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
		
	save_params(config, out_dir)

	outfile = os.path.join(out_dir, "bumps.csv")
	print(outfile)

	ssh = "sudo ssh {0} '{1}'"
	template= 'grep -ir "{0}" /data/logs/cockroach.node-* | wc -l'.format(term)
	ps = []
	with open(outfile, "w") as f:
		i = 1

	with open(outfile, "a") as f:
		for n in nodes:
			cmd = ssh.format(n["ip"], template)
			print(cmd)
			p = subprocess.Popen(shlex.split(cmd), stdout=f)
			p.wait()

		
def start_cluster(nodes):
    if len(nodes) == 0:
        return

    first = nodes[0]
    start_cockroach_node(first).wait()

    ps = []
    for n in nodes[1:]:
        ps.append(start_cockroach_node(n, join=first["ip"]))

    for p in ps:
        p.wait()

    set_cluster_settings(first)


def build_cockroach(node, commit):
    cmd = ("ssh {0} 'export GOPATH=/usr/local/temp/go "
           "&& cd {1} && git fetch origin {2} && git checkout {2} && git pull origin {2} && git submodule update --init"
           "&& (make build || "
           "(./bin/dep ensure && make clean && make build))'") \
           .format(node["ip"], COCKROACH_DIR, commit)

    return subprocess.Popen(shlex.split(cmd))


def build_cockroach_commit(nodes, commit):
    ps = [build_cockroach(n, commit) for n in nodes]

    for p in ps:
        p.wait()


def cleanup_previous_experiment(config):
    ps = []
    for n in config["workload_nodes"]:
        p = kill_cockroach_node(n)
        ps.append(p)

    for n in config["hot_nodes"] + config["warm_nodes"]:
        p = kill_cockroach_node(n)
        ps.append(p)

    for p in ps:
        p.wait()


def set_hot_keys(nodes, keys):
    if len(keys) == 0:
        return

    values = ', '.join(map(lambda k: "({})".format(k), keys))

    for n in nodes:
        ip = n["ip"]
        cmd = ('echo "'
               'alter table kv.kv hotkey at values {2};'
               '" | {0} sql --insecure '
               '--url="postgresql://root@{1}?sslmode=disable"').format(EXE, ip, values)

        call_remote(ip, cmd, "Failed to set cluster settings.")


def init_experiment(config):
    nodes = config["workload_nodes"] \
            + config["warm_nodes"] \
            + config["hot_nodes"]

    build_cockroach_commit(nodes, config["cockroach_commit"])

    # Start hot node separately from warm nodes
    # start_cluster(config["hot_nodes"])
    start_cluster(config["warm_nodes"] + config["hot_nodes"]) # no, start them together for now


def save_params(exp_params, out_dir):
    params = {
        "exp_params": exp_params
    }

    path = os.path.join(out_dir, "params.json")
    with open(path, "w") as f:
        json.dump(params, f, indent=4)


def read_params(out_dir):
    path = os.path.join(out_dir, "params.json")
    with open(path, "r") as f:
        params = json.load(f)
        return params["exp_params"]


def vary_zipf_skew(config, skews):
    if ("benchmark" in config and
        "run_args" in config["benchmark"] and
        "distribution" in config["benchmark"]["run_args"] and
        "type" in config["benchmark"]["run_args"]["distribution"] and
        config["benchmark"]["run_args"]["distribution"]["type"] == "zipf"):
    
        out_dir = config["out_dir"]
        exps = []
        
        for i in range(len(skews)):
            s = skews[i]
            
            c = config["benchmark"]["run_args"]["concurrency"][i]

            e = copy.deepcopy(config)
            if "params" not in e["benchmark"]["run_args"]["distribution"]:
                e["benchmark"]["run_args"]["distribution"]["params"] = {}

            if "skew" in e["benchmark"]["run_args"]["distribution"]["params"]:
                print("WARNING: Overwriting skew param in experiment config!")

            e["benchmark"]["run_args"]["distribution"]["params"]["skew"] = s
            e["benchmark"]["run_args"]["concurrency"] = c
            e["out_dir"] = os.path.join(out_dir, "skew-{0}".format(i))
            exps.append(e)

        return exps

    else:
        raise ValueError(
            "Passed experiment that does not use Zipf distribution!")


def parse_bench_args(bench_config, is_warmup=False, hot_key=None):
    args = []
    if "duration" in bench_config:
    	if is_warmup:
    		args.append("--duration={}s".format(bench_config["warmup_duration"]))
    	else: 
    		args.append("--duration={}s".format(bench_config["duration"]))
    
    if "drop" in bench_config and bench_config["drop"] is True:
        args.append("--drop")

    if "concurrency" in bench_config:
        args.append("--concurrency={}".format(bench_config["concurrency"]))

    if "splits" in bench_config:
        args.append("--splits={}".format(bench_config["splits"]))

    if "read_percent" in bench_config:
        args.append("--read-percent={}".format(bench_config["read_percent"]))

    if "n_statements_per_txn" in bench_config:
        args.append("--stmt-per-txn={}".format(bench_config["n_statements_per_txn"]))

    if "n_keys_per_statement" in bench_config:
        args.append("--batch={}".format(bench_config["n_keys_per_statement"]))
        
    if "distribution" in bench_config:
        d = bench_config["distribution"]
        params = d["params"]

        if d["type"] == "zipf":
            args.append("--zipfian")
            args.append("--s={1}".format(args, params["skew"]))
            
            if "use_original_zipfian" in bench_config:
                args.append("--useOriginal={}".format(bench_config["use_original_zipfian"]))
				
    if hot_key:
        args.append("--hotkey={}".format(hot_key))
		
    if "keyspace" in bench_config:
        args.append("--keyspace={}".format(bench_config["keyspace"]))

    return " ".join(args)


def init_workload(b, name, urls, workload_nodes):

	args = parse_bench_args(b["init_args"], is_warmup=True)
	cmd = "{0} workload init {1} {2} {3}".format(EXE, name, urls, args)

	ip = workload_nodes[0]["ip"]
	call_remote(ip, cmd, "Failed to initialize benchmark")


def set_database_settings(nodes, create_partition, hot_key):

	ip = nodes[0]["ip"]
	cmd = ('echo "'
			'alter range default configure zone using num_replicas = 1;')
	if create_partition:
		cmd +=  'alter table kv partition by range(k) (partition hot values from (minvalue) to ({0}), partition warm values from ({0}) to (maxvalue));'.format(hot_key)
		cmd += "alter partition hot of table kv configure zone using constraints='\\''[+region=newyork]'\\'';"
		cmd += "alter partition warm of table kv configure zone using constraints='\\''[-region=newyork]'\\'';"
	
	cmd += ('" | {0} sql --insecure --database=kv '
			'--url="postgresql://root@{1}?sslmode=disable"').format(EXE, ip)
	
	call_remote(ip, cmd, "Failed to assign partition affinity")


def extract_config_params(config):

	out_dir = config["out_dir"]
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)

	nodes = config["warm_nodes"]
	if config["use_hot_nodes_as_gateways"]:
		nodes += config["hot_nodes"]

	b = config["benchmark"]
	name = b["name"]

	urls = ["postgresql://root@{0}:26257?sslmode=disable".format(n["ip"])
			for n in nodes]
	urls = " ".join(urls)

	workload_nodes = config["workload_nodes"]

	return out_dir, nodes, b, name, urls, workload_nodes


def run_workload(workload_nodes, b, name, urls, out_dir, is_warmup=False, hot_key=None):
	
	i = 0
	ps = []
	for wn in workload_nodes:
		args = parse_bench_args(b["run_args"], is_warmup=is_warmup, hot_key=hot_key)
		cmd = "{0} workload run {1} {2} {3}".format(EXE, name, urls, args)
		ip = wn["ip"]

		if is_warmup:

			# Call remote
			cmd = "sudo ssh {0} '{1}'".format(ip, cmd)
			print(cmd)

			ps.append(subprocess.Popen(shlex.split(cmd)))

		else:
			path = os.path.join(out_dir, "bench_out_{0}.txt".format(i))

			p = call_remote_redirect_stdout(ip, cmd, "run_workload_err", path)
			ps.append(p)

		i += 1

	for p in ps:
		p.wait()


def prepopulate_cluster(config):

	out_dir, nodes, b, name, urls, workload_nodes = extract_config_params(config)
	init_workload(b, name, urls, workload_nodes)
	set_database_settings(nodes, config["should_create_partition"], config["hot_key"])

	b_copy = copy.deepcopy(b)
	b_copy["run_args"]["warmup_duration"] = 30
	b_copy["run_args"]["read_percent"] = 0

	# populate with writes
	hot_key = None
	if "hot_key" in config:
		hot_key = config["hot_key"]
	run_workload(workload_nodes, b_copy, name, urls, out_dir, is_warmup=True, hot_key=hot_key)

	# real warmup
	run_workload(workload_nodes, b, name, urls, out_dir, is_warmup=True, hot_key=hot_key)


def warmup_cluster(config):

	out_dir, nodes, b, name, urls, workload_nodes = extract_config_params(config)

	if len(workload_nodes) == 0:
		print("No workload nodes!")
		return

	if len(nodes) == 0:
		print("No cluster nodes!")
		return

	# initialize workload on database
	init_workload(b, name, urls, workload_nodes)

	# set database settings (hot key, replicas)
	set_database_settings(nodes, config["should_create_partition"], config["hot_key"])

	# run workload
	hot_key = None
	if "hot_key" in config:
		hot_key = config["hot_key"]
	run_workload(workload_nodes, b, name, urls, out_dir, is_warmup=True, hot_key=hot_key)


def run_bench(config):

	out_dir, nodes, b, name, urls, workload_nodes = extract_config_params(config)
	
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
		
	save_params(config, out_dir)
	
	if len(workload_nodes) == 0:
		print("No workload nodes!")
		return
		
	if len(nodes) == 0:
		print("No cluster nodes!")
		return

	hot_key = None
	if "hot_key" in config:
		hot_key = config["hot_key"]
	run_workload(workload_nodes, b, name, urls, out_dir, is_warmup=False, hot_key=hot_key)
   
