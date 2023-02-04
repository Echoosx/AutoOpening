from PyQt6.QtWidgets import QApplication, QWidget, QPushButton,QMainWindow,QFileDialog,QLineEdit,QInputDialog,QLabel,QComboBox,QHBoxLayout,QVBoxLayout,QDoubleSpinBox,QSpinBox,QCheckBox,QTextEdit,QProgressBar,QMessageBox
from PyQt6.QtGui import QAction,QIcon
from PyQt6.QtCore import Qt,QSize
from my_exception import *
from main import auto_op_replace
from logger import stdout_box
import global_var
import sys
import os
import cv2
import configparser
import logger
import traceback
import time


# 全局变量
global_var._init()
global_var.set_value('abort_flag',False)
global_var.set_value('running_flag',False)

config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__),'config.ini')
config.read(config_path,encoding='utf-8')

message_label = QLabel()
progress_bar = QProgressBar()
abort_btn = QPushButton('放弃')

class MLineEdit(QLineEdit):
    def __init__(self, title, main, video):
        super().__init__(title, main)
        self.setAcceptDrops(True)
        self.main = main
        self.video = video

    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        filePathList = e.mimeData().text()
        filePath = filePathList.split('\n')[0] #拖拽多文件只取第一个地址
        filePath = filePath.replace('file:///', '', 1) #去除文件地址前缀的特定字符
        self.setText(filePath)
        if(self.video):
            self.main.set_root(filePath)


class RunWindow(QWidget):
    def __init__(self,title):
        super().__init__()
        self.setWindowTitle(title)
        self.initUI()
    
    def initUI(self):
        self.resize(QSize(600,400))
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowIcon(QIcon('windowIcon.ico'))
        
        # 错误报告
        # self.log = logger.read_log()
        # error_text_box = QTextEdit()
        # error_text_box.setText(self.log)
        # error_text_box.setReadOnly(True)
        
        # 日志显示框
        stdout_box.setReadOnly(True)

        # 保存日志按钮
        save_btn = QPushButton('保存日志',self)
        save_btn.clicked.connect(self.save_log)

        # 停止运行按钮
        abort_btn.clicked.connect(self.abort)
        abort_btn.setEnabled(True)

        # 信息条
        # self.message = QLabel()

        # 进度条
        # self.progress_bar = QProgressBar()
        progress_bar.setRange(0,100)
        progress_bar.setFixedWidth(300)
        progress_bar.setHidden(True)
        # signal.progress_update.connect(self.set)
        

        # 布局
        grid = QVBoxLayout()
        grid.addWidget(stdout_box)

        row_2 = QHBoxLayout()
        
        row_2.addWidget(abort_btn)
        row_2.addWidget(save_btn)
        row_2.addWidget(message_label)
        row_2.addStretch(1)
        row_2.addWidget(progress_bar)
        grid.addLayout(row_2)

        self.setLayout(grid)
    
    # 保存日志
    def save_log(self):
        if(global_var.get_value('running_flag')):
            QMessageBox.about(self,"提示","不要在运行过程中保存日志")
            return
        log_path = QFileDialog.getSaveFileName(self, '保存日志到', './log/{}.log'.format(time.strftime("%Y_%m_%d"),"all files(*.*)"))[0]
        if(log_path!=''):
            log_content = stdout_box.toPlainText()
            logger.write_log(log_content,log_path)

    # 中止运行
    def abort(self):
        self.abort_confirm()

    # 关闭窗口
    def closeEvent(self, event):
        if(self.abort_confirm()):
            event.accept()
        else:
            event.ignore()

    # 中止确认
    def abort_confirm(self):
        if(global_var.get_value('running_flag')):
            reply = QMessageBox.question(self, '警告', '是否终止当前任务？')
            if(reply == QMessageBox.StandardButton.Yes):
                global_var.set_value('abort_flag',True)
                abort_btn.setEnabled(False)
                message_label.setStyleSheet("color:black;")
                message_label.setText("任务终止")
                return True
            else:
                return False
        else:
            return True



