import logging 
import cv2			#opencv2 library 
import time			#time module
import operator		#operator module for map function used for math operations on lists
import numpy as np
from os.path import join

logger = logging.getLogger('CAM_Instances')

class CAMERA_BUFFER(object):
	def __init__(self, Type='default', Max_Count=0, FPS=10):	# TODO: Route all default directly to cv2.videocapture
		self.Frame_buffer 	= []							# TODO: numpy array 
		self.Type 		= Type
		self.Max_Count	= Max_Count	
		#self.Frame_width 	= 0	# how to update these if required?
		#self.Frame_height 	= 0
		self.FPS 		= FPS

	def count(self):
		return len(self.Frame_buffer)
	
	def frame_width(self):
		if self.count():
			return len(self.Frame_buffer[0])
		else:
			return 0
	
	def frame_height(self):
		if self.frame_width():
			return len(self.Frame_buffer[0][0])
		else:
			return 0



class CAMERA(object):
	color = ('b','g','r')

	def __init__(self,Name , Type, Configuration):
		self.Name = Name
		self.Type =	Type
		self.fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
		self.configuration = Configuration
		self.isHealthy	= True
		default_camera_buffer = CAMERA_BUFFER(Max_Count=60)
		self.Buffer_Dict = {default_camera_buffer.Type:default_camera_buffer}	# Type : Buffer

	def update_buffers(self): 
		logger.error("Referancing to base class method- No buffer available here")
		
	def update_configuration(self, configuration_number):
		logger.error("Referencing to base class method- No new configuration available")

	def cam_attributes(self,buffer_type='default'):	
		"""return frame width and height of a buffer"""
		if buffer_type in self.Buffer_Dict:
			width 	= self.Buffer_Dict[buffer_type].frame_width()
			height 	= self.Buffer_Dict[buffer_type].frame_height()
			return(height,width)
		else:
			return (0,0)

	def total_buffers(self):
		return len(self.Buffer_Dict)

	def get_buffer_image(self, buffer_type='default', image_number=0):
		if buffer_type not in  self.Buffer_Dict:
			buffer_type = None 

		if buffer_type:
			if image_number < len(self.Buffer_Dict[buffer_type].Frame_buffer): #If image number is less than total images in buffer
				return self.Buffer_Dict[buffer_type].Frame_buffer[image_number]
			else:
				logger.error("Image number is greater than total images in buffer!!")

		return None 

	def get_buffer_item(self, *args, **kwargs): 	# Alias of get_buffer_image as buffer also contain non-image data such as time.
		self.get_buffer_item = self.get_buffer_image # change function refence so that every function call dont have two call overhead.
		return self.get_buffer_image(*args,**kwargs)

	def get_snapshot(self, buffer_type='default', image_number=0):
		self.update_buffers()
		return self.get_buffer_image(buffer_type, image_number)

	def save_image(self,image_name="image.jpg",image_number=0,buffer_type='default',tag=''):
		image = self.get_buffer_image(buffer_type=buffer_type, image_number=image_number).copy()
		image_name = join('logs',image_name)

		logger.debug("writing image %s from %s buffer and %s frame to disk",image_name, buffer_type, image_number)
		try :
			cv2.rectangle(image, (0,0), (280,50), (255,255,255), -1)
			cv2.putText(image,tag,(10,40), cv2.FONT_HERSHEY_SIMPLEX, 0.7,(0,0,255),3)
			ret = cv2.imwrite(image_name,image)
		except Exception as e:
			ret = False
			logger.error("Raised Exception %s",e)
		if not ret:
			logger.error("Failed to write image to disk")

	def save_video(self, video_name="video.avi",start_frame=0,end_frame=0,buffer_type='default',tag=''):
		if end_frame == 0: end_frame = self.Buffer_Dict[buffer_type].count() - 1
		video_name = join('logs',video_name)

		logger.debug("writing video %s from %s buffer  %s : %s frame to disk",video_name, buffer_type, start_frame, end_frame)
		videoW = cv2.VideoWriter(video_name, self.fourcc, self.Buffer_Dict[buffer_type].FPS , self.cam_attributes(buffer_type))
		return_val = True
		for i in range(end_frame,start_frame-1,-1): #reverse order: end_frame, end_frame-1,... ,start_frame
			try:
				image = self.Buffer_Dict[buffer_type].Frame_buffer[i].copy()
				if i - start_frame < 10:
					cv2.rectangle(image, (0,0), (280,50), (255,255,255), -1)
					cv2.putText(image,tag,(10,40), cv2.FONT_HERSHEY_SIMPLEX, 0.7,(0,0,255),3)
				videoW.write(image)	
			except Exception as e:
				logger.error("Exception during video-write : %s", e)
		videoW.release()
		#if not return_val:
		#	logger.error("Failed to write video %s to disk", video_name)

	def save_video_after_event(self,video_name="After_video.avi",frame_count=0,time=0,buffer_type='default',tag=''):
		if time:
			frame_count = time * self.Buffer_Dict[buffer_type].FPS
		logger.debug("Generating and saving after-event-video %s from %s buffer  %s  frame_count to disk",video_name, buffer_type, frame_count)
		for i in range(frame_count):
			self.update_buffers()

		self.save_video(video_name=video_name,start_frame=0,end_frame=frame_count-1,buffer_type=buffer_type,tag=tag)
	
		


