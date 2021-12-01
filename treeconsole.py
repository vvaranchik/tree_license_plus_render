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

def path_is_abs(p)->bool: return (len(p) > 1) and (p[0] == '/' or p[1] == ':')

def log(logtype:int, str_log:str)->None:
    cur_time = time.localtime()
    if logtype == 0: # just log
        sys.stdout.write("[{hours}:{minutes}:{seconds}] [LOG] {msg} \n".format(hours = cur_time.tm_hour, minutes = cur_time.tm_min, seconds = cur_time.tm_sec, msg = str_log));
        sys.stdout.flush();
        sys.stderr.flush();
        return
    if logtype == 1: # log error and raise exception
        sys.stderr.write("[{hours}:{minutes}:{seconds}] [ERROR] {msg} \n".format(hours = cur_time.tm_hour, minutes = cur_time.tm_min, seconds = cur_time.tm_sec, msg = str_log));
        sys.stderr.flush();
        sys.stdout.close()
        sys.stderr.close();
        raise Exception(str_log)
    if logtype == 2: # log warning and continue
        sys.stderr.write("[{hours}:{minutes}:{seconds}] [WARN] {msg} \n".format(hours = cur_time.tm_hour, minutes = cur_time.tm_min, seconds = cur_time.tm_sec, msg = str_log));
        sys.stderr.flush();
        sys.stdout.close()

def is_all_paths_valid(paths:list[str])->bool:
    for path in paths:
        if path == None or path == '':
            return False;
            #if is_path_dir_or_file(path):
            #    return True;
        return os.path.exists(path)
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
        #first_line:str = f.readline()
        #if first_line.startswith('/*'):
        result = ensure_licensed(f, '/*')
        #return False
    if ftype == 1:
        html_file:str = f.read(-1)
        head_idx = html_file.find("<head")
        if head_idx != -1:
            head_tag = html_file[head_idx::]
            if head_tag.find("<!--") != -1:
                #f.close()
                #return True;
                if head_tag.find('<!-- File: "') != -1 or head_tag.find('THE SOFTWARE IS PROVIDED "AS IS"') != -1:
                    result = True
            #f.close()
            #return False;
        else: 
            #f.close()
            log(2, 'No <head> tag in ' + fname.name)
            #return False
    else:
        first_line:str = f.readline()
        if first_line.startswith("#"):
            #f.close()
            #return True
            result = ensure_licensed(f)
        #f.close()
        #return False
    f.close()
    return result
    
def get_file_type(fname)->int:
    ext = os.path.splitext(fname.name)
    if ext[1] == ".css": return 0
    if ext[1] == ".html": return 1
    if ext[1] == ".sh" or ext[1] == ".py": return 2
    return -1

def process_license_in_file(p:subprocess.Popen, path:str, fname, ftype:int, comment_char_start:str='', comment_char_end:str='')->None:
    std_out, std_err = p.communicate(timeout=5)
    if p.returncode != 0:
        log(1, std_err.strip().decode('utf-8'))
    licensed_file = fname
    if os.path.exists(licensed_file):
        log(0, 'License for file "{}" already exists. Skipping...'.format(fname))
        return
    with open(licensed_file, "w") as licensed:
        license_filled:list[str] = std_out.strip().decode('utf-8').split('\r')
        #print(license_filled)
        f = open(path, 'r')
        if ftype != 1:
            first_line = True
            for line in license_filled:
                if first_line and (comment_char_start == '/*' or comment_char_start == '#'):
                    f_line = f.readline()
                    if f_line.find('#!') != -1:
                        licensed.write(f_line)
                    first_line = False
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
            #print('>> ' + line.rstrip().decode("utf-8"))
        else:
            f = open(path, 'r')
            html_file:str = f.read(-1)
            head_idx = html_file.find("<head")
            if head_idx != -1:
                licensed_str = '<head ' + comment_char_start + ' '
                #for line in iter(p.stdout.readline, b''):
                #for line in iter(std_out.readline, b''):
                for line in license_filled:
                    licensed_str += line
                licensed_str += comment_char_end + '\n'
                html_file = html_file.replace("<head", licensed_str)
                #html_file[head_idx] += comment_char_start
                licensed.write(html_file)
            licensed.flush()
            f.close()
            licensed.close()
        added_paths.append(path)
        log(0, 'Created licensed file "{}"'.format(licensed_file))

def try_add_license(fname)->None:
    ftype = get_file_type(fname)
    if is_licensed(fname, ftype) != True:
        #os.system('python renderer.py --filename="{filename}" --root_folder="{root_folder}" --year="{year}" --org_name="{org_name}" {license_file_path}'.format(filename = fname.path, root_folder = project_path, year = str(2021), org_name = "StackSoft", license_file_path = license_path) )
        remove_count = ftype == 0 and 4 or ftype == 1 and 5 or 3
        licensed_filename = fname.path[:len(fname.path)-remove_count] + "_licensed" + os.path.splitext(fname.name)[1]
        cmd = [sys.executable, "renderer.py",
               '--filename="{filename}"'.format(filename = licensed_filename),
               '--root_folder="{root_folder}"'.format(root_folder = project_path),
               '--year="{year}"'.format(year = str()),
               '--org_name="{org_name}"'.format(org_name = "StackSoft"),
               license_path]
        p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        if ftype == 0:
            #licensed.write('/*\n')
            process_license_in_file(p, fname.path, licensed_filename, ftype, '/*', '*/');
        else: 
            if ftype == 2:
                process_license_in_file(p, fname.path, licensed_filename, ftype, '#');
            else:
                if ftype == 1:
                    process_license_in_file(p, fname.path, licensed_filename, ftype, '<!--', '-->');
            #print('>> ' + line.rstrip().decode("utf-8"))
        #edited_lists.append(0)
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
    log_path = os.getcwd() + "\license.log"
    it = 0
    while it < len(sys.argv):
        arg = process_argument(sys.argv[it], sys.argv, it+1)
        it = it + 1
        if(arg == ''): exit(0)
        arg_pair = arg.split(' ')
        if(len(arg_pair) > 1):
            if(arg_pair[0] == '-f'):
                license_path = arg_pair[1];
                continue
            if(arg_pair[0] == '-l'):
                log_path = arg_pair[1];
                continue
        else:
            project_path = arg_pair[0];
            continue
    locale.setlocale(locale.LC_TIME, '')
    logger = open(log_path, 'w')
    sys.stdout = logger
    sys.stderr = logger
    if license_path == '':
        license_file_path = os.getenv("LICENSE_FILE_PATH")
        if license_file_path == None or license_file_path == '':
            log(1, "License environment variable LICENSE_FILE_PATH required when -f parament not used. Exiting...")
        else:
            license_path = license_file_path
    if path_is_abs(license_path) == False:
        license_path = os.getcwd() + "/" + license_path;
    if path_is_abs(log_path) == False:
        log_path = os.getcwd() + "/" + log_path;
    log(0, "Log file initialized")
    if(is_all_paths_valid([project_path, license_path, log_path]) != True):
        log(1, 'One of the path parametrs missing or does not exist. Exiting...')
    process_license(project_path)
    #time.sleep(2)
    log(0, "Total edited files: {}".format(len(added_paths)))
    sys.stderr.close()
    sys.stdout.close()