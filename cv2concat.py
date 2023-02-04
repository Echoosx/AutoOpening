from PyQt6.QtWidgets import QApplication
import cv2
import logger
from my_exception import *
import global_var
import math

SOURCE_PATH = 'source/'
TMP_PATH = 'tmp/'

op_dict = {
    "混血新版OP":SOURCE_PATH + 'op_new.mp4',
    "混血旧版OP":SOURCE_PATH + 'op_old.mp4'
}
op_dict_29 = {
    "混血新版OP":SOURCE_PATH + 'op_new_29.97.mp4',
    "混血旧版OP":SOURCE_PATH + 'op_old_29.97.mp4'    
}

def cv2clip(video_input_path, op_type, start_frame, end_frame, fps, progress_bar):
    progress_bar.setHidden(False)
    cap = cv2.VideoCapture(video_input_path)
    op = cv2.VideoCapture(op_dict[op_type]) if(fps == 24.0) else cv2.VideoCapture(op_dict_29[op_type])

    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    op_frames = int(op.get(cv2.CAP_PROP_FRAME_COUNT))
    total_frames = video_frames + op_frames - (end_frame - start_frame + 1)
    op_offset = op_frames - (end_frame - start_frame + 1)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(TMP_PATH + 'output_videoOnly.mp4', fourcc, fps, (int(width),int(height)), True)

    try:
        # cut_A部分
        cap.set(cv2.CAP_PROP_POS_FRAMES,0)
        pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

        while(pos < start_frame):
            progress_bar.setValue(math.floor((pos * 100.0)/total_frames))
            _, frame = cap.read()
            out.write(frame) 
            pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            if(pos%50==0):
                if global_var.get_value('abort_flag'): raise UserAbortException
                formatStdout(pos,total_frames,"Editing the part before OP...")
            QApplication.processEvents()

        # cut_B部分
        op.set(cv2.CAP_PROP_POS_FRAMES,0)
        pos = int(op.get(cv2.CAP_PROP_POS_FRAMES))

        while(pos < op_frames):
            progress_bar.setValue(math.floor(((pos + start_frame)*100.0)/total_frames))
            _, frame = op.read()
            out.write(frame)
            pos = int(op.get(cv2.CAP_PROP_POS_FRAMES))
            if((pos + start_frame)%50==0):
                if global_var.get_value('abort_flag'): raise UserAbortException
                formatStdout((pos + start_frame),total_frames,"Editing the part of OP...")
            QApplication.processEvents()

        # cut_C部分
        cap.set(cv2.CAP_PROP_POS_FRAMES, end_frame + 1)
        pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

        while(pos < video_frames):
            progress_bar.setValue(math.floor(((pos + op_offset) * 100)/total_frames))
            _, frame = cap.read()
            out.write(frame)
            pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            if((pos + op_offset)%50==0):
                if global_var.get_value('abort_flag'): raise UserAbortException
                formatStdout((pos + op_offset),total_frames,"Editing the part after OP...")
            QApplication.processEvents()

    finally:
        op.release()
        cap.release()
        out.release()

def formatStdout(pos,total_frames,msg):
    logger.info("[{:.1f}%][{}/{} frames] {}".format(
        (pos * 100) / total_frames,
        pos,
        total_frames,
        msg
    ))