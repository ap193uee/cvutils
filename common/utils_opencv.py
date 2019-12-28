import cv2
import numpy as np
from threading import Thread

from PIL import Image
try:
   from queue import Queue
except ImportError:
    from Queue import Queue
    
cv2_version = cv2.__version__.split('.')[0]
FACE_PAD = 50

class VideoStream(object):
    def __init__(self, url, queueSize=4):
        self.stream = cv2.VideoCapture(url)
        if cv2_version == '3':
            self.stream.set(cv2.CAP_PROP_BUFFERSIZE,3)
        self.stopped = False
        self.frameBuffer = Queue(maxsize=queueSize)

    def start(self):
        # start a thread to read frames from the file video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely
        while self.stream.isOpened():
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return

            # otherwise, ensure the queue has room in it
            if not self.frameBuffer.full():
                (grabbed, frame) = self.stream.read()
                if not grabbed:
                    self.stop()
                    return
                # add the frame to the queue
                self.frameBuffer.put(frame)

    def read(self):
        # return next frame in the queue
        return self.frameBuffer.get()

    def more(self):
        # return True if there are still frames in the queue
        return self.frameBuffer.qsize() > 0

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

def showImage(img, window = 'Image'):
    """ Shows the image in a resizeable window"""
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.imshow(window,  img)

def resizeImg(img, size, keepAspect = False, padding = False):
    """ Resize the image to given size.
    img         -- input source image
    size        -- (w,h) of desired resized image
    keepAspect  -- to preserve aspect ratio during resize 
    padding     -- to add black padding when target aspect is different 
    """
    dtype = img.dtype
    outW, outH = size

    if len(img.shape)>2:
        h, w, d = img.shape[:3]
        if padding:
            outimg = np.zeros((outH, outW, d), dtype=dtype)
    else:
        h, w = img.shape[:2]
        if padding:
            outimg = np.zeros((outH, outW), dtype=dtype)

    if keepAspect:
        aspect = float(w)/h
        if int(outH*aspect) < outW:   #output image is wider so limiting factor is height
            out = cv2.resize(img, (int(outH*aspect), outH))
            if padding:
                outimg[:, (outW-int(outH*aspect))/2:(outW+int(outH*aspect))/2, ] = out
                out = outimg
        else:
            out = cv2.resize(img, (outW, int(outW/aspect)))
            if padding:
                outimg[(outH-int(outW/aspect))/2:(outH+int(outW/aspect))/2, ] = out
                out = outimg
    else:
        out = cv2.resize(img, size)
    return out

