import cv2
import numpy as np

cap = cv2.VideoCapture('demo/demo_4.mp4')
frame_count = 0
while cap.isOpened():
    frame_count += 1
    locating, img = cap.read()
    if not locating:
        break

    # 显示视频
    cv2.namedWindow("video",0)
    cv2.resizeWindow("video", 1250, 720)
    cv2.imshow('video', img)
    
    # 写入图片
    cv2.imwrite('output/demo_3/frame_%d.jpg' %frame_count,img)

    # 监听中止按键
    key = cv2.waitKey(20) & 0xff
    if  key == ord('k') or key == ord('K') :
        break
