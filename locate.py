from skimage.metrics import structural_similarity as sk_cpt_ssim
from my_exception import LocateException
from rich.progress import Progress
import global_var
import logger
import cv2

SOURCE_PATH = 'source/'
start_dict = {
    "混血新版OP":SOURCE_PATH + 'op_start_new.jpg',
    "混血旧版OP":SOURCE_PATH + 'op_start_old.jpg'
}
end_dict = {
    "混血新版OP":SOURCE_PATH + 'op_end_new.jpg',
    "混血旧版OP":SOURCE_PATH + 'op_end_old.jpg'
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
def locate_opening(video_input_path, op_type , diff_threshold, pre_threshold, start_offset, end_offset, debug_mod, std_out):
    frame_count = 0
    start_frame = 0
    end_frame = 0
    start_flag = False
    cap = cv2.VideoCapture(video_input_path)
    frame_total = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    op_start_img = cv2.imread(start_dict[op_type])
    op_end_img = cv2.imread(end_dict[op_type])

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
        score_start_pre = compare_image(img[550:560,900:950], op_start_img[550:560,900:950])
        score_end_pre = compare_image(img[550:560,900:950], op_end_img[550:560,900:950])
        if(not start_flag and score_start_pre > pre_threshold):
            score_start = compare_image(img,op_start_img)
            if(debug_mod):
                logger.info("[frame:{}] [similar value:{}]".format(frame_count,score_start))
            if(score_start > diff_threshold):
                start_frame = frame_count
                start_flag = True
                logger.success("Found the start frame of the opening: {}".format(start_frame))
                std_out.setStyleSheet("color:green;")
                std_out.setText('识别到OP头部: {}帧'.format(start_frame))
        
        if(score_end_pre > pre_threshold):
            score_end = compare_image(img,op_end_img)
            if(debug_mod):
                logger.info("[frame:{}] [similar value:{}]".format(frame_count,score_end))
            if(score_end > diff_threshold):
                end_frame = frame_count
        
        elif(end_frame!=0 and end_frame == frame_count-1):
            logger.success("Found the end frame of the opening: {}".format(end_frame))
            if(start_flag):
                std_out.setStyleSheet("color:green;")
                std_out.setText('已识别到完整OP: {}-{}帧'.format(start_frame, end_frame) + '\n可按K键跳过剩余部分!')

        # 监听中止按键
        key = cv2.waitKey(20) & 0xff
        if  key == ord('k') or key == ord('K') :
            cv2.destroyAllWindows()
            break
        if global_var.get_value('skip_flag'):
            cv2.destroyAllWindows()
            break
    cap.release()

    if(start_frame==0 or end_frame==0):
        raise LocateException
    else:
        # 实际情况特殊处理
        if(op_type == "混血新版OP"):
            start_frame = start_frame - 7 + start_offset
            end_frame = end_frame + end_offset
        else:
            start_frame = start_frame - 2 + start_offset
            end_frame = end_frame + end_offset
    
    return start_frame,end_frame