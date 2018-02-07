import cv2
import numpy as np
from threading import Thread
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

def resizeImg(img, size, keepAspect = False):
    """ Resize the image to given size.
    img         -- input source image
    size        -- (w,h) of desired resized image
    keepAspect  -- to preserve aspect ratio during resize 
    """
    h, w = img.shape[:2]
    if keepAspect:
        aspect = float(w)/h
        outW, outH = size
        if int(outH*aspect) < outW:   #output image is wider so limiting factor is height
            out = cv2.resize(img, (int(outH*aspect), outH))
        else:
            out = cv2.resize(img, (outW, int(outW/aspect)))
    else:
        out = cv2.resize(img, size)
    return out

def sub_image(img, bbox):
    upper_cut = [min(img.shape[0], bbox['bottomright']['y'] + FACE_PAD), min(img.shape[1], bbox['bottomright']['x'] + FACE_PAD)]
    lower_cut = [max(bbox['topleft']['y'] - FACE_PAD, 0), max(bbox['topleft']['x'] - FACE_PAD, 0)]
    roi_color = img[lower_cut[0]:upper_cut[0], lower_cut[1]:upper_cut[1]]
    return roi_color

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

def draw_label(img, text, topleft):
    # draw class text
    x, y = topleft
    yoff = -10 if y > 20 else 20   # text remains inside image
    if cv2_version == '2':
        cv2.putText(img, text, (x, y+yoff), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2, cv2.CV_AA)
    else:
        cv2.putText(img, text, (x, y+yoff), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2, cv2.LINE_AA)
    return img

def showImagesInDirectory(directory):
    """ Shows all the images in a directory and its sub-directories. """
    from os import walk, path
    for root, dirnames, filenames in walk(directory):
        for name in filenames:
            try:
                file_path = path.join(root, name)
                frame = cv2.imread(file_path, -1)
                print 'Original Image Size:', frame.shape, name
                showImage(frame)
            except Exception, e:
                print 'Exception: ', e
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
        showImage(frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break