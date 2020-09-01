set terminal png
set xlabel "throughput (txn/sec)"

set ylabel "p50 (ms)"
set title "latency throughput (p50)"
set output "lt_comparison_one_node.png"
plot "lt_one_node.csv" using "ops/sec(cum)":"p50(ms)" title "1 node" with linespoint,\
		 "lt_one_node_disabled2.csv" using "ops/sec(cum)":"p50(ms)" title "1 node, disabled cores=2" with linespoint,\
		 "lt_one_node_disabled4.csv" using "ops/sec(cum)":"p50(ms)" title "1 node, disabled cores=4" with linespoint,\

set output "lt_comparison_two_nodes.png"
plot "lt_two_nodes.csv" using "ops/sec(cum)":"p50(ms)" title "2 nodes" with linespoint,\
		 "lt_two_nodes_disabled2.csv" using "ops/sec(cum)":"p50(ms)" title "2 nodes, disabled cores=2" with linespoint,\
		 "lt_two_nodes_disabled4.csv" using "ops/sec(cum)":"p50(ms)" title "2 nodes, disabled cores=4" with linespoint


set output "lt_comparison_three_nodes.png"
plot "lt_three_nodes.csv" using "ops/sec(cum)":"p50(ms)" title "3 nodes" with linespoint,\
		 "lt_three_nodes_disabled2.csv" using "ops/sec(cum)":"p50(ms)" title "3 nodes, disabled cores=2" with linespoint,\
		 "" using "ops/sec(cum)":"p50(ms)":"concurrency" with labels point pt 7 offset char 1, 1 notitle,\
		 #"lt_three_nodes_disabled4.csv" using "ops/sec(cum)":"p50(ms)" title "3 nodes, disabled cores=4" with linespoint,\
		 #"" using "ops/sec(cum)":"p50(ms)":"concurrency" with labels point pt 7 offset char 1, 1 notitle


set output "lt_comparison_nodes.png"
plot "lt_one_node.csv" using "ops/sec(cum)":"p50(ms)" title "1 node" with linespoint,\
		 "lt_two_nodes.csv" using "ops/sec(cum)":"p50(ms)" title "2 nodes" with linespoint,\
		 "lt_three_nodes.csv" using "ops/sec(cum)":"p50(ms)" title "3 nodes" with linespoint

