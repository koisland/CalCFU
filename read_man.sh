#!/usr/bin/env bash

# subshells don't load functions so call conda.sh manually. conda activate will fail otherwise.
source ~/miniconda3/etc/profile.d/conda.sh

conda activate calcfu

python3 ../read_man.py -i $1 -o $2