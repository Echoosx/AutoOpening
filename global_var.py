import logger
import traceback

def _init():  # 初始化
    global _global_dict
    _global_dict = {}
    #     'SOURCE_PATH':'source/',
    #     'TMP_PATH':'tmp/',
    #     'LOG_PATH':'log/'
    # }

def set_value(key, value):
    #定义一个全局变量
    _global_dict[key] = value

def get_value(key):
    #获得一个全局变量，不存在则提示读取对应变量失败
    try:
        return _global_dict[key]
    except KeyError:
        logger.error("Unable to read key '{}'".format(key))
    except Exception as e:
        logger.error(traceback.format_exc())