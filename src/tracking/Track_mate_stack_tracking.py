# @File(label="Please enter your input folder", description="Input folder", style="directory") folder_in
# @String(label="Please enter the type of correction of your image", choices={"no additional bleach correction","additional bleach correction"}, description="Correction type") cortype_in
# @Boolean(label="Crop ring in order to remove false positive signal from well wall") crop_in
# @Boolean(label="Don't show tracked image stacks") headless
# @Boolean(label="Detector: SUBPIXEL_LOCALIZATION",value=True) SUBPIXEL_LOCALIZATION 
# @Float(label="Detector: RADIUS",value=4.0) RADIUS 
# @Integer(label="Detector: TARGET_CHANNEL",value=1) TARGET_CHANNEL 
# @Float(label="Detector: THRESHOLD",value=0.5) THRESHOLD 
# @Boolean(label="Detector: MEDIAN_FILTERING",value=False) MEDIAN_FILTERING 
# @Float(label="Initial Filter: SPOT_FILTER",value=0.0) SPOT_FILTER 
# @Float(label="Filter: QUALITY",value=0.0) QUALITY 
# @Float(label="Filter: CONTRAST",value=0.0) CONTRAST 
# @Float(label="Filter: MAX_ESTIMATED_DIAMETER",value=12.0) MAX_ESTIMATED_DIAMETER 
# @Float(label="Filter: MAX_MEDIAN_INTENSITY",value=20.0) MAX_MEDIAN_INTENSITY 
# @Float(label="Tracking: LINKING_MAX_DISTANCE",value=100.0) LINKING_MAX_DISTANCE 
# @Boolean(label="Tracking: LINKING_FEATURE_PENALTIES",value=False) LINKING_FEATURE_PENALTIES
# @String(label="Tracking: LINKING_FEATURE_PENALTIES_TYPE",value="Quality") LINKING_FEATURE_PENALTIES_TYPE
# @Float(label="Tracking: LINKING_FEATURE_PENALTIES_VALUE",value=1.0) LINKING_FEATURE_PENALTIES_VALUE 
# @Boolean(label="Tracking: ALLOW_GAP_CLOSING",value=True) ALLOW_GAP_CLOSING 
# @Float(label="Tracking: GAP_CLOSING_MAX_DISTANCE",value=200.0) GAP_CLOSING_MAX_DISTANCE 
# @Integer(label="Tracking: MAX_FRAME_GAP",value=2) MAX_FRAME_GAP 
# @Boolean(label="Tracking: GAP_CLOSING_FEATURE_PENALTIES",value=False) GAP_CLOSING_FEATURE_PENALTIES
# @String(label="Tracking: GAP_CLOSING_FEATURE_PENALTIES_TYPE",value="Quality") GAP_CLOSING_FEATURE_PENALTIES_TYPE 
# @Float(label="Tracking: GAP_CLOSING_FEATURE_PENALTIES_VALUE",value=1.0) GAP_CLOSING_FEATURE_PENALTIES_VALUE 
# @Boolean(label="Tracking: ALLOW_TRACK_SPLITTING",value=False) ALLOW_TRACK_SPLITTING 
# @Float(label="Tracking: SPLITTING_MAX_DISTANCE",value=0.0) SPLITTING_MAX_DISTANCE 
# @Boolean(label="Tracking: SPLITTING_FEATURE_PENALTIES",value=False) SPLITTING_FEATURE_PENALTIES 
# @String(label="Tracking: SPLITTING_FEATURE_PENALTIES_TYPE",value="Quality") SPLITTING_FEATURE_PENALTIES_TYPE 
# @Float(label="Tracking: SPLITTING_FEATURE_PENALTIES_VALUE",value=1.0) SPLITTING_FEATURE_PENALTIES_VALUE 
# @Boolean(label="Tracking: ALLOW_TRACK_MERGING",value=False) ALLOW_TRACK_MERGING 
# @Float(label="Tracking: MERGING_MAX_DISTANCE",value=0.0) MERGING_MAX_DISTANCE 
# @Boolean(label="Tracking: MERGING_FEATURE_PENALTIES",value=False) MERGING_FEATURE_PENALTIES 
# @String(label="Tracking: MERGING_FEATURE_PENALTIES_TYPE",value="Quality") MERGING_FEATURE_PENALTIES_TYPE 
# @Float(label="Tracking: MERGING_FEATURE_PENALTIES_VALUE",value=1.0) MERGING_FEATURE_PENALTIES_VALUE 
# @Float(label="Filter Tracks: MINIMUM_TRACK_DISPLACEMENT",value=100.0) TRACK_DISPLACEMENT 
# @Float(label="Filter Tracks: TRACK_START",value=0.9) TRACK_START

