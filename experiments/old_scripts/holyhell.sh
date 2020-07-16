#!/bin/bash

for skew in 1.1 1.2 1.3 1.4 1.5 1.6 1.7 1.8 1.9 2.0
do
	set -x
	sudo ./cockroach workload run kv \
		postgresql://root@192.168.1.2:26257?sslmode=disable \
		postgresql://root@192.168.1.3:26257?sslmode=disable \
		postgresql://root@192.168.1.4:26257?sslmode=disable \
		postgresql://root@192.168.1.5:26257?sslmode=disable \
		postgresql://root@192.168.1.6:26257?sslmode=disable \
		postgresql://root@192.168.1.7:26257?sslmode=disable \
		postgresql://root@192.168.1.8:26257?sslmode=disable \
		postgresql://root@192.168.1.9:26257?sslmode=disable \
		postgresql://root@192.168.1.10:26257?sslmode=disable \
		postgresql://root@192.168.1.11:26257?sslmode=disable \
		postgresql://root@192.168.1.12:26257?sslmode=disable \
		postgresql://root@192.168.1.13:26257?sslmode=disable \
		postgresql://root@192.168.1.14:26257?sslmode=disable \
		postgresql://root@192.168.1.15:26257?sslmode=disable \
		postgresql://root@192.168.1.16:26257?sslmode=disable \
		--zipfian --read-percent=90 --skew=$skew --duration=30s &> statsv2-$skew
	set +x
done
