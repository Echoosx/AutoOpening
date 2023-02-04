from skimage.metrics import structural_similarity as sk_cpt_ssim
from my_exception import *
import global_var
import logger
import cv2

SOURCE_PATH = 'source/'
start_dict = {
    "混血新版OP":SOURCE_PATH + 'op_start_new.jpg',
    "混血旧版OP":SOURCE_PATH + 'op_start_old.jpg',
}
end_dict = {
    "混血新版OP":SOURCE_PATH + 'op_end_new.jpg',
    "混血旧版OP":SOURCE_PATH + 'op_end_old.jpg',
}

# 计算图片相似度
def compare_image(image_a,image_b):
    # 使用色彩空间转化函数 cv2.cvtColor( )进行色彩空间的转换
    gray_a = cv2.cvtColor(image_a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(image_b, cv2.COLOR_BGR2GRAY)
    # 计算图像相似度并圈出不同处
    (score, _) = sk_cpt_ssim(gray_a, gray_b, full=True)
    # print("SSIM: {}".format(score))
    return score

# 定位OP的起始结束帧位置
def locate_opening(video_input_path, op_type , diff_threshold, pre_threshold, start_offset, end_offset, std_out):
    frame_count = -1
    start_frame = -1
    end_frame = -1
    start_flag = False
    cap = cv2.VideoCapture(video_input_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if(op_type != "自动识别"):
        op_start_img = cv2.imread(start_dict[op_type])
        op_end_img = cv2.imread(end_dict[op_type])
        score_start_pre = 0
        score_end_pre = 0

        while cap.isOpened():
            frame_count += 1
            locating, img = cap.read()
            if not locating:
                break
            
            # 显示视频
            cv2.namedWindow('video',0)
            cv2.resizeWindow('video', 1300,720)
            cv2.imshow('video', img)

            # diff
            if(not start_flag):
                score_start_pre = compare_image(img[550:560,900:950], op_start_img[550:560,900:950])
            else:
                score_end_pre = compare_image(img[550:560,900:950], op_end_img[550:560,900:950])
            
            # 定位开始帧
            if(not start_flag and (score_start_pre > pre_threshold)):
                score_start = compare_image(img,op_start_img)
                logger.info("[{:.1f}%] {}/{} frames, similar {}".format(
                    (frame_count * 100) / total_frames,
                    frame_count,
                    total_frames,
                    score_start
                ))
                if(score_start > diff_threshold):
                    start_frame = frame_count
                    start_flag = True
                    logger.success("Found the start frame of OP: {}".format(start_frame))
                    std_out.setText('识别到OP头部: {}帧'.format(start_frame))
            
            # 定位结束帧
            if(start_flag and (score_end_pre > pre_threshold)):
                score_end = compare_image(img,op_end_img)
                logger.info("[{:.1f}%] {}/{} frames, similar {}".format(
                    (frame_count * 100) / total_frames,
                    frame_count,
                    total_frames,
                    score_end
                ))
                if(score_end > diff_threshold):
                    end_frame = frame_count
            
            # 输出最终的结束帧
            elif(start_flag and end_frame!=-1 and end_frame == frame_count-1):
                logger.success("Found the end frame of OP: {}".format(end_frame))
                if(start_flag):
                    cv2.destroyAllWindows()
                    break
            
            # 定时输出
            if(frame_count%20 == 0):
                if global_var.get_value('abort_flag'):
                    cv2.destroyAllWindows()
                    raise UserAbortException
                logger.info("[{:.1f}%] {}/{} frames, Locating the range of OP...".format(
                    (frame_count * 100) / total_frames,
                    frame_count,
                    total_frames
                ))

            # 监听中止按键
            key = cv2.waitKey(20) & 0xff
    else:
        op_start_img_new = cv2.imread(start_dict["混血新版OP"])
        op_start_img_old = cv2.imread(start_dict["混血旧版OP"])
        op_end_img = cv2.imread(end_dict["混血新版OP"])
        score_start_pre_new = 0
        score_start_pre_old = 0
        score_end_pre = 0
        
        while cap.isOpened():
            frame_count += 1
            locating, img = cap.read()
            if not locating: break
            
            # 显示视频
            cv2.namedWindow('video',0)
            cv2.resizeWindow('video', 1300,720)
            cv2.imshow('video', img)

            # diff
            if(not start_flag):
                score_start_pre_new = compare_image(img[550:560,900:950], op_start_img_new[550:560,900:950])
                score_start_pre_old = compare_image(img[550:560,900:950], op_start_img_old[550:560,900:950])
            else:
                score_end_pre = compare_image(img[550:560,900:950], op_end_img[550:560,900:950])
            
            # 定位开始帧
            if(not start_flag):
                if(score_start_pre_new > pre_threshold):
                    score_start = compare_image(img,op_start_img_new)
                    logger.info("[{:.1f}%] {}/{} frames, similar {}".format(
                        (frame_count * 100) / total_frames,
                        frame_count,
                        total_frames,
                        score_start
                    ))
                    if(score_start > diff_threshold):
                        start_frame = frame_count
                        start_flag = True
                        op_type = "混血新版OP"
                        logger.success("Found the start frame of OP: {}".format(start_frame))
                        std_out.setText('识别到OP头部: {}帧'.format(start_frame))
                
                elif(score_start_pre_old > pre_threshold):
                    score_start = compare_image(img,op_start_img_old)
                    logger.info("[{:.1f}%] {}/{} frames, similar {}".format(
                        (frame_count * 100) / total_frames,
                        frame_count,
                        total_frames,
                        score_start
                    ))
                    if(score_start > diff_threshold):
                        start_frame = frame_count
                        start_flag = True
                        op_type = "混血旧版OP"
                        op_end_img = cv2.imread(end_dict["混血旧版OP"])
                        logger.success("Found the start frame of OP: {}".format(start_frame))
                        std_out.setText('识别到OP头部: {}帧'.format(start_frame))
            
            # 定位结束帧
            if(start_flag and (score_end_pre > pre_threshold)):
                score_end = compare_image(img,op_end_img)
                logger.info("[{:.1f}%] {}/{} frames, similar {}".format(
                    (frame_count * 100) / total_frames,
                    frame_count,
                    total_frames,
                    score_end
                ))
                if(score_end > diff_threshold):
                    end_frame = frame_count
            
            # 输出最终的结束帧
            elif(start_flag and end_frame!=-1 and end_frame == frame_count-1):
                logger.success("Found the end frame of OP: {}".format(end_frame))
                if(start_flag):
                    cv2.destroyAllWindows()
                    break
            
            # 定时输出
            if(frame_count%20 == 0):
                if global_var.get_value('abort_flag'):
                    cv2.destroyAllWindows()
                    raise UserAbortException
                logger.info("[{:.1f}%] {}/{} frames, Locating the range of OP...".format(
                    (frame_count * 100) / total_frames,
                    frame_count,
                    total_frames
                ))

            # 监听中止按键
            key = cv2.waitKey(20) & 0xff

    cap.release()

    if(start_frame == -1 or end_frame == -1):
        raise LocateException
    else:
        # 实际情况特殊处理
        if(op_type == "混血新版OP"):
            start_frame = start_frame - 11 + start_offset
            end_frame = end_frame + end_offset
        else:
            start_frame = start_frame + start_offset
            end_frame = end_frame + end_offset
        
        # 帧越界修正
        if(start_frame < 0):
            start_frame = 0
        
        std_out.setText("识别到OP: {}-{}帧".format(start_frame, end_frame))
    
    return start_frame, end_frame, op_type