set terminal png
set xlabel "throughput (txn/sec)"

# ARG1 is the csv file
# ARG2 is the output location of the graphs
# ARG3 is the suffix
# ARG4 is the skew

set ylabel "p50 (ms)"
set title "latency throughput (p50)"
set output "lt_comparison_one_node.png"
set offset 1, 1, 1, 1
plot "lt_one_node.csv" using "ops/sec(cum)":"p50(ms)" title "1 node" with linespoint,\
		 "" using "ops/sec(cum)":"p50(ms)":"concurrency" with labels point pt 7 offset char 1, 1 notitle,\
		 "lt_one_node_disabled2.csv" using "ops/sec(cum)":"p50(ms)" title "1 node, disabled cores=2" with linespoint,\
		 "" using "ops/sec(cum)":"p50(ms)":"concurrency" with labels point pt 7 offset char 1, 1 notitle


set output "lt_comparison_two_nodes.png"
set offset 1, 1, 1, 1
plot "lt_two_nodes.csv" using "ops/sec(cum)":"p50(ms)" title "2 nodes" with linespoint,\
		 "lt_two_nodes_disabled2.csv" using "ops/sec(cum)":"p50(ms)" title "2 nodes, disabled cores=2" with linespoint,\
		 "lt_two_nodes_disabled4.csv" using "ops/sec(cum)":"p50(ms)" title "2 nodes, disabled cores=4" with linespoint


set output "lt_comparison_three_nodes.png"
set offset 1, 1, 1, 1
plot "lt_three_nodes.csv" using "ops/sec(cum)":"p50(ms)" title "3 nodes" with linespoint,\
		 "" using "ops/sec(cum)":"p50(ms)":"concurrency" with labels point pt 7 offset char 1, 1 notitle,\
		 "lt_three_nodes_disabled2.csv" using "ops/sec(cum)":"p50(ms)" title "3 nodes, disabled cores=2" with linespoint,\
		 "" using "ops/sec(cum)":"p50(ms)":"concurrency" with labels point pt 7 offset char 1, 1 notitle,\
		 #"lt_three_nodes_disabled4.csv" using "ops/sec(cum)":"p50(ms)" title "3 nodes, disabled cores=4" with linespoint,\
		 #"" using "ops/sec(cum)":"p50(ms)":"concurrency" with labels point pt 7 offset char 1, 1 notitle


