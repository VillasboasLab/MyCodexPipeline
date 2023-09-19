import os,json,sys,re,csv,glob,argparse
import tifffile
import xarray as xr
from pathlib import Path
from typing import Union
import pandas as pd
import numpy as np
from pprint import pprint

channelDesign = {'ch001':'DAPI','ch002':'AF750','ch003':'Atto550','ch004':'Cy5'}
# DAPI=Blue, C2=Green, C3=Red, C4=Yellow.

def rgb_to_hex(r, g, b):
	return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def getUniqueColorDesign(chnl,offset):
	if chnl == 'ch001':
		hx = rgb_to_hex( (0+offset), (0+offset), 255  ) ## Want Blues (0, 0, 255)
	elif chnl == 'ch002':
		hx = rgb_to_hex( (0+offset), 200, (0+offset)  ) ## Want Greens (0, 200, 0)
	elif chnl == 'ch003':
		hx = rgb_to_hex( 255, (0+offset), (0+offset)  ) ## Want Reds (255, 0, 0)
	elif chnl == 'ch004':
		hx = rgb_to_hex( 245, 245, (0+offset)  ) ## Want Yellows (0, 200, 0)
	else:
		hx = "#F0F0F0"
	return hx

def rgba_to_int(r: int, g: int, b: int, a: int) -> int:
    """Use int.from_bytes to convert a color tuple.
    >>> print(rgba_to_int(0, 0, 0, 0))  = 0
    >>> print(rgba_to_int(0, 1, 135, 4)) = 100100
    """
    return int.from_bytes([r, g, b, a], byteorder="big", signed=True)

def getUniqueColorPrimativeInt(chnl,offset):
	if chnl == 'ch001':
		hx = rgba_to_int( (0+offset), (0+offset), 255, 255 ) ## Want Blues (0, 0, 255)
	elif chnl == 'ch002':
		hx = rgba_to_int( (0+offset), 200, (0+offset), 255  ) ## Want Greens (0, 200, 0)
	elif chnl == 'ch003':
		hx = rgba_to_int( 255, (0+offset), (0+offset), 255  ) ## Want Reds (255, 0, 0)
	elif chnl == 'ch004':
		hx = rgba_to_int( 245, 245, (0+offset), 255  ) ## Want Yellows (0, 200, 0)
	else:
		hx = 0
	return hx

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]

def get_channel_xml(i,mark,channel):
	cy = channelDesign[channel]
	clc = getUniqueColorPrimativeInt(channel, i)
	outStr = f"""<Channel Color="{clc}" ID="Channel:{i}" Name="{mark}" Fluor="{cy}"  SamplesPerPixel="1" ContrastMethod="Fluorescence" />"""
	return outStr

