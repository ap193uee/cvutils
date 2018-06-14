#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import cv2
import numpy as np

cv2_version = cv2.__version__.split('.')[0]


class VideoStream(object):
    def __init__(self, url, queueSize=4, mode='buffer'):
        from Queue import Queue
        self.stopped = False
        self.frameBuffer = Queue(maxsize=queueSize)
        self.mode = mode
        self.stream = cv2.VideoCapture(url)
        if cv2_version == '3':
            self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 3)

    def start(self):
        """ start a thread to read frames from the file video stream. """
        from threading import Thread
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        """ capture frame from stream and add it to queue in a loop until eos """
        while self.stream.isOpened():
            # if the thread stop indicator variable is set, stop capturing
            if self.stopped:
                return

            # otherwise, ensure the queue has room in it and add frame to it
            if not self.frameBuffer.full():
                (grabbed, frame) = self.stream.read()
                if not grabbed:
                    self.stop()
                    return
                self.frameBuffer.put(frame)

            # for stream mode, stash the last frame in the queue if queue is full
            if self.mode == 'stream' and self.frameBuffer.full():
                self.frameBuffer.get()

    def read(self):
        """ returns next frame in the queue. """
        return self.frameBuffer.get()

    def more(self):
        """ checks if there are still frames in the queue. """
        return self.frameBuffer.qsize() > 0

    def stop(self):
        """ Stops the videostream thread """
        self.stopped = True


def clock():
    return cv2.getTickCount() / cv2.getTickFrequency()


def showImage(imgcv, window='Image'):
    """ Shows the image in a resizeable window"""
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.imshow(window,  imgcv)


def resizeImg(imgcv, size, keepAspect=False, padding=False):
    """ Resize the input image to given size.
    imgcv       -- input source image
    size        -- (w,h) of desired resized image
    keepAspect  -- to preserve aspect ratio during resize
    padding     -- to add black padding when target aspect is different
    """
    dtype = imgcv.dtype
    outW, outH = size

    if keepAspect:
        h, w = imgcv.shape[:2]
        aspect = float(w)/h

        if padding:
            if len(imgcv.shape) > 2:
                d = imgcv.shape[2]
                outimg = np.zeros((outH, outW, d), dtype=dtype)
            else:
                outimg = np.zeros((outH, outW), dtype=dtype)

        # Check if output image is wider/taller to determine limiting factor
        if int(outH*aspect) < outW:  # wider
            out = cv2.resize(imgcv, (int(outH*aspect), outH))
            if padding:
                outimg[:, (outW-int(outH*aspect))/2:(outW+int(outH*aspect))/2, ] = out
                out = outimg
        else:
            out = cv2.resize(imgcv, (outW, int(outW/aspect)))
            if padding:
                outimg[(outH-int(outW/aspect))/2:(outH+int(outW/aspect))/2, ] = out
                out = outimg
    else:
        out = cv2.resize(imgcv, size)
    return out


def subImage(imgcv, bbox, padding=20, padding_type='percentage'):
    """ Extract sub image from given image with padding around
        imgcv   -- input source image
        bbox    -- bounding box of subimage to be cropped
        padding -- padding value of padding_type
        padding_type -- 'absolute' or 'percentage'
    """
    x1, y1 = bbox['topleft']['x'], bbox['topleft']['y']
    x2, y2 = bbox['bottomright']['x'], bbox['bottomright']['y']

    if padding_type == 'percentage':
        offset = padding*(x2 + y2 - x1 - y1)/200
    else:
        offset = padding
    upper_cut = [min(imgcv.shape[0], y2 + offset),
                 min(imgcv.shape[1], x2 + offset)]
    lower_cut = [max(y1 - offset, 0),
                 max(x1 - offset, 0)]
    sub_img = imgcv[lower_cut[0]:upper_cut[0], lower_cut[1]:upper_cut[1]]
    return sub_img


