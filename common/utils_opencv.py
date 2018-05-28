import cv2
import numpy as np
from threading import Thread
from Queue import Queue

cv2_version = cv2.__version__.split('.')[0]
FACE_PAD = 50


class VideoStream(object):
    def __init__(self, url, queueSize=4, mode='buffer'):
        self.stream = cv2.VideoCapture(url)
        if cv2_version == '3':
            self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 3)
        self.stopped = False
        self.frameBuffer = Queue(maxsize=queueSize)
        self.mode = mode

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

            if self.mode == 'stream' and self.frameBuffer.full():
                self.frameBuffer.get()

    def read(self):
        # return next frame in the queue
        return self.frameBuffer.get()

    def more(self):
        # return True if there are still frames in the queue
        return self.frameBuffer.qsize() > 0

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True


def showImage(img, window='Image'):
    """ Shows the image in a resizeable window"""
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.imshow(window,  img)


def resizeImg(img, size, keepAspect=False, padding=False):
    """ Resize the image to given size.
    img         -- input source image
    size        -- (w,h) of desired resized image
    keepAspect  -- to preserve aspect ratio during resize
    padding     -- to add black padding when target aspect is different
    """
    dtype = img.dtype
    outW, outH = size

    if len(img.shape) > 2:
        h, w, d = img.shape[:3]
        if padding:
            outimg = np.zeros((outH, outW, d), dtype=dtype)
    else:
        h, w = img.shape[:2]
        if padding:
            outimg = np.zeros((outH, outW), dtype=dtype)

    if keepAspect:
        aspect = float(w)/h
        if int(outH*aspect) < outW:   # output image is wider so limiting factor is height
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


def subImage(img, bbox, padding=FACE_PAD):
    upper_cut = [min(img.shape[0], bbox['bottomright']['y'] + padding),
                 min(img.shape[1], bbox['bottomright']['x'] + padding)]
    lower_cut = [max(bbox['topleft']['y'] - padding, 0),
                 max(bbox['topleft']['x'] - padding, 0)]
    roi_color = img[lower_cut[0]:upper_cut[0], lower_cut[1]:upper_cut[1]]
    return roi_color


def rotateImg(img, angle, crop=False):
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
        M[0, 2] += (W-w)/2
        M[1, 2] += (H-h)/2
        out = cv2.warpAffine(img, M, (int(W), int(H)))
    return out


def drawLabel(img, text, topleft,
              font=cv2.FONT_HERSHEY_SIMPLEX, size=0.6, color=(0, 255, 0), thickness=2):
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
    cap = VideoStream(0).start()
    time.sleep(1.0)
    while not cap.stopped:
        frame = cap.read()
        frame = resizeImg(frame, (400, 400), keepAspect=True, padding=True)
        frame = drawLabel(frame, 'TEST', (10, 10))
        showImage(frame)
        showImage(subImage(frame, {'bottomright': {'x': 100, 'y': 100},
                                   'topleft': {'x': 0, 'y': 0}}), window='subImage')
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
