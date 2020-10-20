# README #

Common library with python code snippets used frequently.

### Libraries Implemented ###

* OpenCV
* Python multiprocessing

### Installation ###

```sh
pip install --user git+https://gitlab.com/_macherlabs/visonlibs/common.git
```

### Video Recorder annotation usage example###
```sh
video_writer = VideoWriter(filename='pc-rgb.'+'.avi',
                            fourcc = 'XVID',
                            fps = 1,
                            frameSize = (640,480),
                            base_dir = '/LFS/depth_vids',
                            max_sizeMB = 2,
                            cleanupDays = 3,
                            annotations= True,
                            annotations_header=['frame_number','xmin','ymin','xmax','ymax'])
 img=np.ones((640,480)).astype('uint8')
 annotation = ["10","20","30","40"]
 video_writer.write(img,annotation)
 
```
### USB cam_finder usage###
```sh
cam_mount_path=find_usb_cam_path('VENDOR_ID'='1234','MODEL_ID'='12',SERIAL_ID='123')
```
