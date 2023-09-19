#!/bin/bash

##################
## Pull down the 'deepcell-applications' container from dockerhub,
## and make a few small changes in order to run it successfully.
##
## Zach Fogarty
## 6/7/2022
##################

## Assume adding this temp dir from the Running DIR
mkdir -p temp
cd temp
export SINGULARITY_CACHEDIR=$PWD


## grab the existing container from dockerhub (this needs to happen in a directory that I own)
singularity build initialdeepcell.sif docker://vanvalenlab/deepcell-applications

## modify the container and re-build it
singularity build --sandbox mysandbox initialdeepcell.sif 
cp mysandbox/usr/src/app/run_app.py ../
chmod ug+x ../run_app.py
echo "export PYTHONPATH=/usr/src/app" >> mysandbox/environment
singularity build ../deepcell.sif mysandbox/


## clean up intermediate stuff
cd ..
/bin/rm -rf temp