def write_ometiff(targetDir, targetPrefix, outpath, pxSize):
	allTiffs = glob.glob(os.path.join(targetDir,"reg*.tif"))
	allBaseFH = [ os.path.basename(i) for i in allTiffs]
	stepwiseTable = pd.DataFrame([i.replace('.tif','').split('_') for i in allBaseFH])
	if len(stepwiseTable.columns) == 6:
		stepwiseTable.columns = ["Sample","Cycle","Channel","Marker","Barcode","Exposure"]
	else:
		stepwiseTable.columns = ["Sample","Cycle","Channel","Marker"]
	stepwiseTable['Keep'] = 'Yes'
	stepwiseTable.sort_values(by=['Cycle', 'Channel'],inplace=True)
	## Skip All DAPIs & Blanks
	stepwiseTable.loc[stepwiseTable["Marker"].str.startswith("DAPI", na = False), 'Keep'] = 'No'
	stepwiseTable.loc[(stepwiseTable['Cycle']=='cyc002') & (stepwiseTable['Channel']=='ch001'), 'Keep'] = 'Yes'
	# Skip 1st round - old code when blanks where not labelled.
	stepwiseTable.loc[stepwiseTable['Cycle']=='cyc001', 'Keep'] = 'Yes'
	cyc1Tmp = stepwiseTable.loc[stepwiseTable['Cycle']=='cyc001']
	stepwiseTable.loc[stepwiseTable['Cycle']=='cyc001', 'Marker'] = "Background_"+cyc1Tmp['Channel']	
	## Drop any Empty
	stepwiseTable.loc[stepwiseTable['Marker']=='Empty', 'Keep'] = 'No'
	stepwiseTable.loc[stepwiseTable['Marker']=='Blank', 'Keep'] = 'No'
	stepwiseTable['FileHandle'] = pd.Series(allTiffs)
	stepwiseTable.reset_index(drop=True, inplace=True)

	dat = []
	xmlChan = []
	xDim = []
	yDim = []
	cDim = []
	u = 0
	for index, row in stepwiseTable.iterrows():
		if row['Keep'] == 'No':
			continue
		## Check to ensure import TIFF is single image type.
		tmpImg = tifffile.TiffFile(row['FileHandle'])
		if not len(tmpImg.pages) == 1:
			pprint([index,row])
			sys.exit("Unexpected: Input Tiff file is multiple images.")
		xDim.append(tmpImg.pages[0].shape[1])
		yDim.append(tmpImg.pages[0].shape[0])
		cDim.append(row['Marker'])
		print(str(u)+ ": "+str(tmpImg.pages[0].shape)+" Image:"+ os.path.basename(row['FileHandle']))
		xmlChan.append(get_channel_xml(u,row['Marker'],row['Channel']))
		dat.append(tmpImg.pages[0].asarray())
		u += 1
	imgStack = np.array(dat)

	imarr = xr.DataArray(imgStack,
		name=targetPrefix,
		dims=("c", "x", "y"),
		coords={"x": range(imgStack.shape[1]), "y": range(imgStack.shape[2]), "c": cDim}
		)
	Nc, Ny, Nx = imarr.shape
	channels_xml = '\n'.join(xmlChan)
	outname = os.path.splitext(os.path.basename(outpath))[0]

	## Notes:
	# attribute name="PhysicalSizeX" use="optional" type="PositiveFloat" Physical size of a pixel. Units are set by PhysicalSizeXUnit.
	# attribute name="PhysicalSizeXUnit" use="optional" default="µm" type="UnitsLength"  The units of the physical size of a pixel - default:microns[µm].
	# attribute name="PhysicalSizeY" use="optional" type="PositiveFloat" Physical size of a pixel. Units are set by PhysicalSizeYUnit.
	# attribute name="PhysicalSizeYUnit" use="optional" default="µm" type="UnitsLength"  The units of the physical size of a pixel - default:microns[µm].
	xml = f"""<?xml version="1.0" encoding="UTF-8"?>
	<OME xmlns="http://www.openmicroscopy.org/Schemas/OME/2016-06"
			xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
			xsi:schemaLocation="http://www.openmicroscopy.org/Schemas/OME/2016-06 http://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd">
		<Image ID="Image:0" Name="{outname}">
			<Pixels BigEndian="false"
					DimensionOrder="XYCZT"
					ID="Pixels:0"
					Interleaved="false"
					SizeC="{Nc}"
					SizeT="1"
					SizeX="{Nx}"
					SizeY="{Ny}"
					SizeZ="1"
					PhysicalSizeX="{pxSize}"
					PhysicalSizeXUnit="nm"
					PhysicalSizeY="{pxSize}"
					PhysicalSizeYUnit="nm"
					Type="float">
				<TiffData />
				{channels_xml}
			</Pixels>
		</Image>
	</OME>
	"""
	tifffile.imwrite(outpath, data=imarr.values, description=xml, contiguous=True )
	stepwiseTable.to_csv(outpath.replace('.tiff','')+'_table.csv', index=False)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Convert CODEX processor directory to OME.TIFFs')
	parser.add_argument('-i', '--indir', help='CODEX processor directory.', nargs='?', type=str, dest="expDir", metavar="DIR",required=True)
	parser.add_argument('-o', '--outdir', help='Directory to write OME.TIFF files to.', nargs='?', type=str, dest="outDir", metavar="DIR",required=True)
	args = parser.parse_args()

	allSlidesToConvert = filter(os.path.isdir, glob.glob( os.path.join(args.expDir,'stitched','reg*')) )
	runLog = glob.glob(os.path.join(args.expDir,'diagnostics','*.log'))
	if len(runLog) < 1:
		sys.exit("ERROR - Run Log Issue!")

	xyPixSize=377.1 ## Approx default, in case log is missing
	for line in open(runLog[0], "r"):
		if re.search("xyResolution", line):
			print(" Found: "+line,)
			xyPixSize=line.split('=')[1].strip()

	for ele in allSlidesToConvert:
		inPrefix = os.path.basename(os.path.normpath(ele))
		print(" Loading: "+inPrefix+" ...")
		outpath = os.path.join(args.outDir,inPrefix+".ome.tiff")
		write_ometiff(ele, inPrefix, outpath, xyPixSize)
		print("  Saved to: "+outpath)
		
