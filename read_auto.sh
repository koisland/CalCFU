#!/usr/bin/env bash

# subshells don't load functions so call conda.sh manually. conda activate will fail otherwise.
source ~/miniconda3/etc/profile.d/conda.sh

conda activate calcfu

# if weighed, include -w flag
if [[ $3 == "True" ]]; then
  # take last args ($#-1)
  res=$(python3 ../read_auto.py -i $1 -o $2 -w -g $4 -p $5 -d ${@:6:$#-1})
  echo $res
elif [[ $3 == "False" ]]; then
  res=$(python3 ../read_auto.py -i $1 -o $2 -g $4 -p $5 -d ${@:6:$#-1})
  echo $res
fi