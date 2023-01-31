from my_exception import *
from locate import locate_opening
from file_io import write_concat
from runcmd import *
import cv2
import os
import random
import string
import shutil
import logger
import time

VERSION = 'v1.0.0'
SOURCE_PATH = 'source/'
TMP_PATH = 'tmp/'
cut_dict = {
    "混血新版OP":SOURCE_PATH + 'cut_B_new.ts',
    "混血旧版OP":SOURCE_PATH + 'cut_B_old.ts'
}

# 帧数转时间（HH:MM:ss.ms）
def time_format(frame,fps):
    time = frame/fps
    if(time < 60):
        return "00:00:%.3f" %time
    elif(time < 60*60):
        min = int(time//60)
        sec = time-(time//60)*60
        return "00:{min:d}:{sec:.3f}".format(min=min,sec=sec)
    else:
        hour = int(time//3600)
        time = time-(time//3600)*3600
        min = int(time//60)
        sec = time-(time//60)*60
        return "{hour:d}:{min:d}:{sec:.3f}".format(hour=hour,min=min,sec=sec)

def auto_op_replace(video_input_path, video_output_path, op_type, diff_threshold, pre_threshold, start_offset, end_offset, debug_mod, std_out):
    logger.new_log()
    logger.info("==================================\n")
    logger.info("Automatic Opening Replacement Tool {}".format(VERSION))
    logger.info(time.strftime("%a %b %d %H:%M:%S %Y\n"))
    logger.info("==================================\n")
    logger.info('Locating opening of the video "{}"...'.format(video_input_path))
    # 存在性检查
    if(not os.path.exists(video_input_path)):
        raise FileExistsError
        
    # 原文件名持久化
    filename_old = os.path.basename(video_input_path)
    
    try:
        # 路径去中文化
        filename_new = ''.join(random.sample(string.ascii_letters + string.digits,10))
        new_path = os.path.dirname(video_input_path) + os.path.sep + filename_new + os.path.splitext(video_input_path)[-1]
        os.rename(video_input_path,new_path)
        video_input_path = new_path

        # 获取视频帧率帧数信息
        info = cv2.VideoCapture(video_input_path)
        fps = info.get(cv2.CAP_PROP_FPS)
        frame_total = info.get(cv2.CAP_PROP_FRAME_COUNT)
        info.release()

        # 定位OP头尾帧
        start_frame, end_frame = locate_opening(
            video_input_path = video_input_path,
            op_type = op_type,
            diff_threshold = diff_threshold,
            pre_threshold = pre_threshold,
            start_offset = start_offset,
            end_offset = end_offset,
            debug_mod = debug_mod,
            std_out = std_out
        )
        
        # 视频剪切拼接 CutA-CutB-CutC
        if(start_frame > 1):
            runcmd("ffmpeg.exe -y -ss 00:00:00 -t {during:s} -accurate_seek -i \"{input:s}\" -codec copy -avoid_negative_ts 1 {output:s}".format(
                during = time_format(start_frame,fps),
                input = video_input_path,
                output = TMP_PATH + "cut_A.mp4"
            ))
            runcmd("ffmpeg.exe -y -i {TMP_PATH:s}cut_A.mp4 -c copy -bsf:v h264_mp4toannexb -f mpegts {TMP_PATH:s}cut_A.ts".format(
                TMP_PATH = TMP_PATH
            ))

        if(end_frame < frame_total):
            runcmd("ffmpeg.exe -y -ss {start:s} -t {during:s} -accurate_seek -i \"{input:s}\" -codec copy -avoid_negative_ts 1 {output:s}".format(
                start = time_format(end_frame,fps),
                during = time_format(frame_total,fps),
                input = video_input_path,
                output = TMP_PATH + "cut_C.mp4"
            ))
            runcmd("ffmpeg.exe -y -i {TMP_PATH:s}cut_C.mp4 -c copy -bsf:v h264_mp4toannexb -f mpegts {TMP_PATH:s}cut_C.ts" .format(
                TMP_PATH = TMP_PATH
            ))

        write_concat(TMP_PATH + "concat.txt",list = [
            "file 'cut_A.ts'\n" if (start_frame > 1) else '',
            "file '../{cutB_path}'\n".format(cutB_path = cut_dict[op_type]),
            "file 'cut_C.ts'" if (end_frame < frame_total) else ''
        ])

        runcmd("ffmpeg.exe -y -f concat -safe 0 -i {TMP_PATH:s}concat.txt -c copy \"{output:s}\"".format(
            TMP_PATH = TMP_PATH,
            output = video_output_path
        ))

        if(not os.path.exists(video_output_path)):
            logger.error('Video synthesis failed!')
            raise ConcatExcption
        else:
            logger.success('The Opening has been replaced!')

    except LocateException:
        logger.error("No complete opening founded!")
        raise LocateException
    
    finally:
        # 恢复文件名
        os.rename(video_input_path,os.path.dirname(video_input_path) + os.path.sep + filename_old)
        
        # 清空临时文件
        if(not debug_mod):
            shutil.rmtree(TMP_PATH)
            os.mkdir(TMP_PATH)