from fiji.plugin.trackmate import Model
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import TrackMate
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate.detection import LogDetectorFactory
from fiji.plugin.trackmate.detection import DogDetectorFactory
from fiji.plugin.trackmate.tracking.sparselap import SparseLAPTrackerFactory
from fiji.plugin.trackmate.tracking.oldlap import LAPTrackerFactory
from fiji.plugin.trackmate.tracking import LAPUtils
import fiji.plugin.trackmate.action.ExportTracksToXML as ExportTracksToXML
from ij import IJ
from ij import ImagePlus
from ij import VirtualStack
from ij import ImageStack
from ij.process import ImageConverter
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
import sys
import fiji.plugin.trackmate.features.track.TrackDurationAnalyzer as TrackDurationAnalyzer
import fiji.plugin.trackmate.features.track.TrackSpotQualityFeatureAnalyzer as TrackSpotQualityFeatureAnalyzer
import fiji.plugin.trackmate.features.spot.SpotContrastAndSNRAnalyzerFactory as SpotContrastAndSNRAnalyzerFactory
import fiji.plugin.trackmate.features.spot.SpotContrastAndSNRAnalyzer as SpotContrastAndSNRAnalyzer
import fiji.plugin.trackmate.features.spot.SpotIntensityAnalyzerFactory as SpotIntensityAnalyzerFactory
import fiji.plugin.trackmate.features.spot.SpotIntensityAnalyzer as SpotIntensityAnalyzer
import fiji.plugin.trackmate.features.spot.SpotMorphologyAnalyzerFactory as SpotMorphologyAnalyzerFactory
import fiji.plugin.trackmate.features.spot.SpotRadiusEstimatorFactory as SpotRadiusEstimatorFactory

import os
from ij.plugin import RGBStackMerge
from ij.plugin import ChannelSplitter
from ij.gui import OvalRoi, Roi
from java.io import File
from ij.macro import MacroRunner
from ij import WindowManager
from ij.io import FileSaver
import csv
from fiji.plugin.trackmate.io import TmXmlWriter


HEADLESS=headless
folder = str(folder_in)
crop_ring = crop_in

if cortype_in == "additional bleach correction":
	correction_selection = 2
if cortype_in == "no additional bleach correction":
	correction_selection = 1
else:
	correction_selection = 1

print(folder)

correction_type_list = ["Corrected", "Corrected_bleach"]
correction_type = correction_type_list[correction_selection]
#######################



# Get currently selected image
#imp = WindowManager.getCurrentImage()

def create_folder(dirName):
	if not os.path.exists(dirName):
	    os.mkdir(dirName)
	    print("Directory " , dirName ,  " Created ")
	else:    
	    print("Directory " , dirName ,  " already exists")


def zerolistmaker(n):
    listofzeros = [0] * n
    return listofzeros


