set terminal png
set xlabel "throughput (txn/sec)"

set ylabel "p99 (ms)"
set title "latency throughput (p99)"
set output "lt_comparison_one_node.png"
plot "lt_one_node.csv" using "ops/sec(cum)":"p99(ms)" title "1 node" with linespoint,\
		 "lt_one_node_disabled2.csv" using "ops/sec(cum)":"p99(ms)" title "1 node, disabled cores=2" with linespoint,\
		 "lt_one_node_disabled4.csv" using "ops/sec(cum)":"p99(ms)" title "1 node, disabled cores=4" with linespoint,\

set output "lt_comparison_two_nodes.png"
plot "lt_two_nodes.csv" using "ops/sec(cum)":"p99(ms)" title "2 nodes" with linespoint,\
		 "lt_two_nodes_disabled2.csv" using "ops/sec(cum)":"p99(ms)" title "2 nodes, disabled cores=2" with linespoint,\
		 "lt_two_nodes_disabled4.csv" using "ops/sec(cum)":"p99(ms)" title "2 nodes, disabled cores=4" with linespoint


set output "lt_comparison_three_nodes.png"
plot "lt_three_nodes.csv" using "ops/sec(cum)":"p99(ms)" title "3 nodes" with linespoint,\
		 "lt_three_nodes_disabled2.csv" using "ops/sec(cum)":"p99(ms)" title "3 nodes, disabled cores=2" with linespoint,\
		 "lt_three_nodes_disabled4.csv" using "ops/sec(cum)":"p99(ms)" title "3 nodes, disabled cores=4" with linespoint

set output "lt_comparison_nodes.png"
plot "lt_one_node.csv" using "ops/sec(cum)":"p99(ms)" title "1 node" with linespoint,\
		 "lt_two_nodes.csv" using "ops/sec(cum)":"p99(ms)" title "2 nodes" with linespoint,\
		 "lt_three_nodes.csv" using "ops/sec(cum)":"p99(ms)" title "3 nodes" with linespoint

set output "lt_comparison_one_node_keys.png"
plot "lt_one_node_1key.csv"  using "ops/sec(cum)":"p99(ms)" title "1 key" with linespoint,\
		 "lt_one_node_2keys_doagain.csv"  using "ops/sec(cum)":"p99(ms)" title "2 keys" with linespoint,\
		 "lt_one_node_3keys.csv"  using "ops/sec(cum)":"p99(ms)" title "3 keys" with linespoint,\
		 "lt_one_node_4keys.csv"  using "ops/sec(cum)":"p99(ms)" title "4 keys" with linespoint,\
		 "lt_one_node_5keys.csv"  using "ops/sec(cum)":"p99(ms)" title "5 keys" with linespoint,\
		 "lt_one_node_6keys.csv"  using "ops/sec(cum)":"p99(ms)" title "6 keys" with linespoint

set output "lt_debug_one_node_2keys.png"
plot "lt_one_node_2keys_doagain.csv"  using "ops/sec(cum)":"p99(ms)" with linespoint,\
		 "lt_one_node_2keys.csv"  using "ops/sec(cum)":"p99(ms)" with linespoint
