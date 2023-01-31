from rich.console import Console
import time

console = Console()
LATEST_LOG_PATH = 'log/latest.log'

def info(msg,inline = False):
    console.print(msg, end='' if inline else '\n')
    write_log(msg)

def success(msg,inline = False):
    console.print("[green][SUCCESS][/] {}".format(msg), end='' if inline else '\n')
    write_log('[SUCCESS] ' + msg)

def error(msg,inline = False):
    console.print("[red][ERROR][/] {}".format(msg), end='' if inline else '\n')
    write_log('[ERROR] ' + msg)

def warning(msg,inline = False):
    console.print("[yellow][WARN][/] {}".format(msg), end='' if inline else '\n')
    write_log('[WARN] ' + msg)

def read_log():
    with open(LATEST_LOG_PATH, 'r', encoding='UTF-8') as f:
        lines = f.read()
        return lines

def write_log(line):
    with open(LATEST_LOG_PATH, 'a', encoding='UTF-8') as f:
        f.write(line + '\n')

def new_log():
    with open(LATEST_LOG_PATH, 'w', encoding='UTF-8') as f:
        f.write('')

def archive_log():
    date = time.strftime("%Y_%m_%d")
    latest_log = read_log()
    with open('log/' + date + '.log', 'a', encoding = 'UTF-8') as f:
        f.write(latest_log)