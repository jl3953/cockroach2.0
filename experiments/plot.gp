set terminal png
set xlabel "zipfian constant"

# ARG1 is the csv file
# ARG2 is the output location of the graphs
# ARG3 is the suffix

set ylabel "throughput (txns/sec)"
set output ARG2."/tp_v_skew_trial".ARG3.".png"
plot ARG1 using "skew":"ops/sec(cum)" with linespoint

set ylabel "p50 latency (ms)"
set output ARG2."/p50_v_skew_trial".ARG3.".png"
plot ARG1 using "skew":"p50(ms)" with linespoint

set ylabel "p95 latency (ms)"
set output ARG2."/p95_v_skew_trial".ARG3.".png"
plot ARG1 using "skew":"p95(ms)" with linespoint

set ylabel "p99 latency (ms)"
set output ARG2."/p99_v_skew_trial".ARG3.".png"
plot ARG1 using "skew":"p99(ms)" with linespoint
