#!/usr/bin/env python3
import os
import sys
import locale
import time
import io
import subprocess
from re import split

project_path = ''
license_path = ''
log_file:io.TextIOWrapper
added_paths:list=list()

def revert_std()->None:
    sys.stderr.close()
    sys.stdout.close()
    if log_file != None:
        log_file.close()
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

def get_comment_by_type(ftype:int)->tuple[str,str]:
    if ftype == 0:
        return ('/*','*/')
    if ftype == 1:
        return ('<!--','-->')
    if ftype == 2:
        return ('#','')
    return ('','')

def path_is_abs(p:str)->bool: return (len(p) > 1) and (p[0] == '/' or p[1] == ':')

def log(logtype:int, str_log:str)->None:
    cur_time = time.localtime()
    msg = "[{hours}:{minutes}:{seconds}] [{type}] {msg} \n".format(type = "LOG" if logtype == 0 else "ERROR" if logtype == 1 else "WARNING", hours = cur_time.tm_hour, minutes = cur_time.tm_min, seconds = cur_time.tm_sec, msg = str_log)
    if log_file != None:
        log_file.write(msg)
        log_file.flush()
    if logtype == 0 or logtype == 2: # just log
        sys.stdout.write(msg)
        sys.stdout.flush()
        return
    if logtype == 1: # log error and exit script
        sys.stderr.write(msg)
        sys.stderr.flush()
        revert_std()
        exit(1)

def is_all_paths_valid(paths:list[str])->bool:
    for path in paths:
        if path == None or path == '' or not os.path.exists(path):
            return False
    return True

def ensure_licensed(f:io.TextIOWrapper, comment_start:str='#')->bool:
    for line in f:
        if line.find(comment_start + ' File: "') != -1 or line.find('THE SOFTWARE IS PROVIDED "AS IS"') != -1: # try to find one of two lines of license
            return True
    return False

def is_licensed(fname, ftype: int)->bool:
    f = open(fname.path, "r", encoding="utf-8")
    result:bool = False
    if ftype == 0:
        result = ensure_licensed(f, '/*')
    if ftype == 1:
        html_file:str = f.read(-1)
        head_idx = html_file.find("<head")
        if head_idx != -1:
            head_tag = html_file[head_idx::]
            if head_tag.find("<!--") != -1:
                if head_tag.find('Copyright (c) ') != -1 or head_tag.find('THE SOFTWARE IS PROVIDED "AS IS"') != -1: # double check if any of license info is presented in file
                    result = True
        else: log(2, 'No <head> tag in ' + fname.name)
    else:
        first_line:str = f.readline()
        if first_line.startswith("#"):
            result = ensure_licensed(f)
    f.close()
    return result

def get_file_type(fname)->int:
    ext = os.path.splitext(fname.name)
    if ext[1] == ".css": return 0
    if ext[1] == ".html": return 1
    if ext[1] == ".sh" or ext[1] == ".py": return 2
    return -1

def process_license_in_file(p:subprocess.Popen, fname, ftype:int, comment_char_start:str, comment_char_end:str='')->None:
    std_out, std_err = p.communicate()
    if p.returncode != 0:
        log(1, std_err.strip().decode('utf-8'))
    try:
        with open(fname, "r+") as licensed:
            original_content = licensed.read()
            licensed.seek(0)
            output:str = std_out.strip().decode('utf-8')
            license_filled:list[str] = output.replace('\r', '').split('\n')
            if ftype != 1:
                first_line = True
                for line in license_filled:
                    if(len(line) > 1):
                        line += '\n'
                    else: line = '\n'
                    if first_line and (comment_char_start == '/*' or comment_char_start == '#'):
                        first_line = False
                        f_line = licensed.readline()
                        licensed.seek(0)
                        if f_line.find('#!/') != -1:
                            licensed.write(f_line.endswith('\n') and f_line or f_line+'\n')
                            original_content = original_content.replace(f_line, '')
                        licensed.write(comment_char_start + ' ' + line)
                    else:
                        if comment_char_start == '#':
                            if line != '\n':
                                line = '# ' + line;
                            else: line = '# \n'
                            licensed.write(line);
                        else: licensed.write(line)
                if comment_char_end != '':
                    licensed.write(comment_char_end + '\n')
                else: licensed.write('\n')
                licensed.write(original_content)
                licensed.flush()
            else:
                head_idx = original_content.find("<head")
                if head_idx != -1:
                    licensed_str = '<head ' + comment_char_start + '\n'
                    for line in license_filled:
                        licensed_str += line.endswith('\n') == True and line or (line + '\n')  
                    licensed_str += comment_char_end + '\n'
                    original_content = original_content.replace("<head", licensed_str)
                    licensed.write(original_content)
                licensed.flush()
            added_paths.append(fname)
            log(0, 'Added license in file "{}"'.format(fname))
    except PermissionError:
        log(2, "Can't edit file {} (Permission denied)".format(fname))


