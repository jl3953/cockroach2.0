#!/bin/bash

dirname=${PWD##*/}
new_location=/proj/cops-PG0/workspaces/jl87/$dirname
mkdir $new_location

cp -R * $new_location

echo "Finish copying $dirname to $new_location"
