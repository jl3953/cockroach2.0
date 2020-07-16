#!/usr/bin/env Rscript

library(R.utils)
library(scales)
library(magrittr)
library(dplyr)
library(readr)
library(tidyr)
library(ggplot2)
require(purrr)

# csv <- '../logs/kv-skew/kvbench_results.csv,../logs/kv-skew-hot-1/kvbench_results.csv,../logs/kv-skew-hot-10/kvbench_results.csv,'
csv <- cmdArg("csv")
out <- cmdArg("out")

if (is.null(csv)) {
  throw("--csv argument required")
}

if (is.null(out)) {
  throw("--out argument required")
}

files <- as.list(strsplit(csv, ",")[[1]])
measurements <- files %>%
  map(read_csv) %>%
  reduce(rbind)

data <- measurements %>%
  filter(sample_type %in% c("total_aggregate")) %>%
  select(
    "p50_ms",
    "p95_ms",
    "p99_ms",
    "key_dist_skew",
    "n_hot_keys"
  ) %>%
  rename(
    "skew" = "key_dist_skew"
  )

data$n_hot_keys <- factor(data$n_hot_keys) 

xlims <- c(1.1, 2)
ylims <- c(0, 1500)

data %>%
  ggplot(aes(x = skew, y = p50_ms, color = n_hot_keys)) +
  geom_point() +
  geom_line() +
  labs(
    title = "Transaction Latency vs. Skew",
    x = "Zeta Skew",
    y = "Latency (ms)",
    color = "# Hot Keys"
  ) +
  scale_x_continuous(labels = number_format(accuracy = 0.01), breaks = pretty_breaks(n = 10), limits = xlims) +
  scale_y_continuous(labels = comma, breaks = pretty_breaks(n = 20), limits = ylims) +
  theme_classic() +
  theme(
    legend.position = "bottom"
  )

ggsave(out, width = 16, height = 9, dpi = 300)
