import logging 
import cv2			#opencv2 library 
import time			#time module
import operator		#operator module for map function used for math operations on lists
import Camera_Base
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "Behaviors"))
import numpy as np
import threading


logger = logging.getLogger('CAM_Instances')

CHECK_DVR_Priority = 90
Max_Trials = 1000

class SYNC_CAM(Camera_Base.CAMERA):
	def __init__(self, name , configuration):
		logger.debug("Creating object for SYNC cam-%s", name)
		self.cap = None 
		self.cameraType = configuration.get("cameraType","SYNC")
		self.FPS = configuration.get("params",{}).get("fps",0)
		self.source_FPS = configuration.get("params",{}).get("source_fps",0)
		super(SYNC_CAM,self).__init__(name, self.cameraType, configuration)

		for trial in range(Max_Trials):
			success = self._init_VideoCapture()
			self._report(trial,success,init_stage=True)
			if success:
				break
			else:
				time.sleep(10)

		self.SKIP = int(self.source_FPS/self.FPS) if self.source_FPS and self.FPS else 1

	def grab_skip_retrieve(self):
		Success = False
		Grab_Success = False

		for skip in range(self.SKIP)[::-1]: # value of skip is False for last element, ie for self.SKIP=4,skip = [True,True,True,False]
			Grab_Success = False
			for trial in range(Max_Trials): 

				if self.cap.isOpened():
					# Grab Frame
					try:
						Grab_Success = self.cap.grab()
					except Exception as e:
						logger.error("Exception in Cam-%s: grabbing frame : %s", self.Name, e)
						Grab_Success = False

					# Check for event and retrive frme based on skip criteria
					if Grab_Success:
						self._report(trial,Grab_Success)

						if not skip:
							ret2, im = self.cap.retrieve()
							if ret2:
								self.im = im
								self.frame_time = time.time()
								logger.debug("Cam-{}: Frame Time: {}".format(self.Name, self.frame_time))
								Success = True						
							else:
								logger.error("Error in Cam-%s: Decoder problem in retrieve", self.Name)
						break

				# Recovery Mechanism: if cam didn't worked or wasn't open for current trial
				if not Grab_Success:	
					self._init_VideoCapture()		
					self._report(trial,Grab_Success)
					time.sleep(10)
						
		return Success
	
	def _init_VideoCapture(self):
		link = self.configuration['url']
		try:
			print("making Videocapture object : ",link)
			self.cap = cv2.VideoCapture(link)
			self.source_FPS = self.configuration.get("params",{}).get("source_fps",self.cap.get(cv2.CAP_PROP_FPS))
		except Exception as e:
			print("Error making Videocapture object : %s ", e)
			return False

		return True

	def _report(self, trial, success, init_stage=False):
		state = "initiaze" if init_stage else "grab"
		if success:
			if trial > 11 or init_stage:
				print("Cam-{}: {} success, trial: {}".format(self.Name,state, trial))
		else:
			print("Error in Cam-{}: Failed to {}, trial: {}".format(self.Name, state, trial))					
			
			if trial%180==11:	
				print("Feed_Lost detected at Cam- {} Stats: {}".format(self.Name ,trial))
			if trial >= 600:
				sys.exit()

	def update_buffers(self): 
		while self.Buffer_Dict["default"].count() <= self.Buffer_Dict["default"].Max_Count :
			if not self.grab_skip_retrieve():
				logger.error("Failed to update buffer: %s", self.Name)
				continue

			self.Buffer_Dict["default"].Frame_buffer.insert(0,self.im)

		self.Buffer_Dict["default"].Frame_buffer.pop()

class ASYNC_CAM(SYNC_CAM):
	def __init__(self, name , configuration):
		logger.debug("Creating object for ASYNC cam-%s", name)
		super(ASYNC_CAM,self).__init__(name, configuration)

		self.camera_capture_thread_ref = None
		self.camera_capture_thread_Success = False
		self.camera_capture_thread_Image = None
		self.camera_capture_thread_frame_time = None
		self.camera_capture_thread_stop_event =  threading.Event()

	def camera_capture_thread(self):
		logger.debug("Started Cam-%s thread", self.Name)
		while not self.camera_capture_thread_stop_event.is_set():
			if self.cap.isOpened():
				try:
					retval, Image = self.cap.read()
					if retval:
						self.camera_capture_thread_Success, self.camera_capture_thread_Image = (retval, Image)	# TODO: use thread lock
						self.camera_capture_thread_frame_time = time.time()
					else:
						logger.warning("Failed in Cam-%s thread: grabbing frame", self.Name)
				except Exception as e:
					logger.error("Exception in Cam-%s thread: grabbing frame : %s", self.Name, e)
				time.sleep(0.01)
			else:
				self._init_VideoCapture()
		
		logger.debug("Stopped Cam-%s thread", self.Name)

	# override grab_skip_retrieve method of sync cam with async implementation
	def grab_skip_retrieve(self):
		Success = False
		time.sleep(self._async_sleep_time())
		for trial in range(Max_Trials): 
			# Check for event and retrive frme based on skip criteria
			if self.camera_capture_thread_Success:
				self.im = self.camera_capture_thread_Image.copy()
				self.frame_time = self.camera_capture_thread_frame_time
				logger.debug("Cam-{}: Frame Time: {}".format(self.Name, self.frame_time))

				Success = True											
				self.camera_capture_thread_Success = False 			#TODO : use thread lock

				self._report(trial,success=True)
				break

			#Recovery Mechanism: if cam didn't worked or wasn't open for current trial
			else:				
				if trial % 10 == 7: # On every 10th consecutive failure, re-initialise camera
					# reset camera thread: stop and cleanup
					logger.debug("Stopping Cam-%s thread", self.Name)
					self.camera_capture_thread_stop_event.set()
					self.camera_capture_thread_ref.join(timeout=10)
					if self.camera_capture_thread_ref.is_alive():
						logger.error("Could not stop Cam-%s thread. Proceeding to create new thread anyway. It can cause unexpected behaviours.", self.Name)	
					self.camera_capture_thread_ref = None
				
				if self.camera_capture_thread_ref is None or not self.camera_capture_thread_ref.is_alive(): 	#ckeck if thread have not been started or killed
					self.camera_capture_thread_stop_event.clear()
					# reinitialise camera
					self._init_VideoCapture()
					# start thread
					self.camera_capture_thread_ref = threading.Thread(target=self.camera_capture_thread)
					self.camera_capture_thread_ref.start()

				self._report(trial,success=False)
				if trial < 10:
					time.sleep(0.05)
				else:
					time.sleep(10)
			
		return Success

	def _async_sleep_time(self,now=None):
		try: 
			if self.FPS:
				if not now: now=time.time()
				last_time = self.frame_time
				elapsed_time = now-last_time
				wait_time = 1.0/self.FPS - elapsed_time
			else:
				wait_time = 0.1
		except AttributeError:
			wait_time = 0.1
		
		return wait_time if wait_time > 0 else 0.01


##########################################################################################################
##										Instantiating Function											##
##########################################################################################################

def initialize_cam(name, configuration):
	if configuration.get("cameraType","SYNC") == "ASYNC":
		return ASYNC_CAM(name ,configuration)
	else:
		return SYNC_CAM(name ,configuration)