def track_cells(folder_w,filename,imp,correction):
	#imp = IJ.openImage(os.path.join(folder,filename))
	#imp.show()

	#get image dimensions, set ROI remove part of flouresncent ring
	x_size=ImagePlus.getDimensions(imp)[0]
	y_size=ImagePlus.getDimensions(imp)[1]
	x_start = 0
	y_start = 0
	#calculate alternative ROI
	if crop_ring:
		x_start = 170/2
		y_start = 170/2
		x_size = x_size - 170
		y_size = y_size - 170
	print(str(x_start) + ", " + str(y_start) + ", " + str(x_size) + ", " + str(y_size))
	imp.setRoi(OvalRoi(x_start,y_start,x_size,y_size))
	#imp_dup = imp.duplicate()
	#imp_dup.show()
	#red_corrected_img.show()
	
	IJ.run(imp, "Make Inverse", "")
	IJ.setForegroundColor(0,0,0)
	IJ.run(imp, "Fill", "stack");
	imp.killRoi()

	#imp.show()
	#sys.exit()

	

	#img_filename = filename+"_corrected_red_stack.tif"
	#folder_filename= os.path.join(well_folder,img_filename)
	#IJ.save(imp, folder_filename)
	    
	#----------------------------
	# Create the model object now
	#----------------------------
	    
	# Some of the parameters we configure below need to have
	# a reference to the model at creation. So we create an
	# empty model now.
	    
	model = Model()
	    
	# Send all messages to ImageJ log window.
	model.setLogger(Logger.IJ_LOGGER)
	    
	    
	       
	#------------------------
	# Prepare settings object
	#------------------------
	       
	settings = Settings()
	settings.setFrom(imp)
	       
	# Configure detector - We use the Strings for the keys
	settings.detectorFactory = LogDetectorFactory()
	settings.detectorSettings = { 
	    'DO_SUBPIXEL_LOCALIZATION' : SUBPIXEL_LOCALIZATION,
	    'RADIUS' : RADIUS,
	    'TARGET_CHANNEL' : TARGET_CHANNEL,
	    'THRESHOLD' : THRESHOLD,
	    'DO_MEDIAN_FILTERING' : MEDIAN_FILTERING,
	}  
	    
	# Configure spot filters - Classical filter on quality
	settings.initialSpotFilterValue = SPOT_FILTER	
	settings.addSpotAnalyzerFactory(SpotIntensityAnalyzerFactory())
	settings.addSpotAnalyzerFactory(SpotContrastAndSNRAnalyzerFactory())
	settings.addSpotAnalyzerFactory(SpotMorphologyAnalyzerFactory())
	settings.addSpotAnalyzerFactory(SpotRadiusEstimatorFactory())
	
	filter1 = FeatureFilter('QUALITY', QUALITY, True)
	filter2 = FeatureFilter('CONTRAST', CONTRAST, True)
	filter2a = FeatureFilter('ESTIMATED_DIAMETER', MAX_ESTIMATED_DIAMETER, False)
	filter2b = FeatureFilter('MEDIAN_INTENSITY', MAX_MEDIAN_INTENSITY, False)
	
	settings.addSpotFilter(filter1)
	settings.addSpotFilter(filter2)
	settings.addSpotFilter(filter2a)
	settings.addSpotFilter(filter2b)
	print(settings.spotFilters)
	
	# Configure tracker - We want to allow merges and fusions
	settings.trackerFactory = SparseLAPTrackerFactory()
	settings.trackerSettings = LAPUtils.getDefaultLAPSettingsMap() # almost good enough

	##adapted from https://forum.image.sc/t/trackmate-scripting-automatically-exporting-spots-in-tracks-links-in-tracks-tracks-statistics-and-branching-analysis-to-csv/6256
	#linking settings
	settings.trackerSettings['LINKING_MAX_DISTANCE'] = LINKING_MAX_DISTANCE
	if LINKING_FEATURE_PENALTIES == True:
		settings.trackerSettings['LINKING_FEATURE_PENALTIES'] = {LINKING_FEATURE_PENALTIES_TYPE : LINKING_FEATURE_PENALTIES_VALUE}
	else:
		settings.trackerSettings['LINKING_FEATURE_PENALTIES'] = {}
		
	#gap closing settings
	settings.trackerSettings['ALLOW_GAP_CLOSING'] = ALLOW_GAP_CLOSING
	if ALLOW_GAP_CLOSING == True:
		settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = GAP_CLOSING_MAX_DISTANCE
		settings.trackerSettings['MAX_FRAME_GAP'] = MAX_FRAME_GAP
		if GAP_CLOSING_FEATURE_PENALTIES == True:
			settings.trackerSettings['GAP_CLOSING_FEATURE_PENALTIES'] = {GAP_CLOSING_FEATURE_PENALTIES_TYPE : GAP_CLOSING_FEATURE_PENALTIES_VALUE}
		else:
			settings.trackerSettings['GAP_CLOSING_FEATURE_PENALTIES'] = {}
	
	#splitting settings
	settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = ALLOW_TRACK_SPLITTING
	if ALLOW_TRACK_SPLITTING == True:
		settings.trackerSettings['SPLITTING_MAX_DISTANCE'] = SPLITTING_MAX_DISTANCE
		if SPLITTING_FEATURE_PENALTIES == True:
			settings.trackerSettings['SPLITTING_FEATURE_PENALTIES'] = {SPLITTING_FEATURE_PENALTIES_TYPE : SPLITTING_FEATURE_PENALTIES_VALUE}
		else:
			settings.trackerSettings['SPLITTING_FEATURE_PENALTIES'] = {}
	
	#merging settings
	settings.trackerSettings['ALLOW_TRACK_MERGING'] = ALLOW_TRACK_MERGING
	if ALLOW_TRACK_MERGING == True:
		settings.trackerSettings['MERGING_MAX_DISTANCE'] = MERGING_MAX_DISTANCE
		if MERGING_FEATURE_PENALTIES == True:
			settings.trackerSettings['MERGING_FEATURE_PENALTIES'] = {MERGING_FEATURE_PENALTIES_TYPE : MERGING_FEATURE_PENALTIES_VALUE}
		else:
			settings.trackerSettings['MERGING_FEATURE_PENALTIES'] = {}
	
	print(settings.trackerSettings)
	    
	# Configure track analyzers - Later on we want to filter out tracks 
	# based on their displacement, so we need to state that we want 
	# track displacement to be calculated. By default, out of the GUI, 
	# not features are calculated. 
	    
	# The displacement feature is provided by the TrackDurationAnalyzer.
	    
	settings.addTrackAnalyzer(TrackDurationAnalyzer())
	settings.addTrackAnalyzer(TrackSpotQualityFeatureAnalyzer())
	    
	# Configure track filters - We want to get rid of the two immobile spots at 
	# the bottom right of the image. Track displacement must be above 10 pixels.
	    
	filter3 = FeatureFilter('TRACK_DISPLACEMENT', TRACK_DISPLACEMENT, True)
	filter4 = FeatureFilter('TRACK_START', TRACK_START, False)
	#filter5 = FeatureFilter('TRACK_STOP', float(imp.getStack().getSize())-1.1, True)
	
	
	settings.addTrackFilter(filter3)
	settings.addTrackFilter(filter4)
	#settings.addTrackFilter(filter5)    
	    
	#-------------------
	# Instantiate plugin
	#-------------------
	    
	trackmate = TrackMate(model, settings)
	       
	#--------
	# Process
	#--------
	    
	ok = trackmate.checkInput()
	if not ok:
	    sys.exit(str(trackmate.getErrorMessage()))
	    
	ok = trackmate.process()
	
