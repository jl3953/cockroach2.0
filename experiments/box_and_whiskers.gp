set terminal png
set xlabel "zipfian constant"
set boxwidth 0.005
# set style fill solid

# ARG1 is the output graph
# ARG2 is the input csv data file
# ARG3 is the title of the y axis

set ylabel ARG3
set output ARG1
plot ARG2 using "skew":"box_min":"whisker_min":"whisker_high":"box_high" with candlesticks lt -1 lw 2 whiskerbars,\
		 "" using "skew":"median":"median":"median":"median" with candlesticks lt -1 lw 2 notitle,\
		 "" using "skew":"median" with linespoint notitle
