#! /bin/bash
# by Raymond Moore

usage()
{
cat << EOF
###########################################################################
##	Generate OME.TIFF, QC Reports, QuPath Project & Quantification Files for Codex MxIF.
##
##	Script Options:
##	-i	<input>	 - (REQUIRED)  Input directory to Raw Codex Processor files.
##	-o	<output> - (REQUIRED)  Working directory, to output files from workflow.
##	-d	<DAPI>	 - (OPTIONAL)  Provide the Channel Index for DAPI [Default = 0]. 
##	-m	<MEMBR>	 - (OPTIONAL)  Provide the Channel Index for Membrane [Default = 11].
##	-t	<title>	 - (OPTIONAL)  Provide an optional name for Report title(s). NO SPACES!
##	-h			- Display Help 
##
###########################################################################
## Authors:             Raymond Moore
##For questions, comments, or concerns, contact 
##       Raymond (moore.raymond@mayo.edu)
EOF
}

### Pre determined Variables: Edit Once ###
TITLE="Codex_MxIF_Analysis"
WKFL=Modules/
QPATHFULL=/research/biotools/qupath/0.4.3/bin
DAPIIDX=0
MEMBRIDX=7



while getopts "i:o:d:m:t:h" OPTION; do
  case $OPTION in
	h) usage
		exit ;;
	i) INPUT=$OPTARG ;;
	o) OUTPUT=$OPTARG ;;
	d) DAPIIDX=$OPTARG ;;
	m) MEMBRIDX=$OPTARG ;;
	t) TITLE=$OPTARG ;;
   \?) echo -e "\e[1;31mInvalid option: -$OPTARG.\e[0m"
       usage
       exit ;;
    :) echo -e "\e[1;31mOption -$OPTARG requires an argument.\e[0m"
       usage
       exit ;;
  esac
done

if [ ! -s "$INPUT" ]
then
	echo -e "\e[1;31mMust provide a input directory.\e[0m"
	usage
	exit 1;
fi

mkdir -p $OUTPUT/{OMETIFF,SEGMASKS,QUPATH,REPORTS}

## Step 1: Generate OME.TIFF's
python $WKFL/convertCodexDir2Ometiff.py -i $INPUT -o $OUTPUT/OMETIFF

## QC 1: General non-Referenced Image Metrics
python $WKFL/OMETIFF_QC_02.py --save_data --whole_slide -i "$OUTPUT/OMETIFF" -o "$OUTPUT/REPORTS"

## Segementation Setup: need to run just once.
# /bin/bash $WKFL/build_deepcell_singularity.sh

for ROIFH in $OUTPUT/OMETIFF/*.ome.tiff; do 
	echo $ROIFH;
 	$WKFL/run_deepcell_singularity.sh $OUTPUT $ROIFH $DAPIIDX $MEMBRIDX
done

## Make QuPath project, and generate Quantification
$QPATHFULL/QuPath script $WKFL/createNewProject_Codex.groovy -a $OUTPUT 

PRGT=$(ls $OUTPUT/QUPATH/*.qpproj)
$QPATHFULL/QuPath script $WKFL/export_individual_qupath_rois.groovy -a $OUTPUT -p $PRGT



