import cv2
import numpy as np

cv2_version = cv2.__version__.split('.')[0]

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

def draw_bbox(img, detections, typ='json'):
    """ Draws bounding boxes of detection on given image """
    for obj in detections:
        if typ == 'json':
            x1, y1, x2, y2 = obj['box']['topleft']['x'], obj['box']['topleft']['y'], obj['box']['bottomright']['x'], obj['box']['bottomright']['y']
        elif typ == 'opencv':
            x1, y1, x2, y2 = obj[0], obj[1], obj[0]+obj[2], obj[1]+obj[3]
        cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)
    return img

def draw_label(img, loc):
    # draw class text
    yoff = -10 if y1 > 20 else 20   # text remains inside image
    if cv2_version == '2':
        cv2.putText(img, obj['class'], (x1, y1+yoff), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2, cv2.CV_AA)
    else:
        cv2.putText(img, obj['class'], (x1, y1+yoff), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2, cv2.LINE_AA)
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
    showImagesInDirectory('/home/aestaq/Pictures')
    # img = cv2.imread('C:\Users\Aesta\Pictures\Screenshots\Screenshot.png')
    # im = rotateImg(img, 45)
    # print img.shape, im.shape
    # showImage(img)
    # showImage(im, 'Rotated')
    # key = cv2.waitKey(0)