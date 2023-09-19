#!/bin/bash

##################
## Run the deepcell container in order to perform whole-cell and nuclear segmentation
## More info at: https://github.com/vanvalenlab/deepcell-applications
##
## Zach Fogarty
## 6/7/2022
##################

export SINGULARITY_CACHEDIR=$PWD
wkfldir=$1
imgfile=$2
fbname=$(basename "$imgfile" | cut -d. -f1)

NCHANNEL=$3 
MCHANNEL=$(echo $4 | tr ',' ' ')  #13   ## if there are multiple channels to use, they should be space-delimited
OUTDIR=$wkfldir/SEGMASKS

if [ ! -d $OUTDIR ] 
then
	mkdir -p $OUTDIR
fi

## whole-cell segmentation
singularity run -B $wkfldir deepcell.sif mesmer \
 --nuclear-image $imgfile \
 --membrane-image $imgfile \
 --nuclear-channel $NCHANNEL \
 --membrane-channel $MCHANNEL \
 --output-directory $OUTDIR \
 --output-name ${fbname}_WholeCellMask.tiff \
 --compartment whole-cell