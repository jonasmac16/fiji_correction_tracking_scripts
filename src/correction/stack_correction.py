# @String(label="Please enter your input folder", description="Input folder", style="directory") FOLDER

###Loading ImageJ and pythn libraries
from ij import IJ
from ij import ImagePlus
from ij import VirtualStack
from ij import ImageStack
from ij.process import ImageConverter
import sys

import os
from ij.plugin import RGBStackMerge

sys.path.append(str(os.path.dirname(os.path.abspath(__file__))))
from correct_3d_script import run_3d_drift_correct

from ij.plugin import ChannelSplitter
from ij.gui import OvalRoi, Roi
from java.io import File
#from ij.macro import MacroRunner
from ij.io import FileSaver
import csv
from emblcmci import BleachCorrection_MH
from ij.plugin.filter import BackgroundSubtracter
from java. lang import ClassLoader
ClassLoader.getSystemClassLoader().loadClass('de.embl.cba.illuminationcorrection.basic.BaSiCCommand')
import de.embl.cba.illuminationcorrection.basic as basic


## Parsing commandline input about input folder
folder = FOLDER
###############################################

def run():
    print("Input folder:" + folder)
    find_folders(folder)
    
def create_folder(dirName):
	if not os.path.exists(dirName):
	    os.mkdir(dirName)
	    print("Directory " , dirName ,  " Created ")
	else:    
	    print("Directory " , dirName ,  " already exists")

def find_folders(inpt_folder):

	#get list of folders and open folder one after the other
	for idx,i in enumerate(os.listdir(inpt_folder)):
		if os.path.isdir(os.path.join(inpt_folder, i)):
			comp_img,timepoints = open_images(os.path.join(inpt_folder, i))
			corrected_img, corrected_img_bleach = pre_process_images(comp_img,timepoints)
			
			create_folder(os.path.join(inpt_folder, i, "Corrected"))
			file_name = i +"_Red_corrected.tif"
			folder_file = os.path.join(inpt_folder, i, "Corrected",file_name)
			IJ.save(corrected_img,folder_file)

			create_folder(os.path.join(inpt_folder, i, "Corrected_bleach"))
			file_name = i + "_Red_corrected_bleach.tif"
			folder_file = os.path.join(inpt_folder, i, "Corrected_bleach",file_name)
			IJ.save(corrected_img_bleach,folder_file)





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

def apply_rollingball(imp, rolling_ball, createBackground, lightBackground, useParaboloid, doPresmooth, correctCorners):
	## taken from https://forum.image.sc/t/run-fiji-python-script-with-parameters-on-windows/6162/9
	print 'Substracting Background - Radius:', rolling_ball
	# Create BackgroundSubtracter instance
	bs = BackgroundSubtracter()
	# get the stacks
	stack, nslices = getImageStack(imp)

	for index in range(1, nslices+1):
		ip = stack.getProcessor(index)
		# Run public method rollingBallBackground
		bs.rollingBallBackground(ip, rolling_ball, createBackground, lightBackground, useParaboloid, doPresmooth, correctCorners)

	return imp

def open_images(in_folder):
	#open Red folder
	for i in os.listdir(os.path.join(in_folder,"Red")):
		file_path = os.path.join(in_folder,"Red", i)
		 
		if os.path.isfile(file_path) and i.endswith(".tif"):
			print(i)
			cur_img_red = IJ.openImage(file_path)
			nslices_red = cur_img_red.getStack().getSize() # get the number slices in stack within the ImagePlus
			
	#open phase folder
	for i in os.listdir(os.path.join(in_folder,"Phase")):
		file_path = os.path.join(in_folder,"Phase", i)
		 
		if os.path.isfile(file_path) and i.endswith(".tif"):
			print(i)
			cur_img_phase = IJ.openImage(file_path)
			nslices_phase = cur_img_phase.getStack().getSize() # get the number slices in stack within the ImagePlus

		
	if nslices_red != nslices_phase:
		sys.exit("Red and phase channel have unequal number of images!")

	timepoints = nslices_red
	
	ImageConverter(cur_img_phase).convertToGray16()
	

	comp_stack_img = RGBStackMerge.mergeChannels([cur_img_red, None, None, cur_img_phase, None, None, None], True)
	

	return(comp_stack_img, timepoints)

def pre_process_images(image_input,timepoints):
	#correct drift
	IJ.run(image_input,"Properties...", "channels=2 slices=1 frames="+ str(timepoints) + " unit=pixel pixel_width=1.0000 pixel_height=1.0000 voxel_depth=1.0000");
	corrected_img = run_3d_drift_correct(image_input)

	#split channels
	red_corrected_img, phase_corrected_img = ChannelSplitter.split(corrected_img)
	
	#get image dimensions, set ROI remove part of flouresncent ring
	x_size=ImagePlus.getDimensions(red_corrected_img)[0]
	y_size=ImagePlus.getDimensions(red_corrected_img)[1]
	x_start = 0
	y_start = 0
	
	red_corrected_img.setRoi(OvalRoi(x_start,y_start,x_size,y_size))
		
	IJ.run(red_corrected_img, "Make Inverse", "")
	IJ.setForegroundColor(0,0,0)
	IJ.run(red_corrected_img, "Fill", "stack");
	red_corrected_img.killRoi()
	
	#correcting background
	IJ.run(red_corrected_img,"Properties...", "channels=1 slices="+ str(timepoints) + " frames=1 unit=pixel pixel_width=1.0000 pixel_height=1.0000 voxel_depth=1.0000");
	#red_corrected_background_img = apply_rollingball(red_corrected_img, 7.0, False, False,False, False, False)

	testset = basic.BaSiCSettings()
	
	testset.imp = red_corrected_img
	testset.myShadingEstimationChoice = "Estimate shading profiles"
	testset.myShadingModelChoice = "Estimate both flat-field and dark-field"
	testset.myParameterChoice = "Manual"
	testset.lambda_flat = 2.0
	testset.lambda_dark = 2.0
	testset.myDriftChoice = "Replace with zero"
	testset.myCorrectionChoice = "Compute shading and correct images"
		
	test = basic.BaSiC(testset)
	test.run()
	red_corrected_background_img =test.getCorrectedImage()
	
	#change properties back and perform bleach correction
	IJ.run(red_corrected_background_img,"Properties...", "channels=1 slices=1 frames="+ str(timepoints) + " unit=pixel pixel_width=1.0000 pixel_height=1.0000 voxel_depth=1.0000");
	red_corrected_background_img_dup =red_corrected_background_img.duplicate()
	corrected_bleach = BleachCorrection_MH(red_corrected_background_img)
	corrected_bleach.doCorrection()

	return(red_corrected_background_img_dup, red_corrected_background_img)



run()