class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.config = configparser.ConfigParser()
        self.config_path = os.path.join(os.path.dirname(__file__),'config.ini')
        self.config.read(self.config_path,encoding='utf-8')
        self.__default_input_path = self.config['DEFAULT']['root']
        self.__default_output_path = self.config['DEFAULT']['root']
        self.__default_prefix = self.config['DEFAULT']['prefix']
        self.__default_diff = 0.9
        self.__default_pre = 0.8

    def initUI(self):

        centralWidget = QWidget()
        grid = QVBoxLayout()

        # 菜单栏
        menubar = self.menuBar()
        settingMenu = menubar.addMenu('设置')
        defaultPrefix = QAction('输出前缀',self)
        defaultRoot = QAction('默认路径',self)
        settingMenu.addAction(defaultPrefix)
        settingMenu.addAction(defaultRoot)
        
        defaultPrefix.triggered.connect(self.setPrefix)
        defaultRoot.triggered.connect(self.setRoot)

        # 视频
        self.input_lineEdit = MLineEdit('',self,True)
        self.input_lineEdit.setPlaceholderText('可以将文件拖拽到这里')
        self.input_pushButton = QPushButton('视频')
        self.input_lineEdit.setReadOnly(True)
        self.input_pushButton.clicked.connect(self.select_input_file)

        # 输出
        self.output_lineEdit = QLineEdit('')
        self.output_lineEdit.setPlaceholderText('默认输出到与原视频相同目录下')
        self.output_pushButton = QPushButton('输出')
        self.output_pushButton.clicked.connect(self.select_output_file)

        # 选择OP类型
        self.type_select = QComboBox()
        self.type_select.addItems(["自动识别","混血新版OP","混血旧版OP"])
        self.type_select.setMinimumWidth(90)
        type_select_label = QLabel('OP类型 ')

        # 设置diff阈值
        self.diff_threshold = QDoubleSpinBox()
        self.diff_threshold.setDecimals(3)
        self.diff_threshold.setMaximum(0.999)
        self.diff_threshold.setMinimum(0.8)
        self.diff_threshold.setSingleStep(0.001)
        self.diff_threshold.setValue(0.9)
        self.diff_threshold.setMinimumWidth(90)
        self.diff_threshold.setToolTip('相似阈值越低, 识别兼容性越高\n没有识别成功可尝试降低该阈值\n相似阈值过低可能会识别到错误的位置')
        self.diff_threshold.valueChanged.connect(self.diff_threshold_change)
        diff_threshold_label = QLabel('相似阈值 ')
        diff_threshold_label.setToolTip('相似阈值越低, 识别兼容性越高\n没有识别成功可尝试降低该阈值\n相似阈值过低可能会识别到错误的位置')

        # 设置预处理阈值
        self.pre_threshold = QDoubleSpinBox()
        self.pre_threshold.setDecimals(2)
        self.pre_threshold.setMaximum(0.9)
        self.pre_threshold.setMinimum(0.6)
        self.pre_threshold.setSingleStep(0.01)
        self.pre_threshold.setValue(0.8)
        self.pre_threshold.setMinimumWidth(90)
        self.pre_threshold.setToolTip('预识别阈值越高, 耗时可能越短, 但识别兼容性变差\n预识别阈值理论上要低于相似阈值\n预识别阈值过高可能导致无法识别')
        pre_threshold_label = QLabel('预识别阈值 ')
        pre_threshold_label.setToolTip('预识别阈值越高, 耗时可能越短, 但识别兼容性变差\n预识别阈值理论上要低于相似阈值\n预识别阈值过高可能导致无法识别')

        # OP头部偏移
        self.start_offset = QSpinBox()
        self.start_offset.setValue(0)
        self.start_offset.setSingleStep(1)
        self.start_offset.setMaximum(99)
        self.start_offset.setMinimum(-99)
        self.start_offset.setMinimumWidth(90)
        self.start_offset.setSuffix('帧')
        self.start_offset.setToolTip('在自动识别基础上手动调节OP插入时间\n正值代表向后偏移, 负值代表向前偏移')
        start_offset_label = QLabel('头部偏移量 ')
        start_offset_label.setToolTip('在识别基础上手动调节OP插入时间\n正值代表向后偏移, 负值代表向前偏移')

        # OP尾部偏移
        self.end_offset = QSpinBox()
        self.end_offset.setValue(0)
        self.end_offset.setMaximum(99)
        self.end_offset.setMinimum(-99)
        self.end_offset.setSingleStep(1)
        self.end_offset.setMinimumWidth(90)
        self.end_offset.setSuffix('帧')
        self.end_offset.setToolTip('在自动识别基础上手动调节OP结束时间\n正值代表向后偏移, 负值代表向前偏移')
        end_offset_label = QLabel('尾部偏移量 ')
        end_offset_label.setToolTip('在自动识别基础上手动调节OP结束时间\n正值代表向后偏移, 负值代表向前偏移')

        # 模式
        self.auto_close = QCheckBox()
        self.auto_close.setText('完成后自动关闭')
        self.auto_close.setChecked(True)

        # 运行按钮
        self.run_btn = QPushButton('运行',self)
        self.run_btn.clicked.connect(self.op_replace)

        # 退出按钮
        cancel_btn = QPushButton('取消', self)
        cancel_btn.clicked.connect(self.close_Event)

        # 重置按钮
        reset_btn = QPushButton('重置', self)
        reset_btn.clicked.connect(self.reset)
        
        # std输出
        self.std_out = QLabel()

        # 信息条
        self.msg = QLabel()
        self.msg.setText("注: 当OP播放完后, 即可按K键跳过剩余部分的扫描")

        # 窗口布局
        row_1 = QHBoxLayout()
        row_1.addWidget(self.input_lineEdit)
        row_1.addWidget(self.input_pushButton)
        grid.addLayout(row_1)

        row_2 = QHBoxLayout()
        row_2.addWidget(self.output_lineEdit)
        row_2.addWidget(self.output_pushButton)
        grid.addLayout(row_2)

        row_3 = QHBoxLayout()
        row_3.addWidget(type_select_label)
        row_3.addWidget(self.type_select)
        row_3.addStretch(1)
        row_3.addWidget(diff_threshold_label)
        row_3.addWidget(self.diff_threshold)
        row_3.addStretch(1)
        row_3.addWidget(pre_threshold_label)
        row_3.addWidget(self.pre_threshold)
        grid.addLayout(row_3)

        row_4 = QHBoxLayout()
        row_4.addWidget(start_offset_label)
        row_4.addWidget(self.start_offset)
        row_4.addStretch(1)
        row_4.addWidget(end_offset_label)
        row_4.addWidget(self.end_offset)
        row_4.addStretch(1)
        row_4.addWidget(self.auto_close)
        row_4.addStretch(1)
        grid.addLayout(row_4)
        
        grid.addStretch(1)

        row_5 = QHBoxLayout()
        row_5.addWidget(self.std_out)
        row_5.addStretch(1)
        row_5.addWidget(self.run_btn)
        row_5.addWidget(cancel_btn)
        row_5.addWidget(reset_btn)
        grid.addLayout(row_5)
    
        self.setMinimumSize(500,230)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.center()

        self.setWindowTitle('混血万事屋OP自动替换工具')
        self.setWindowIcon(QIcon('windowIcon.ico'))
        centralWidget.setLayout(grid)
        self.setCentralWidget(centralWidget)
        self.show()

    # 运行提示信息
    def write_message(self,msg,type):
        message_label.setText(msg)
        if(type=='success'):
            message_label.setStyleSheet("color:green;")
        elif(type=='error'):
            message_label.setStyleSheet("color:red;")
        else:
            message_label.setStyleSheet("color:black;")

    # op替换功能入口
    def op_replace(self):
        video_input_path = self.input_lineEdit.text()
        video_output_path = self.output_lineEdit.text()
        if(not self.preCheck(video_input_path,video_output_path)): return
        op_type = self.type_select.currentText()
        diff_threshold = self.diff_threshold.value()
        pre_threshold = self.diff_threshold.value()
        start_offset = self.start_offset.value()
        end_offset = self.end_offset.value()
        auto_close = self.auto_close.isChecked()
        filename = os.path.splitext(video_input_path)[0]
        global_var.set_value('abort_flag',False)
        global_var.set_value('running_flag',True)
        stdout_box.setPlainText('')
        message_label.setStyleSheet("color:black;")
        message_label.setText('')

        self.run_btn.setEnabled(False)
        self.run_window = RunWindow(filename)
        self.run_window.show()

        try:
            auto_op_replace(video_input_path,video_output_path, op_type, diff_threshold, pre_threshold, start_offset, end_offset, message_label, progress_bar)
            progress_bar.setValue(100)
            self.write_message("已完成!",'success')
            abort_btn.setEnabled(False)
            global_var.set_value('running_flag',False)
            os.startfile(os.path.dirname(video_output_path))
            if(auto_close):
                time.sleep(3)
                self.close_Event()
                self.run_window.close()

        except KeyboardInterrupt:
            pass
        except FileExistsError:
            self.write_message("无法找到视频!",'error')
        except LocateException:
            self.write_message("未定位到完整OP!\n请检查OP类型是否正确或降低相似阈值",'error')
        except FPSException:
            self.write_message("视频帧率不符合标准!",'error')
        except FrameSizeException:
            self.write_message("视频尺寸不符合标准!",'error')
        except ConcatException:
            self.write_message("视频合并失败!",'error')
        except UserAbortException:
            logger.stdout("\nWork is aborted by user.")
        except Exception:
            self.write_message("未知错误!\n请将日志反馈给开发者",'error')
            logger.error(traceback.format_exc())
        finally:
            global_var.set_value('running_flag',False)
            cv2.destroyAllWindows()
            self.run_btn.setEnabled(True)

    # 退出按钮
    def close_Event(self):
        if(self.abort_confirm()):
            self.close()

    # 重写关闭按钮
    def closeEvent(self, event) -> None:
        if(self.abort_confirm()):
            event.accept()
        else:
            event.ignore()

    # 中止确认
    def abort_confirm(self):
        if(global_var.get_value('running_flag')):
            reply = QMessageBox.question(self, '警告', '是否终止当前任务？')
            if(reply == QMessageBox.StandardButton.Yes):
                global_var.set_value('abort_flag',True)
                abort_btn.setEnabled(False)
                message_label.setStyleSheet("color:black;")
                message_label.setText("任务终止")
                return True
            else:
                return False
        else:
            return True

    # 设置前缀
    def setPrefix(self):
        prefix_input = QInputDialog()
        text,ok = prefix_input.getText(self,'设置','输出前缀',text=self.__default_prefix)
        prefix_input.setOkButtonText('保存')
        prefix_input.setCancelButtonText('取消')
        
        if (ok and text != ''):
            self.__default_prefix = str(text)
            self.config['DEFAULT']['prefix'] = str(text)
            with open(self.config_path,'w',encoding = 'utf-8') as configfile:
                self.config.write(configfile)

    # 设置默认目录
    def setRoot(self):
        home_dir = './'
        dirpath = QFileDialog.getExistingDirectory(self, '设置默认目录', home_dir)

        if (dirpath):
            self.__default_input_path = dirpath
            self.__default_output_path = dirpath
            self.config['DEFAULT']['root'] = dirpath
            with open(self.config_path,'w',encoding = 'utf-8') as configfile:
                self.config.write(configfile)
    
    # 选择文件EVENT
    def select_input_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, '选择视频文件',self.__default_input_path,"Video (*.mp4)")
        # if(filepath!=''):
        #     self.input_lineEdit.setText(filepath)
        #     self.set_root(filepath)
        if(filepath != ''):
            self.input_lineEdit.setText(filepath)
            self.output_lineEdit.setText(os.path.dirname(filepath) + '/' + self.__default_prefix + os.path.basename(filepath))
            self.input_lineEdit.setCursorPosition(0)
            self.output_lineEdit.setCursorPosition(0)

    def select_output_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "输出至",self.__default_output_path + '',"Video (*.mp4)")
        self.output_lineEdit.setText(filename)

    # output同步input路径
    def set_root(self, filepath):
        self.__default_input_path = filepath
        self.__default_output_path = self.get_output_filepath(filepath,self.__default_prefix)
        self.output_lineEdit.setText(self.__default_output_path)

    def get_output_filepath(self, filepath, prefix):
        dirname = os.path.dirname(filepath)
        basename = os.path.basename(filepath)
        return os.path.join(dirname, prefix + basename)

    # 同步相似阈值下限
    def diff_threshold_change(self):
        self.diff_threshold.setMinimum(self.pre_threshold.value())

    # 重置内容
    def reset(self):
        self.input_lineEdit.setText('')
        self.output_lineEdit.setText('')
        self.type_select.setCurrentIndex(0)
        self.diff_threshold.setValue(self.__default_diff)
        self.pre_threshold.setValue(self.__default_pre)
        self.start_offset.setValue(0)
        self.end_offset.setValue(0)
        self.auto_close.setChecked(False)
        self.std_out.setText('')

    # stdout
    def stdout(self,type,msg):
        if(type):
            self.std_out.setStyleSheet("color:green;")
            self.std_out.setText(msg)
        else:
            self.std_out.setStyleSheet("color:red;")
            self.std_out.setText(msg)


    # 参数预检查
    def preCheck(self,input_path,output_path):
        if(input_path == ''):
            self.stdout(False,"输入视频为空!")
            return False
        elif(output_path == ''):
            self.stdout(False,"输出路径为空!")
            return False
        else:
            return True

    # 窗口居中
    def center(self):
        
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()

        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # 检测键盘skip按键
    def keyPressEvent(self, event):
        if(event.key() == Qt.Key.Key_K):
            global_var.set_value('skip_flag',True)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWidget = MainWidget()
    sys.exit(app.exec())