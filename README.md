# MyCodexPipeline
This is the workflow to pre-process images into single cell quantification.

## Description
This workflow transforms pile of files from Codex Processor folder into one OME.TIFF per Region of Interest (ROI).
Those OME.TIFF go through a meteric calculation step which can be investigated for image based quality metrics. 
Then DeepCell is run to generate segmentation masks.
Those original OME.TIFF files and SEGMASKs are then joined within QuPath to create visulalizations and quantification. 
The quantification is automatically produced as tsv output tables.

## Prepartion

build_deepcell_singularity.sh is included to create the correct singularity contaner for Deepcell.

`/bin/bash $WKFL/build_deepcell_singularity.sh`

Additonally you will need to edit the variables `WKFL` & `QPATHFULL` within run_pipeline_codex.sh to your installations within your enviroment.

## Running the code

`./run_pipeline_codex.sh -i <input processor folder> -o <output folder> -d <nuclear channel> -m <membrane channel(s)>`