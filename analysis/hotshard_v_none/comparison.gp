set terminal png
set xlabel "zipfian constant"
set boxwidth 0.05
set ylabel "throughput (txn/sec)"

set output "comparison.png"
set title "6-key txns vanilla vs rpcserver hotshard, hotkey=[0]"
plot "vanilla_six.csv" using "skew":"box_min":"whisker_min":"whisker_high":"box_high" notitle with candlesticks lt -1 lw 2 whiskerbars,\
		 "" using "skew":"median":"median":"median":"median" with candlesticks lt -1 lw 2 notitle,\
		 "" using "skew":"median" title "vanilla CRDB" with linespoint,\
		 "hotshard.csv" using "skew":"box_min":"whisker_min":"whisker_high":"box_high" notitle with candlesticks lt -1 lw 2 whiskerbars,\
		 "" using "skew":"median":"median":"median":"median" with candlesticks lt -1 lw 2 notitle,\
		 "" using "skew":"median" title "hotshard rpc" with linespoint,\
		 "hotshard_more_machines.csv" using "skew":"box_min":"whisker_min":"whisker_high":"box_high" notitle with candlesticks lt -1 lw 2 whiskerbars,\
		 "" using "skew":"median":"median":"median":"median" with candlesticks lt -1 lw 2 notitle,\
		 "" using "skew":"median" title "hotshard rpc + extra machine" with linespoint


set output "comparison-med.png"
plot "vanilla_six.csv" using "skew":"median" title "vanilla CRDB" with linespoint,\
		 "hotshard.csv" using "skew":"median" title "hotshard rpc" with linespoint,\
		 "hotshard_more_machines.csv" using "skew":"median" title "hotshard rpc + extra machine" with linespoint