#	if not ok:
	    #sys.exit(str(trackmate.getErrorMessage()))
	    
	       
	#----------------
	# Display results
	#----------------
	
	#Set output folder and filename and create output folder
	well_folder = os.path.join(folder_w,filename)	
	output_folder = os.path.join(well_folder,"Tracking")	
	create_folder(output_folder)
	xml_file_name = filename + "_" + correction +"_trackmate_analysis.xml"
	folder_filename_xml= os.path.join(output_folder,xml_file_name)
	 
	

	#ExportTracksToXML.export(model, settings, File(folder_filename_xml))
	outfile = TmXmlWriter(File(folder_filename_xml))
	outfile.appendSettings(settings)
	outfile.appendModel(model)
	outfile.writeToFile()
	    
	# Echo results with the logger we set at start:
	#model.getLogger().log(str(model))
	


	#create araray of timepoint length with filled 0
	cell_counts = zerolistmaker(imp.getStack().getSize())
	if ok:
		for id in model.getTrackModel().trackIDs(True):
	   	    # Fetch the track feature from the feature model.
		    track = model.getTrackModel().trackSpots(id)
		    for spot in track:
		        # Fetch spot features directly from spot. 
		        t=spot.getFeature('FRAME')
		        print(t)
		        cell_counts[int(t)] = cell_counts[int(t)] + 1
	else:
		print("No spots detected!")        

	
	if HEADLESS==False:
		selectionModel = SelectionModel(model)
		displayer =  HyperStackDisplayer(model, selectionModel, imp)
		displayer.render()
		displayer.refresh()
	del imp
	return(cell_counts + [len(model.getTrackModel().trackIDs(True))])


def find_folders(inpt_folder, correction):
	with open(inpt_folder+'Summary_'+correction+'.csv', 'wb') as csvfile:
		spamwriter = csv.writer(csvfile, delimiter=' ',quotechar='|', quoting=csv.QUOTE_MINIMAL)
		
		#get list of folders and open folder one after the other
		for idx,i in enumerate(os.listdir(inpt_folder)):
			if os.path.isdir(os.path.join(inpt_folder, i)):
				comp_img,timepoints = open_images(os.path.join(inpt_folder, i), correction)
				cell_counts = track_cells(inpt_folder,i,comp_img,correction)
				
				if idx == 0:
					spamwriter.writerow(['well']+["timepoint_"+str(j) for j in range(timepoints)]+['ntracks'])
				spamwriter.writerow([i]+cell_counts)


def getImageStack(imp):
	## taken from https://forum.image.sc/t/run-fiji-python-script-with-parameters-on-windows/6162/9
	# get the stacks
	try:
		stack = imp.getStack() # get the stack within the ImagePlus
		nslices = stack.getSize() # get the number of slices
	except:
		stack = imp.getProcessor()
		nslices = 1
		print 'Execption with stack'

	print 'Number of slices: ', nslices

	return stack, nslices



def open_images(in_folder, correction):
	folder_path = os.path.join(in_folder,correction)

	if os.listdir(folder_path) == 1:
		sys.exit("More than one file in input folder!!")

	for i in os.listdir(folder_path):
		file_path = os.path.join(folder_path,i)	
		if os.path.isfile(file_path) and i.endswith(".tif"):
			print(i)
			cur_img_red = IJ.openImage(file_path)
			nslices_red = cur_img_red.getStack().getSize()
			IJ.run(cur_img_red,"Properties...", "channels=1 slices=1 frames="+ str(nslices_red) + " unit=pixel pixel_width=1.0000 pixel_height=1.0000 voxel_depth=1.0000");
	

	return(cur_img_red, nslices_red)



find_folders(folder, correction_type)

print("Done")

