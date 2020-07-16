set terminal png
set xlabel "zipfian constant"
set boxwidth 0.05
set ylabel "throughput (txn/sec)"

set output "comparison.png"
plot ARG1 using "skew":"box_min":"whisker_min":"whisker_high":"box_high" notitle with candlesticks lt -1 lw 2 whiskerbars,\
		 "" using "skew":"median":"median":"median":"median" with candlesticks lt -1 lw 2 notitle,\
		 "" using "skew":"median" title "six keys, instant hot key" with linespoint,\
		 ARG2 using "skew":"box_min":"whisker_min":"whisker_high":"box_high" notitle with candlesticks lt -1 lw 2 whiskerbars,\
		 "" using "skew":"median":"median":"median":"median" with candlesticks lt -1 lw 2 notitle,\
		 "" using "skew":"median" title "five keys" with linespoint,\
		ARG3 using "skew":"box_min":"whisker_min":"whisker_high":"box_high" notitle with candlesticks lt -1 lw 2 whiskerbars,\
		 "" using "skew":"median":"median":"median":"median" with candlesticks lt -1 lw 2 notitle,\
		 "" using "skew":"median" title "six keys" with linespoint

set output "comparison-med.png"
plot ARG1 using "skew":"median" title "six keys, instant hot key" with linespoint,\
		 ARG2 using "skew":"median" title "five keys" with linespoint,\
		ARG3 using "skew":"median" title "six keys" with linespoint



