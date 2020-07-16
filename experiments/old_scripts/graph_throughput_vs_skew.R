#!/usr/bin/env Rscript

library(R.utils)
library(scales)
library(magrittr)
library(dplyr)
library(readr)
library(tidyr)
library(ggplot2)

csv <- cmdArg("csv")
out <- cmdArg("out")

if (is.null(csv)) {
  throw("--csv argument required")
}

if (is.null(out)) {
  throw("--out argument required")
}

measurements <- read_csv(csv)

data <- measurements %>%
  filter(sample_type %in% c("total_aggregate")) %>%
  select(
    "ops/sec",
    "key_dist_skew"
  ) %>%
  rename(
    "tput" = "ops/sec",
    "skew" = "key_dist_skew"
  )

data %>%
  ggplot(aes(x = skew)) +
  geom_point(aes(y = tput), stat = "identity") +
  geom_line(aes(y = tput), stat = "identity") +
  labs(
    x = "Zipf Skew",
    y = "Throughput (txns/sec)"
  ) +
  scale_x_continuous(labels = number_format(accuracy = 0.01)) +
  scale_y_continuous(labels = comma) +
  theme_classic()

ggsave(out)