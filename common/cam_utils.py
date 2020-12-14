import logging
logger = logging.getLogger(__name__)
logger.info("Loaded " + __name__)

import cv2
import numpy as np
import urllib
import base64
import time

# RTSP based capture
class cap_rtsp():

    def __init__(self, config):
        
        self.config = config
        logger.info("URL : " + str(self.config["url"]))
        username = self.config.get('username', None)
        password = self.config.get('password', None)
        if username and password and(self.config['url'].find('@')==-1):
            url=self.config['url'][0:7]+username+':'+password+'@'+self.config['url'][7:]
            self.config['url']=url
        self.video = cv2.VideoCapture(self.config['url'])
        params = self.config.get('params',{})
        self.config['params']=params
        self.source_FPS = self.config['params'].get('source_fps', int(self.video.get(cv2.CAP_PROP_FPS)))
        print("fps of camera-{}".format(self.source_FPS))
        self.FPS = self.config['params'].get('fps', 5)
        self.SKIP = int(self.source_FPS/self.FPS) if self.source_FPS and self.FPS else 1
        self.lastFeedTime=None

    def set(self,attribute,value):
        self.video.set(attribute,value)

    def read(self):
        if (self.video.isOpened()):
            frame= self.run()
            if frame is None:
                return 0,None
            else:
                return 1,frame
        else:
            logger.info('camera capture object not opened for camera {} ,url{}'.format(self.config['name'],self.config['url']))
            return 0,None

    def reinitialize(self):
        self.video.release()
        self.video = cv2.VideoCapture(self.config['url'])

    def clear(self):
        self.config = None
        self.source_FPS = None
        self.FPS = None
        self.SKIP = None
        self.video.release()
        
    def release(self):
        self.clear()


    def run(self):
        if self.lastFeedTime is not None:
            timeTaken = time.time()-self.lastFeedTime
            fps=1.0/timeTaken
            #print("fps",fps)
            self.SKIP = min(int(self.source_FPS/fps)+1,self.source_FPS-5)
            #print("fps",fps,self.SKIP)
        for skip in range(self.SKIP)[::-1]:
            Grab_Success = False 
            try:
                Grab_Success = self.video.grab()
            except Exception as e:
                logger.info("Exception in Camera grabbing frame...")
                Grab_Success  =False

            if Grab_Success:
                if not skip:
                    # frame_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ret, frame = self.video.retrieve()
                    if ret==1 :
                        self.lastFeedTime=time.time()
                        return frame
            
        return None
        

## Over http protocol
class cap_http():

    def __init__(self,config):
        self.config = config
        url = self.config['url']
        logger.info("URL : " + url)

        username = self.config.get('username', '')
        password = self.config.get('password', '')

        userpass = '%s:%s' % (username, password)
        base64string=base64.b64encode(userpass.encode()).decode()
        request = urllib.request.Request(url)
        request.add_header("Authorization", "Basic %s" % base64string)


        try:   
            self.stream = urllib.request.urlopen(request)
        except Exception as e:
            logger.info("Cmaera Stream object was not created")
            logger.info(e)

        self.generator = self.gen()

    def read(self):
        return next(self.generator)    

    def gen(self):
        byytes = bytes()
        fail =0
        while True:
            try:
                byytes += self.stream.read(1024)
                a = byytes.find(b'\xff\xd8')
                b = byytes.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = byytes[a:b+2]
                    byytes = byytes[b+2:]
                    image = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.IMREAD_COLOR)
                    fail = 0
                    yield 1,image
            except Exception as e:
                logger.info(e)
                yield 0, None
    def reinitialize(self):
        pass

    def set(self,id,value):
        pass   

    def isOpened(self):
        return True
