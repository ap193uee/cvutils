import subprocess

import sys

def find_path(vendor_id=sys.argv[1]):
    for num in range (0,10):
        cam_path = '/dev/video'+str(num)
        try:
            ps = subprocess.Popen(['udevadm', 'info', '--query=all',cam_path], stdout=subprocess.PIPE)
            output = subprocess.check_output(('grep', 'VENDOR_ID'), stdin=ps.stdout)
            ps.wait()
            res=output.split('\n')[0]
            index = res.find('=')
            res=res[index+1:]
            print("res",res)
            if res == vendor_id:
                print("cam path found", cam_path)
                return cam_path
                
        except:
            pass
    print("no cam path found")
    return None
