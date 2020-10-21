import subprocess

import sys

def get_ids(res_ids):
#    print("here",res_ids)
    sid,vid,mid="","",""
    for res in res_ids:
        index = res.find('=')
        id=res[index+1:]
#        ids.append(id)
        if res.find('VENDOR')!= -1:
            vid=id
        elif res.find('SERIAL')!= -1:
            sid=id
        elif res.find('MODEL')!= -1:
            mid=id
    return mid,sid,vid

def find_usb_cam_path(**kwargs):
    
    # Get all the provided ids
    VENDOR_ID=kwargs.get('VENDOR_ID',None)
    MODEL_ID=kwargs.get('MODEL_ID',None)
    SERIAL_ID=kwargs.get('SERIAL_ID',None)
    print(VENDOR_ID,MODEL_ID,SERIAL_ID)
    match_pattern='VENDOR_ID\|MODEL_ID\|SERIAL_SHORT'
    
    # Loop through camera mount paths and find the matching ids
    for num in range (0,10):
        cam_path = '/dev/video'+str(num)
        try:
            ps = subprocess.Popen(['udevadm', 'info', '--query=all',cam_path], stdout=subprocess.PIPE)
            output = subprocess.check_output(('grep', match_pattern), stdin=ps.stdout)
            ps.wait()
            res=output.decode('utf-8').split('\n')
            mid,sid,vid=get_ids(res)
            print(mid,sid,vid)
            if SERIAL_ID is not None and sid==SERIAL_ID:
                print("cam path found", cam_path)
                return cam_path
            if MODEL_ID is not None and mid==MODEL_ID:
                print("cam path found", cam_path)
                return cam_path
            if VENDOR_ID is not None and vid==VENDOR_ID:
                print("cam path found", cam_path)
                return cam_path

        except Exception as e:
            print(e)
    print("no cam path found")
    return None
            
