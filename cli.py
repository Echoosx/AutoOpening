from main import auto_op_replace
import os

if __name__ == "__main__":

    print("==========================================\n")
    print("    Automatic Opening Replacement Tool\n")
    print("==========================================\n")

    # 获取代操作视频路径
    video_input_path = input("Please drag the video in!\n")
    print("")
    video_input_path = video_input_path.strip(' ').strip('"')
    try:
        video_output_path = os.path.dirname(video_input_path) + '/' + "【OP】" + os.path.basename(video_input_path)
        auto_op_replace(video_input_path,video_output_path,'混血新版OP',0.95)

    except FileExistsError:
        print("\033[31m\nFailed! Video is not exist!\033[0m")
    
    except Exception as e:
        print("\033[31mUnknown Error!\033[0m",e)