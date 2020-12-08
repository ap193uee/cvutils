import multiprocessing 
import time
import logging 
from . import Camera_Base
from . import Camera_types
import cv2
import requests
from requests.auth import HTTPBasicAuth

def get_camera_config(camera_id, config,embedded=False):
    Veda_auth = HTTPBasicAuth(config['VedaUser'], config['VedaPassword'])
    url = "{}/{}/cameras/{}".format(config['ServerUrl'], config['API_VERSION'],str(camera_id))
    if embedded==True:
        querystring = {"embedded":"{\"behaviourTypes.behaviourId\":1}"}
    else:
        querystring ={}
    response = requests.request("GET", url, auth=Veda_auth,params=querystring)
    logger.debug("%s \n Response: %s", url, response)
    status = True
    return(response.json())


logger = logging.getLogger('CAM_Kernel')
class CAM_KERNEL(multiprocessing.Process): 
	def __init__(self, config): 
		Configuration = config
		username = Configuration.get('username', None)
		password = Configuration.get('password', None)
		if username and password and(Configuration['url'].find('@')==-1):
			url=Configuration['url'][0:7]+username+':'+password+'@'+Configuration['url'][7:]
			Configuration['url']=url
		logger.info("URL : ".format(Configuration["url"]))
		logger.debug("Initialisation started...")
		multiprocessing.Process.__init__(self) 
		self.exit = multiprocessing.Event()
		logger.debug(Configuration['url'])
		self.Name = Configuration["name"]
		self.Camera = None
		self.Configuration = Configuration
		self.run()
		logger.debug("Initialisation Finished.")

	def run(self):
		self.Camera = Camera_types.initialize_cam(self.Name, self.Configuration)
		if not self.Camera:
			logger.error("Failed to initialize CAM - {}. Raising request to shutdown.".format(self.Name))
			self.shutdown()

	def isOpened(self):
		return not self.exit.is_set()

	def read(self):
		if not self.exit.is_set():
			self.Camera.update_buffers()
			img = self.Camera.get_buffer_image(image_number=0)
			if img is None:
				return False, img
			else:
				return True, img
		else:
			return False, None

	def shutdown(self): 
		logger.debug(self.Name + " shutdown initiated.") 
		self.exit.set()

if __name__ == "__main__":

	user_config = {
		"VedaUser":"",
		"VedaPassword":"",
		"ServerUrl":"https://api.staging.vedalabs.in",
		"API_VERSION":"v1/rest"
	}
	config = get_camera_config("5faa50b309e7f79f972eb43c", user_config)
	cam = CAM_KERNEL(config)
	while cam.isOpened():
		ret, frame = cam.read()
		if ret:
			cv2.imshow("frame", frame)
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break

	cv2.destroyAllWindows()
	cam.shutdown()
