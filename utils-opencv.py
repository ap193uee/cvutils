import cv2
import numpy as np

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

def showImage(img, window = 'Image'):
    """ Shows the image in a resizeable window"""
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.imshow(window,  img)

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

def rotateImg(img, angle, crop = False):
    """ Rotate an image counter-clockwise by given angle with or without cropping. """
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

if __name__ == '__main__':
    showImagesInDirectory('/home/aestaq/Pictures')
    # img = cv2.imread('C:\Users\Aesta\Pictures\Screenshots\Screenshot.png')
    # im = rotateImg(img, 45)
    # print img.shape, im.shape
    # showImage(img)
    # showImage(im, 'Rotated')
    # key = cv2.waitKey(0)