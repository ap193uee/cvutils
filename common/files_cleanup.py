import os
import sys
import time
import re
import logging
logger = logging.getLogger(__name__)
 
#----------------------------------------------------------------------
def remove(path,delete=True):
    """
    Remove the file or directory
    """
    if os.path.isdir(path):
        try:
            if delete: os.rmdir(path)
            logger.info("Removed folder: %s" % path)
        except OSError:
             logger.error("Unable to remove folder: %s" % path)
    else:
        try:
            if os.path.exists(path):
                logger.info("Removed file: %s" % path)
                if delete: os.remove(path)
        except OSError:
            logger.error("Unable to remove file: %s" % path)

def cleanup(number_of_days, path, pattern=".*", delete=True):
    """
    Removes files from the passed in path that are older than or equal 
    to the number_of_days
    """
    logger.info("Running cleanup with params: days:{},path: {}, pattern: {},delete:{}".format(number_of_days, path, pattern, delete))
    time_in_secs = time.time() - (number_of_days * 24 * 60 * 60)
    for root, dirs, files in os.walk(path, topdown=False):
        for filename in files:
            full_path = os.path.join(root, filename)
            if re.match(pattern, full_path):
                stat = os.stat(full_path)
                if stat.st_mtime <= time_in_secs:
                    remove(full_path, delete=delete)
                    
        if not os.listdir(root) and re.match(pattern, root):
            remove(root, delete=delete)

if __name__ == "__main__":
    ##################################
    # Usage: $ python files_cleanup.py 0 .. '^.*.log$'
    # Specify  ^ and $ for exact match otherwise lots of unintended files might be matched and deleted
    #
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(filename='output.log',format=FORMAT, level=logging.INFO)
    days, path,pattern = int(sys.argv[1]), sys.argv[2] , sys.argv[3]
    logger = logging.getLogger(__name__)
    print(days, path,pattern)
    cleanup(days, path, pattern,False)