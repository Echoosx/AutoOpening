from moviepy.editor import *
from PyQt6.QtWidgets import QApplication

TMP_PATH = "tmp/"

def separate_audio(video_path):
    QApplication.processEvents()
    audio = AudioFileClip(video_path)
    audio.write_audiofile(TMP_PATH + "input_audioOnly.mp3")

def merge_audio(video_path, audio_path, output_path):
    QApplication.processEvents()
    audio = AudioFileClip(audio_path)
    video = VideoFileClip(video_path)
    video.set_audio(audio)
    video.write_videofile(output_path)