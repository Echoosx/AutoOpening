from PyQt6.QtWidgets import QApplication, QWidget, QPushButton,QMainWindow,QFileDialog,QLineEdit,QInputDialog,QLabel,QComboBox,QHBoxLayout,QVBoxLayout,QDoubleSpinBox,QSpinBox,QCheckBox,QTextEdit
from PyQt6.QtGui import QAction,QIcon
from PyQt6.QtCore import Qt,QSize
from my_exception import *
from main import auto_op_replace
import global_var
import sys
import os
import cv2
import configparser
import logger
import traceback


# 全局变量
global_var._init()
global_var.set_value('skip_flag',False)

config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__),'config.ini')
config.read(config_path,encoding='utf-8')

class ErrorWindow(QWidget):
    def __init__(self,title = '错误信息'):
        super().__init__()
        self.setWindowTitle(title)
        self.initUI()
    
    def initUI(self):
        self.resize(QSize(800,900))
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowIcon(QIcon('windowIcon.ico'))
        
        # 错误报告
        self.log = logger.read_log()
        error_text_box = QTextEdit()
        error_text_box.setText(self.log)
        error_text_box.setReadOnly(True)

        # 复制按钮
        copy_btn = QPushButton('复制',self)
        copy_btn.clicked.connect(self.copy_log)

        # 关闭按钮
        close_btn = QPushButton('关闭',self)
        close_btn.clicked.connect(self.close)

        # msg
        self.msg = QLabel()

        # 布局
        grid = QVBoxLayout()
        grid.addWidget(error_text_box)

        row_2 = QHBoxLayout()
        row_2.addWidget(self.msg)
        row_2.addStretch(1)
        row_2.addWidget(copy_btn)
        row_2.addWidget(close_btn)
        grid.addLayout(row_2)

        self.setLayout(grid)
    
    def copy_log(self):
        clipborad = QApplication.clipboard()
        clipborad.setText(self.log)
        self.msg.setText('已复制到剪贴板')

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
        self.type_select.addItems(["混血新版OP",'混血旧版OP'])
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
        self.start_offset.setMaximum(999)
        self.start_offset.setMinimum(-999)
        self.start_offset.setMinimumWidth(90)
        self.start_offset.setSuffix('帧')
        self.start_offset.setToolTip('在自动识别基础上手动调节OP插入时间\n正值代表向后偏移, 负值代表向前偏移')
        start_offset_label = QLabel('头部偏移量 ')
        start_offset_label.setToolTip('在识别基础上手动调节OP插入时间\n正值代表向后偏移, 负值代表向前偏移')

        # OP尾部偏移
        self.end_offset = QSpinBox()
        self.end_offset.setValue(0)
        self.end_offset.setMaximum(999)
        self.end_offset.setMinimum(-999)
        self.end_offset.setSingleStep(1)
        self.end_offset.setMinimumWidth(90)
        self.end_offset.setSuffix('帧')
        self.end_offset.setToolTip('在自动识别基础上手动调节OP结束时间\n正值代表向后偏移, 负值代表向前偏移')
        end_offset_label = QLabel('尾部偏移量 ')
        end_offset_label.setToolTip('在自动识别基础上手动调节OP结束时间\n正值代表向后偏移, 负值代表向前偏移')

        # 模式
        self.debug_mod = QCheckBox()
        self.debug_mod.setText('调试模式')
        self.debug_mod.setToolTip('勾选后将保留运行过程中的临时文件\n并在运行结束后输出控制台内容')

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
        row_4.addWidget(self.debug_mod)
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

        grid.addStretch(1)

        row_msg = QHBoxLayout()
        row_msg.addWidget(self.msg)
        row_msg.addStretch(1)
        grid.addLayout(row_msg)

        self.setFixedSize(500, 230)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.center()

        self.setWindowTitle('混血万事屋OP自动替换工具')
        self.setWindowIcon(QIcon('windowIcon.ico'))
        centralWidget.setLayout(grid)
        self.setCentralWidget(centralWidget)
        self.show()

    # op替换功能入口
    def op_replace(self):
        video_input_path = self.input_lineEdit.text()
        video_output_path = self.output_lineEdit.text()
        op_type = self.type_select.currentText()
        diff_threshold = self.diff_threshold.value()
        pre_threshold = self.diff_threshold.value()
        start_offset = self.start_offset.value()
        end_offset = self.end_offset.value()
        debug_mod = self.debug_mod.isChecked()
        global_var.set_value('skip_flag',False)

        if(self.preCheck(video_input_path,video_output_path)):
            self.std_out.setStyleSheet("color:black;")
            self.std_out.setText("正在识别OP…")
            self.run_btn.setEnabled(False)

            try:
                auto_op_replace(video_input_path, video_output_path, op_type, diff_threshold, pre_threshold, start_offset, end_offset, debug_mod, self.std_out)
                self.stdout(True,"视频已处理完成!")
                if(debug_mod):
                    self.error_window = ErrorWindow('控制台输出')
                    self.error_window.show()
            except KeyboardInterrupt:
                pass
            except FileExistsError:
                self.stdout(False,"无法找到视频!")
            except LocateException:
                self.stdout(False,"未定位到完整的OP!\n请检查OP类型是否正确, 或降低相似阈值")
            except ConcatExcption:
                self.stdout(False,"视频合并失败!")
                self.error_window = ErrorWindow()
                self.error_window.show()
            except Exception as e:
                self.stdout(False,"未知错误!\n请将错误信息反馈给开发者")
                logger.error(traceback.format_exc())
                self.error_window = ErrorWindow()
                self.error_window.show()
            finally:
                logger.archive_log()
                cv2.destroyAllWindows()
                self.run_btn.setEnabled(True)


    # 退出按钮
    def close_Event(self):
        global_var.set_value('skip_flag',True)
        self.close()

    # 重写关闭按钮
    def closeEvent(self, event) -> None:
        global_var.set_value('skip_flag',True)
        self.close()

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
        dirpath = QFileDialog.getExistingDirectory(self, 'Open file', home_dir)

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
        self.debug_mod.setChecked(False)
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