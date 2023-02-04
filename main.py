from my_exception import *
from locate import locate_opening
from cv2concat import cv2clip
from audio_concat import audioConcat
from runcmd import *
from audio_sep import *
import cv2
import os
import shutil
import logger
import time


VERSION = 'v1.1.0'
SOURCE_PATH = 'source/'
TMP_PATH = 'tmp/'

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

def auto_op_replace(video_input_path, video_output_path, op_type, diff_threshold, pre_threshold, start_offset, end_offset, std_out, progress_bar):
    logger.stdout("==================================\n")
    logger.stdout("Automatic Opening Replacement Tool {}".format(VERSION))
    logger.stdout(time.strftime("%a %b %d %H:%M:%S %Y\n"))
    logger.stdout("==================================\n")
    logger.info('Locating opening of the video "{}"...'.format(video_input_path))
    # 存在性检查
    if(not os.path.exists(video_input_path)):
        raise FileExistsError
        
    # 原文件目录
    # video_dir = os.path.dirname(video_input_path)
    
    try:
        # 路径去中文化
        """
        filename_new = ''.join(random.sample(string.ascii_letters + string.digits,10))
        new_path = os.path.dirname(video_input_path) + os.path.sep + filename_new + os.path.splitext(video_input_path)[-1]
        os.rename(video_input_path,new_path)
        video_input_path = new_path
        """

        # 获取视频帧率帧大小信息, 可行性检测
        info = cv2.VideoCapture(video_input_path)
        fps = round(info.get(cv2.CAP_PROP_FPS),2)
        width = info.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = info.get(cv2.CAP_PROP_FRAME_HEIGHT)
        info.release()
        if(fps!=24.0 and fps!=29.97):
            raise FPSException
        if(width!=1920 or height!=1080):
            raise FrameSizeException

        # 定位OP头尾帧
        start_frame, end_frame, op_type = locate_opening(
            video_input_path = video_input_path,
            op_type = op_type,
            diff_threshold = diff_threshold,
            pre_threshold = pre_threshold,
            start_offset = start_offset,
            end_offset = end_offset,
            std_out = std_out
        )
        logger.success("Identified the range of OP: frame {}-{}".format(start_frame,end_frame))
        progress_bar.setHidden(False)
        progress_bar.setValue(0)

        # 视频剪切拼接 CutA-CutB-CutC
        """
        
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
        """
        

        # 移植音频
        """
        runcmd("ffmpeg.exe -y -i \"{input:s}\" -vn -acodec copy {TMP_PATH:s}audioOnly.aac".format(
            input = video_input_path,
            TMP_PATH = TMP_PATH
        ))
        """

        # 剥离原音频
        # runcmd("ffmpeg.exe -y -i \"{input:s}\" {output:s}".format(
        #     input = video_input_path,
        #     output = TMP_PATH + 'input_audioOnly.mp3'
        # ))

        # 剥离原音频
        separate_audio(video_input_path)

        # cv2剪辑影像
        std_out.setText("正在处理视频...")
        cv2clip(video_input_path, op_type, start_frame, end_frame, fps, progress_bar)
        logger.success("Video processing completed!")

        # 剪切合并新音频
        std_out.setText("正在处理音频...")
        audioConcat(TMP_PATH+'input_audioOnly.mp3', start_frame, end_frame, fps, op_type)

        # 合并影像与音频
        std_out.setText("合并中...")
        runcmd("ffmpeg.exe -y -i {video:s} -i {audio:s} -c copy -map 0:v:0 -map 1:a:0 \"{output:s}\"".format(
            video = TMP_PATH + "output_videoOnly.mp4",
            audio = TMP_PATH + "output_audioOnly.mp3",
            output = video_output_path
        ))
        # merge_audio(TMP_PATH+"output_videoOnly.mp4",TMP_PATH+"output_audioOnly.mp3",video_output_path)
        logger.success("Audio processing completed!")

        # 成果物检测
        if(not os.path.exists(video_output_path)):
            logger.error('Video synthesis failed!')
            raise ConcatException
        else:
            logger.success('The Opening has been replaced!')

    except LocateException:
        logger.error("No complete opening founded!")
        raise LocateException
    
    finally:
        # 恢复文件名
        # os.rename(video_input_path,os.path.dirname(video_input_path) + os.path.sep + filename_old)
        
        # 清空临时文件
        shutil.rmtree(TMP_PATH)
        os.mkdir(TMP_PATH)
        pass