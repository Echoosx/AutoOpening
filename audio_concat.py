from pydub import AudioSegment
import global_var
from my_exception import UserAbortException
from PyQt6.QtWidgets import QApplication
import logger

# TMP_PATH = global_var.get_value("TMP_PATH")
# SOURCE_PATH = global_var.get_value("SOURCE_PATH")
TMP_PATH = 'tmp/'
SOURCE_PATH = 'source/'

audio_dict = {
    "混血新版OP":"op_new_audio.mp3",
    "混血旧版OP":"op_old_audio.mp3"
}

def cutVoice(input_path, op_start_frame, op_end_frame, fps):
    if global_var.get_value('abort_flag'):
        raise UserAbortException
    sound = AudioSegment.from_mp3(input_path)
    if(op_start_frame!=0):
        end_time = round((op_start_frame * 1000) / fps)
        soundA = sound[:end_time]
        soundA.export(TMP_PATH + "sound_A.mp3",format="mp3")
        QApplication.processEvents()

    start_time = round((op_end_frame * 1000) /fps)
    soundC = sound[start_time:]
    soundC.export(TMP_PATH + "sound_C.mp3",format="mp3")
    QApplication.processEvents()

def joinVoice(start_frame, soundA_path, soundB_path, soundC_path, output_path):
    if global_var.get_value('abort_flag'):
        raise UserAbortException
    if(start_frame != 0):
        # 加载需要拼接的三个片段
        soundA = AudioSegment.from_file(soundA_path,"mp3")
        soundB = AudioSegment.from_file(soundB_path,"mp3")
        soundC = AudioSegment.from_file(soundC_path,"mp3")
        QApplication.processEvents()
    
        # 取得BC两个片段的声音分贝
        db1 = soundA.dBFS
        db2 = soundB.dBFS
        dbplus = db1 - db2
    
        # 设置声音大小为平均数
        if dbplus < 0:
            soundA += abs(dbplus)
            soundC +  abs(dbplus)
        else:
            soundB += abs(dbplus)
    
        # 拼接三个音频片段
        finSound = soundA + soundB + soundC
        finSound.export(output_path, format="mp3")
        QApplication.processEvents()
    else:
        soundB = AudioSegment.from_file(soundB_path,"mp3")
        soundC = AudioSegment.from_file(soundC_path,"mp3")
        QApplication.processEvents()

        # 取得BC两个片段的声音分贝
        db1 = soundC.dBFS
        db2 = soundB.dBFS
        dbplus = db1 - db2
        
        # 设置声音大小为平均数
        if dbplus < 0:
            soundC += abs(dbplus)
        else:
            soundB += abs(dbplus)
        # 拼接两个音频片段
        finSound = soundB + soundC
        finSound.export(output_path, format="mp3")
        QApplication.processEvents()


def audioConcat(audio_input_path, start_frame, end_frame, fps, op_type):
    cutVoice(audio_input_path,start_frame,end_frame,fps)
    joinVoice(start_frame, TMP_PATH+'sound_A.mp3', SOURCE_PATH+audio_dict[op_type], TMP_PATH+'sound_C.mp3', TMP_PATH+'output_audioOnly.mp3')