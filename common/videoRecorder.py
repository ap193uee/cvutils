import logging
logger = logging.getLogger(__name__)
logger.info("Loaded " + __name__)
import cv2
from .files_cleanup import cleanup
import os
from datetime import datetime
import csv

class VideoWriter(object):
    def __init__(self, filename, fourcc, fps, frameSize=None,limit_fps=False, base_dir="",
    max_sizeMB =0, max_seconds=0, timestamp_filename=True, 
    cleanupDays=3, delete=True, annotations = False,annotations_header=None,annotations_extension='.csv'):
        
        self.videow = None
        if type(fourcc) ==str:
            self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        else:
            self.fourcc = fourcc
        self.fps = fps
        self.frameSize =frameSize
        self.annotations = annotations
        if self.annotations:
            self.annotations_header= annotations_header
            self.annotations_extension= annotations_extension
        self.limit_fps = limit_fps

        filename, file_extension = os.path.splitext(filename)
        self.filename = filename
        self.file_extension =file_extension
        self.max_sizeMB =max_sizeMB
        self.max_seconds = max_seconds
        self.cleanupDays = cleanupDays
        self.cleanup_delete = delete

        if timestamp_filename:
            self.filename_pattern = '%s-%s%s'%(self.filename, '{}', self.file_extension)
            if self.annotations:
                self.filename_pattern_annotations = '%s-%s%s'%(self.filename, '{}', self.annotations_extension)
            self.cleanup_pattern = '.*%s-%s%s'%(self.filename, '.*', self.file_extension)
        else:
            self.filename_pattern = '%s%s'%(self.filename, self.file_extension)
            if self.annotations:
                self.filename_pattern_annotations = '%s-%s'%(self.filename, self.annotations_extension)
            self.cleanup_pattern = '.*%s%s'%(self.filename, self.file_extension)
        
        if base_dir:
            self.filename_pattern = os.path.join(base_dir, self.filename_pattern)
            if self.annotations:
                self.filename_pattern_annotations = os.path.join(base_dir,self.filename_pattern_annotations)
            self.base_dir = base_dir
        else:
            self.base_dir = os.path.dirname(self.filename)

               
    def clock(self):
        return cv2.getTickCount() / cv2.getTickFrequency()

    def writeAnnotationHeader(self):
        with open(self.aname,'a') as file :
            writer = csv.writer(file)
            writer.writerow(self.annotations_header)

    def writeAnnotations(self,annotations):
        with open(self.aname,'a') as file :
            writer = csv.writer(file)
            for annotation in annotations:
                annotation.insert(0,str(self.current_framecount))
                writer.writerow(annotation)
                
    def write(self, imgcv, annotations = None):
        ### initilize video writer object
        new_video = False
        if self.videow is None:
            
            # Cleanup old files to recover disk space
            cleanup(self.cleanupDays, path=self.base_dir, pattern=self.cleanup_pattern, delete=self.cleanup_delete)
            # Start new recording
            datestr = datetime.now().strftime("%d-%m-%y-%H%M%S")
            self.vname = self.filename_pattern.format(datestr)
            if self.annotations:
                self.aname=self.filename_pattern_annotations.format(datestr)
                logger.info('Annotations file created - %s', self.aname)
                self.writeAnnotationHeader()
            self.videow = cv2.VideoWriter(self.vname, self.fourcc, int(self.fps), self.frameSize)
            logger.info('Video Saved - %s', self.vname)
            # Frame Count and fps calculation variable init
            self.current_framecount = 0
            self.timer = 0
            new_video = True
            self.last_time=self.clock()
            
        writing = False
        ### write frame with desired fps
        if self.timer == 0:
            if len(imgcv.shape) == 2:
                imgcv = cv2.cvtColor(imgcv, cv2.COLOR_GRAY2BGR)
            if self.annotations and annotations is not None:
                self.writeAnnotations(annotations)
            self.videow.write(imgcv)
            writing = True,
            self.current_framecount+=1
        if self.limit_fps:
            self.timer = self.clock() - self.last_time 
            if self.timer > 1.0/self.fps:
                self.timer = 0
                self.last_time=self.clock()

        if (self.max_sizeMB and os.path.getsize(self.vname)/1000000 > self.max_sizeMB):
            self.videow.release()
            self.videow = None
            logger.info('Video Release after %d MB - %s', self.max_sizeMB, self.vname) 
        elif self.max_seconds and self.current_framecount > self.max_seconds * self.fps:
            self.videow.release()
            self.videow = None
            logger.info('Video Release after %d Seconds - %s', self.max_seconds, self.vname)

        if new_video:
            return self.vname, self.current_framecount-1, writing
        else:
            return None, self.current_framecount-1, writing

    def release(self):
        ret = self.videow.release()
        self.videow = None
        
        return ret