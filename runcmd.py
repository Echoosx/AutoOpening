import subprocess
import logger

def runcmd(command):
    ret = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8")
    
    while True:
        if(ret.poll() is None):
            logger.info('')
            for line in ret.stdout.readlines():
                logger.info(line.strip())
            for line in ret.stderr.readlines():
                logger.info(line.strip())

        elif(ret.poll() == 0):
            logger.success(command)
            break
        
        else:
            logger.warning(command)
            break