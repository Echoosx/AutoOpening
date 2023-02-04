from PyQt6.QtWidgets import QApplication
from my_exception import *
import subprocess
import logger
import global_var


def runcmd(command):
    logger.debug(command)
    if global_var.get_value('abort_flag'):
        raise UserAbortException
    # QApplication.processEvents()
    ret = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8")
    while True:
        if(ret.poll() is None):
            logger.stdout('')
            for line in ret.stdout.readlines():
                logger.stdout(line.strip())
            for line in ret.stderr.readlines():
                logger.stdout(line.strip())

        elif(ret.poll() == 0):
            logger.success(command)
            break
        
        else:
            logger.error(command)
            break