def try_add_license(fname)->None:
    ftype = get_file_type(fname)
    if ftype == 0 or ftype == 1 or ftype == 2:
        if is_licensed(fname, ftype) != True:
            comments = get_comment_by_type(ftype)
            cmd = ['sh', './render.sh',
                '--filename="{filename}"'.format(filename = os.path.normpath(fname.path)),
                '--root_folder="{root_folder}"'.format(root_folder = os.path.abspath(project_path)),
                '--year="{year}"'.format(year = str(2020)),
                '--org_name="{org_name}"'.format(org_name = "StackSoft"),
                license_path]
            try:
                p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
                process_license_in_file(p, fname.path, ftype, comments[0], comments[1])
            except FileNotFoundError:
                log(1, 'Module "sh" not found on this system. Exiting...')
        else: log(0, 'File "' + fname.name + '" already have license. Skipping...')

def process_license(dir_path:str)->None:
    dirs: list = list()
    files: list = list()
    with os.scandir(dir_path) as entries:
        for entry in entries:
            if entry.is_dir():
                list.append(dirs, entry)
                continue
            if entry.is_file():
                list.append(files, entry)
    for fname in files:
        try_add_license(fname)
    for directory in dirs:
        process_license(directory)

def process_argument(arg_key:str, args:list[str], it: int)->str:
    if arg_key != None and arg_key.startswith('-h'):
        log(0, 'Possible keys:\n-h = prints this message\n-f = path to license file, optional if LICENSE_FILE_PATH is set\n-l = path to log file, optional\npath to project, required')
        return ''
    if(arg_key == '-f' or arg_key == '-l'):
        return arg_key + ' ' + args[it]
    return arg_key

if __name__ == "__main__":
    default_log_path = os.path.normpath(os.getcwd() + "/license.log")
    log_path = ''
    it = 0
    while it < len(sys.argv):
        arg = process_argument(sys.argv[it], sys.argv, it+1)
        it += 1
        if(arg == ''): exit(0)
        arg_pair = arg.split(' ')
        if(arg_pair[0] == '-f'):
            it += 1
            license_path = arg_pair[1]
            continue
        if(arg_pair[0] == '-l'):
            it += 1
            log_path = arg_pair[1]
            continue
        if os.path.basename(arg_pair[0]) == os.path.basename(__file__): continue
        project_path = arg_pair[0]
        continue

    locale.setlocale(locale.LC_TIME, '')
    if not log_path:
        log_path = default_log_path
    try:
        if path_is_abs(log_path) == False:
            log_path = os.path.abspath(log_path)
        log_file = open(log_path, 'w')
        log(0, "Log file initialized")
    except IOError:
        log(2, "Can't open path {err_path}, trying using default {def_path}...".format(err_path = log_path, def_path = default_log_path))
        try:
            log_file = open(default_log_path, 'w')
            log(0, "Log file initialized")
        except IOError:
            log(2, 'Initializing log file failed')
    if license_path == '':
        license_file_path = os.getenv("LICENSE_FILE_PATH")
        if license_file_path == None or license_file_path == '':
            log(1, "License environment variable LICENSE_FILE_PATH required when -f parament not used. Exiting...")
        else: license_path = license_file_path
    if path_is_abs(license_path) == False:
        license_path = os.getcwd() + "/" + license_path
    
    if(is_all_paths_valid([project_path, license_path]) != True):
        log(1, 'One of the path parametrs missing or does not exist. Exiting...')
    process_license(project_path) # main recursive function
    log(0, "Total edited files: {}".format(len(added_paths)))
    revert_std()