def rotateImg(imgcv, angle, crop=False):
    """ Rotate an image counter-clockwise by given angle with or without cropping.
        imgcv   -- input source image
        angle   -- angle in degrees to ratate the imgcv to
        crop    -- to change/preserve the size while rotating
    """
    h, w = imgcv.shape[:2]
    centre = (imgcv.shape[1]/2, imgcv.shape[0]/2)
    M = cv2.getRotationMatrix2D(centre, angle, 1.0)
    if crop:
        out = cv2.warpAffine(imgcv, M, (w, h), flags=cv2.INTER_LINEAR)
    else:
        rangle = np.deg2rad(angle)
        H = abs(h*np.cos(rangle) + w*np.sin(rangle))
        W = abs(w*np.cos(rangle) + h*np.sin(rangle))
        M[0, 2] += (W-w)/2
        M[1, 2] += (H-h)/2
        out = cv2.warpAffine(imgcv, M, (int(W), int(H)))
    return out


def detectBlur(imgcv, threshold=100.0):
    sharpness = cv2.Laplacian(imgcv, cv2.CV_64F).var()
    return sharpness < threshold, sharpness


def enhance(image, brightness=0.1, contrast=0.1):
    return cv2.addWeighted(image, 1 + contrast, image, 0, brightness*255)


def drawLabel(imgcv, text, topleft,
              font=cv2.FONT_HERSHEY_SIMPLEX, size=None,
              color=(0, 255, 0), thickness=None):
    """ Draws text at topleft location. """
    h, w = imgcv.shape[:2]
    x, y = topleft

    if not thickness:
        thickness = max(1, (h + w) // 500)
    if not size:
        size = max(0.001*h, 0.5)

    out = imgcv.copy()
    yoff = -10 if y > 20 else 20   # text remains inside image
    if cv2_version == '2':
        cv2.putText(out, text, (x, y+yoff), font, size, color, thickness, cv2.CV_AA)
    else:
        cv2.putText(out, text, (x, y+yoff), font, size, color, thickness, cv2.LINE_AA)
    return out


def drawObjects(imgcv, detections, tids=None, thickness=None):
    """
    Draws rectangle around detected detections.
    Arguments:
        imgcv    -- image in numpy array on which the rectangles are to be drawn
        detections -- list of detections in a format given in Oject Detection Class
        tids     -- tracking ids to show along class name
    Returns:
        out    -- image in numpy array format with drawn rectangles
    """
    h, w = imgcv.shape[:2]
    if not thickness:
        thickness = max(1, (h + w) // 500)
    if tids is None:
        tids = ['']*len(detections)

    out = imgcv.copy()
    for det, tid in zip(detections, tids):
        x1, y1 = det['box']['topleft']['x'], det['box']['topleft']['y']
        x2, y2 = det['box']['bottomright']['x'], det['box']['bottomright']['y']
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), thickness)

        text = "%s_%s" % (det['class'], tid)
        out = drawLabel(out, text, (x1, y1))
    return out


def showImagesInDirectory(directory):
    """ Shows all the images in a directory and its sub-directories. """
    from os import walk, path
    for root, dirnames, filenames in walk(directory):
        for name in filenames:
            try:
                file_path = path.join(root, name)
                frame = cv2.imread(file_path, -1)
                print('Image Name:%s Image Size:%s' % (name, frame.shape))
                showImage(frame)
            except Exception, e:
                print('Exception: %s' % e)
            key = 0xFF & cv2.waitKey(0)
            if key == 27:
                break
        if key == 27:
            break
    cv2.destroyAllWindows()


def toCvbox(detections):
    return [(det['box']['topleft']['x'], det['box']['topleft']['y'],
            det['box']['bottomright']['x']-det['box']['topleft']['x'],
            det['box']['bottomright']['y']-det['box']['topleft']['y'])
            for det in detections]


if __name__ == '__main__':
    import time
    # showImagesInDirectory('/home/aestaq/Pictures')
    cap = VideoStream(0).start()
    time.sleep(1.0)
    while not cap.stopped:
        frame = cap.read()
        # frame = resizeImg(frame, (400, 400), keepAspect=True, padding=True)
        frame = drawLabel(frame, 'Test', (10, 10))
        showImage(frame)
        showImage(enhance(frame, brightness=0.5, contrast=0), 'bright')
        showImage(enhance(frame, brightness=0.2, contrast=0.4), 'contrast')
        # showImage(subImage(frame, {'bottomright': {'x': 100, 'y': 100},
        #                            'topleft': {'x': 0, 'y': 0}}), window='subImage')
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
