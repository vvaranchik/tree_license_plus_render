import os;
import sys;
import io;

_fname = '""'
_year = '""'
_root_folder = '""'
_org_name = '""'
_lic_fname = ''
license = ''

def process_args(arg_key:str, args:list[str], it: int)->str:
    if(arg_key.startswith('--')):
        return arg_key + ' ' + args[it]
    return arg_key

def check_var():
    global _fname, _year, _root_folder, _org_name
    if _fname.find(_lic_fname) != -1:
        _fname = _fname.replace(_lic_fname, '')
        return
    if _year.find(_lic_fname) != -1:
        _year = _year.replace(_lic_fname, '')
        return
    if _root_folder.find(_lic_fname) != -1:
        _root_folder = _root_folder.replace(_lic_fname, '')
        return
    if _org_name.find(_lic_fname) != -1:
        _org_name = _org_name.replace(_lic_fname, '')
        return

if __name__ == "__main__":
    it = 0
    full_args_str=''
    while it < len(sys.argv):
        full_args_str += sys.argv[it] + ' '
        arg = process_args(sys.argv[it], sys.argv, it+1)
        it += 1
        if(arg == ''): exit(0)
        arg_pair = arg.split('=')
        if(len(arg_pair) > 1):
            targ = arg_pair[0]
            if(targ == '--filename'):
                _fname = arg_pair[1].split("--")[0]
                continue
            if(targ == '--year'):
                _year = arg_pair[1].split("--")[0]
                continue
            if(targ == '--org_name'):
                _org_name = arg_pair[1].split("--")[0]
                continue
            if(targ == "--root_folder"):
                _root_folder = arg_pair[1].split("--")[0]
                continue
        else:
            if(os.path.basename(arg_pair[0]) == os.path.basename(__file__)): 
                continue
            _lic_fname = arg_pair[0]
            if os.path.exists(arg_pair[0]):
                with open(arg_pair[0], "r", encoding="utf-8") as f:
                    license = f.read()
    check_var()
    if license == '':
        sys.stderr.write('No license file found. Exiting...')
        exit(1)
    sys.stdout.write(license.format(filename = _fname, root_folder = _root_folder, year = _year, org_name = _org_name).replace('$', ''))
