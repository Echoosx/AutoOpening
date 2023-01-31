def write_concat(path,list):
    with open(path, 'w', encoding='UTF-8') as f:
        f.writelines(list)
