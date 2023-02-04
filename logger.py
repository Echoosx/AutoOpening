from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCursor
import time
import sys

LATEST_LOG_PATH = 'log/latest.log'

app = QApplication(sys.argv)
stdout_box = QTextEdit()

def stdout(msg,inline = False):
    print(msg, end='' if inline else '\n',flush=True)
    stdout_box.setPlainText(stdout_box.toPlainText() + '\n' + str(msg))
    stdout_box.moveCursor(QTextCursor.MoveOperation.End,QTextCursor.MoveMode.MoveAnchor)

def info(msg,inline = False):
    print("[INFO]\t {}".format(msg), end='' if inline else '\n',flush=True)
    stdout_box.setPlainText(stdout_box.toPlainText() + '\n[INFO]\t ' + str(msg))
    stdout_box.moveCursor(QTextCursor.MoveOperation.End,QTextCursor.MoveMode.MoveAnchor)

def success(msg,inline = False):
    print("[SUCCESS]\t {}".format(msg), end='' if inline else '\n',flush=True)
    stdout_box.setPlainText(stdout_box.toPlainText() + '\n[SUCCESS]\t ' + str(msg))
    stdout_box.moveCursor(QTextCursor.MoveOperation.End,QTextCursor.MoveMode.MoveAnchor)

def error(msg,inline = False):
    print("[ERROR]\t {}".format(msg), end='' if inline else '\n',flush=True)
    stdout_box.setPlainText(stdout_box.toPlainText() + '\n[ERROR]\t ' + str(msg))
    stdout_box.moveCursor(QTextCursor.MoveOperation.End,QTextCursor.MoveMode.MoveAnchor)

def warning(msg,inline = False):
    print("[WARN]\t {}".format(msg), end='' if inline else '\n',flush=True)
    stdout_box.setPlainText(stdout_box.toPlainText() + '\n[WARN]\t ' + str(msg))
    stdout_box.moveCursor(QTextCursor.MoveOperation.End,QTextCursor.MoveMode.MoveAnchor)

def debug(msg,inline = False):
    print("[DEBUG] {}".format(msg), end='' if inline else '\n',flush=True)
    stdout_box.setPlainText(stdout_box.toPlainText() + '\n[DEBUG]\t ' + str(msg))
    stdout_box.moveCursor(QTextCursor.MoveOperation.End,QTextCursor.MoveMode.MoveAnchor)

def read_log():
    with open(LATEST_LOG_PATH, 'r', encoding='UTF-8') as f:
        lines = f.read()
        return lines

def write_log(log_content,log_path):
    with open(log_path, 'w', encoding='UTF-8') as f:
        f.write(log_content)

def new_log():
    with open(LATEST_LOG_PATH, 'w', encoding='UTF-8') as f:
        f.write('')

def archive_log():
    date = time.strftime("%Y_%m_%d")
    latest_log = read_log()
    with open('log/' + date + '.log', 'a', encoding = 'UTF-8') as f:
        f.write(latest_log)