import os
import sys
import locale
import time
import io
import subprocess
import re

project_path = ''
license_path = ''
log_path = ''
added_paths:list=list()

def revert_std()->None:
    sys.stderr.flush()
    sys.stdout.flush()
    sys.stdout.close()
    sys.stderr.close()
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
    if logtype == 0: # just log
        sys.stdout.write("[{hours}:{minutes}:{seconds}] [LOG] {msg} \n".format(hours = cur_time.tm_hour, minutes = cur_time.tm_min, seconds = cur_time.tm_sec, msg = str_log))
        sys.stdout.flush()
        return
    if logtype == 1: # log error and raise exception
        sys.stderr.write("[{hours}:{minutes}:{seconds}] [ERROR] {msg} \n".format(hours = cur_time.tm_hour, minutes = cur_time.tm_min, seconds = cur_time.tm_sec, msg = str_log))
        revert_std()
        raise Exception(str_log)
    if logtype == 2: # log warning and continue
        sys.stdout.write("[{hours}:{minutes}:{seconds}] [WARN] {msg} \n".format(hours = cur_time.tm_hour, minutes = cur_time.tm_min, seconds = cur_time.tm_sec, msg = str_log))
        sys.stdout.flush()

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
                if head_tag.find('<!-- File: "') != -1 or head_tag.find('THE SOFTWARE IS PROVIDED "AS IS"') != -1:
                    result = True
        else:
            log(2, 'No <head> tag in ' + fname.name)
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

def process_license_in_file(p:subprocess.Popen, path:str, fname, ftype:int, comment_char_start:str, comment_char_end:str='')->None:
    std_out, std_err = p.communicate()
    if p.returncode != 0:
        log(1, std_err.strip().decode('utf-8'))
    licensed_file = fname
    if os.path.exists(licensed_file):
        handle = open(licensed_file, 'r')
        if not ensure_licensed(handle, comment_char_start):
            log(2, 'License file "{}" does not have license and will be deleted'.format(license_file))
            handle.close()
            os.remove(licensed_file)
        else:
            log(0, 'License for file "{}" already exists. Skipping...'.format(fname))
            handle.close()
            return
    with open(licensed_file, "w") as licensed:
        newline=False
        output = std_out.strip().decode('utf-8')
        license_filled:list[str] = output.split('\r')
        if len(license_filled) <= 1:
            license_filled.clear()
            license_filled = output.split('\n')
            newline=True
        f = open(path, 'r')
        if ftype != 1:
            first_line = True
            for line in license_filled:
                if newline:
                    line += '\n'
                if first_line and (comment_char_start == '/*' or comment_char_start == '#'):
                    f_line = f.readline()
                    if f_line.find('#!/') != -1: #check shebang
                        licensed.write(f_line)
                    first_line = False
                    if comment_char_start == '#':
                        line = '# ' + line
                        licensed.write(line.replace('\n', '\n# '))
                    else:
                        licensed.write(comment_char_start + ' ' + line)
                else:
                    if comment_char_start == '#':
                        licensed.write(line.replace('\n', '\n# '))
                    else:
                        licensed.write(line)
            if comment_char_end != '':
                licensed.write(comment_char_end + '\n')
            else: licensed.write('\n')
            licensed.write(f.read())
            f.close()
            licensed.flush()
            licensed.close()
        else:
            html_file:str = f.read(-1)
            head_idx = html_file.find("<head")
            if head_idx != -1:
                licensed_str = '<head ' + comment_char_start + ' '
                for line in license_filled:
                    licensed_str += line
                licensed_str += comment_char_end + '\n'
                html_file = html_file.replace("<head", licensed_str)
                licensed.write(html_file)
            licensed.flush()
            f.close()
            licensed.close()
        added_paths.append(path)
        log(0, 'Created licensed file "{}"'.format(licensed_file))

def try_add_license(fname)->None:
    ftype = get_file_type(fname)
    if is_licensed(fname, ftype) != True:
        comments = get_comment_by_type(ftype)
        remove_count = ftype == 0 and 4 or ftype == 1 and 5 or 3
        licensed_filename = fname.path[:len(fname.path)-remove_count] + "_licensed" + os.path.splitext(fname.name)[1]
        cmd = [sys.executable, "renderer.py",
               '--filename="{filename}"'.format(filename = licensed_filename),
               '--root_folder="{root_folder}"'.format(root_folder = project_path),
               '--year="{year}"'.format(year = str()),
               '--org_name="{org_name}"'.format(org_name = "StackSoft"),
               license_path]
        p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        #if ftype == 0:
        process_license_in_file(p, fname.path, licensed_filename, ftype, comments[0], comments[1])
        #else: 
        #    if ftype == 2:
        #        process_license_in_file(p, fname.path, licensed_filename, ftype, '#')
        #    else:
        #        if ftype == 1:
        #            process_license_in_file(p, fname.path, licensed_filename, ftype, '<!--', '-->')
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
    log_path = os.getcwd() + "/license.log"
    it = 0
    while it < len(sys.argv):
        arg = process_argument(sys.argv[it], sys.argv, it+1)
        it = it + 1
        if(arg == ''): exit(0)
        arg_pair = arg.split(' ')
        if(len(arg_pair) > 1):
            if(arg_pair[0] == '-f'):
                license_path = arg_pair[1]
                continue
            if(arg_pair[0] == '-l'):
                log_path = arg_pair[1]
                continue
        else:
            if arg_pair[0] == __file__: continue
            project_path = arg_pair[0]
            continue
    locale.setlocale(locale.LC_TIME, '')
    #logger = open(log_path, 'w')
    sys.stdout = sys.stderr = open(log_path, 'w')
    if license_path == '':
        license_file_path = os.getenv("LICENSE_FILE_PATH")
        if license_file_path == None or license_file_path == '':
            log(1, "License environment variable LICENSE_FILE_PATH required when -f parament not used. Exiting...")
        else:
            license_path = license_file_path
    if path_is_abs(license_path) == False:
        license_path = os.getcwd() + "/" + license_path
    if path_is_abs(log_path) == False:
        log_path = os.getcwd() + "/" + log_path
    log(0, "Log file initialized")
    if(is_all_paths_valid([project_path, license_path, log_path]) != True):
        log(1, 'One of the path parametrs missing or does not exist. Exiting...')
    process_license(project_path) # main recursive function
    log(0, "Total edited files: {}".format(len(added_paths)))
    revert_std()