def subImage(img, bbox, padding_type = "50_pixel", padding=FACE_PAD):
    if  padding_type == "50_pixel":
        upper_cut = [min(img.shape[0], int(bbox['bottomright']['y']) + padding), min(img.shape[1], int(bbox['bottomright']['x']) + padding)]
        lower_cut = [max(int(bbox['topleft']['y']) - padding, 0), max(int(bbox['topleft']['x']) - padding, 0)]
        roi_color = img[lower_cut[0]:upper_cut[0], lower_cut[1]:upper_cut[1]]
        return roi_color

    if padding_type == "percentage":
        x1, y1 = bbox['topleft']['x'], bbox['topleft']['y']
        x2, y2 = bbox['bottomright']['x'], bbox['bottomright']['y']

        if padding_type == "percentage":
            offset = padding*(x2 + y2 - x1 - y1)/200
        else:
            offset = padding
        upper_cut = [min(imgcv.shape[0], y2 + offset),
                     min(imgcv.shape[1], x2 + offset)]
        lower_cut = [max(y1 - offset, 0),
                     max(x1 - offset, 0)]
        sub_img = imgcv[lower_cut[0]:upper_cut[0], lower_cut[1]:upper_cut[1]]
        return sub_img

    if padding_type == "coral":
        x1, y1 = bbox['topleft']['x'], bbox['topleft']['y']
        x2, y2 = bbox['bottomright']['x'], bbox['bottomright']['y']
        width = x2 - x1
        height = y2 - y1
        tol = 15
        up_down = 5
        diff = height-width

        if(diff > 0):
            if not diff % 2:  # symmetric
                y1 = y1-tol-up_down if (y1-tol-up_down) >= 0 else 0
                y2 = y2+tol-up_down if (y2+tol-up_down) < img.shape[0] else img.shape[0]-1
                x1 = x1-tol-int(diff/2) if (x1-tol-int(diff/2)) >=0 else 0
                x2 = x2+tol+int((diff+1)/2) if (x2+tol+int((diff+1)/2)) < img.shape[1] else img.shape[1]-1
                tmp = img[y1:y2,x1:x2,:]
            else:
                y1 = y1-tol-up_down if (y1-tol-up_down) >= 0 else 0
                y2 = y2+tol-up_down if (y2+tol-up_down) < img.shape[0] else img.shape[0]-1
                x1 = x1-tol-int((diff-1)/2) if (x1-tol-int((diff-1)/2)) >=0 else 0
                x2 = x2+tol+int((diff+1)/2) if (x2+tol+int((diff+1)/2)) < img.shape[1] else img.shape[1]-1
                tmp = img[y1:y2,x1:x2,:]
        if(diff <= 0):
            if not diff % 2:  # symmetric
                y1 = y1-tol-int(diff/2)-up_down if (y1-tol-int(diff/2)-up_down) >= 0 else 0
                y2 = y2+tol+int(diff/2)-up_down if (y2+tol+int(diff/2)-up_down) < img.shape[0] else img.shape[0]-1
                x1 = x1-tol if (x1-tol) >= 0 else 0
                x2 = x2+tol if (x2+tol) < img.shape[1] else img.shape[1]-1
                tmp = img[y1:y2,x1:x2,:]
            else:
                y1 = y1-tol-int((diff-1)/2)-up_down if (y1-tol-int((diff-1)/2)-up_down) >=0 else 0
                y2 = y2+tol+int((diff+1)/2)-up_down if (y2+tol+int((diff+1)/2)-up_down) < img.shape[0] else img.shape[0]-1
                x1 = x1-tol if (x1-tol) >= 0 else 0
                x2 = x2+tol if (x2+tol) < img.shape[1] else img.shape[1]-1
                tmp = img[y1:y2,x1:x2,:]
        tmp = np.array(Image.fromarray(np.uint8(tmp)).resize((120, 120), Image.ANTIALIAS))

        return tmp

def rotateImg(img, angle, crop = False):
    """ Rotate an image counter-clockwise by given angle with or without cropping.
    img         -- input source image
    angle       -- angle in degrees to ratate the img to
    crop        -- to change/preserve the size while rotating
    """
    h, w = img.shape[:2]
    centre = (img.shape[1]/2, img.shape[0]/2)
    M = cv2.getRotationMatrix2D(centre, angle, 1.0)
    if crop:
        out = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR)
    else:
        rangle = np.deg2rad(angle)
        H = abs(h*np.cos(rangle) + w*np.sin(rangle))
        W = abs(w*np.cos(rangle) + h*np.sin(rangle))
        M[0,2] += (W-w)/2
        M[1,2] += (H-h)/2
        out = cv2.warpAffine(img, M, (int(W), int(H)))
    return out

def drawLabel(img, text, topleft, font=cv2.FONT_HERSHEY_SIMPLEX, size = 0.6, color=(0,255,0), thickness=2):
    # draw class text
    x, y = topleft
    yoff = -10 if y > 20 else 20   # text remains inside image
    if cv2_version == '2':
        cv2.putText(img, text, (x, y+yoff), font, size, color, thickness, cv2.CV_AA)
    else:
        cv2.putText(img, text, (x, y+yoff), font, size, color, thickness, cv2.LINE_AA)
    return img

def showImagesInDirectory(directory):
    """ Shows all the images in a directory and its sub-directories. """
    from os import walk, path
    for root, dirnames, filenames in walk(directory):
        for name in filenames:
            try:
                file_path = path.join(root, name)
                frame = cv2.imread(file_path, -1)
                print('Original Image Size:', frame.shape, name)
                showImage(frame)
            except Exception as e:
                print('Exception: ', e)
            key = 0xFF & cv2.waitKey(0)
            if key == 27:
                break
        if key == 27:
            break
    cv2.destroyAllWindows()

if __name__ == '__main__':
    import time
    # showImagesInDirectory('/home/aestaq/Pictures')
    cap = VideoStream('/home/aestaq/Videos/qb.mp4').start()
    time.sleep(1.0)
    while not cap.stopped:
        frame = cap.read()
        frame = resizeImg(frame, (400, 400), keepAspect=True, padding=True)
        showImage(frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
