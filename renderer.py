import os;
import sys;
import io;

_fname = '""'
_year = '""'
_root_folder = '""'
_org_name = '""'
license = ''

def process_args(arg_key:str, args:list[str], it: int):
    if(arg_key.startswith('--')):
        return arg_key + ' ' + args[it]
    return arg_key

if __name__ == "__main__":
    it = 0
    while it < len(sys.argv):
        arg = process_args(sys.argv[it], sys.argv, it+1)
        it = it + 1
        if(arg == ''): exit(0)
        arg_pair = arg.split('=')
        if(len(arg_pair) > 1):
            targ = arg_pair[0]
            if(targ == '--filename'):
                _fname = arg_pair[1].split(" ")[0]
                continue
            if(targ == '--year'):
                _year = arg_pair[1].split(" ")[0]
                continue
            if(targ == '--org_name'):
                _org_name = arg_pair[1].split(" ")[0]
                continue
            if(targ == "--root_folder"):
                _root_folder = arg_pair[1].split(" ")[0]
                continue
        else:
            if(arg_pair[0] == os.path.basename(__file__)): 
                continue;
            if os.path.exists(arg_pair[0]):
                with open(arg_pair[0], "r", encoding="utf-8") as f:
                    for line in f:
                        license += line
                #f.close()
    if license == '':
        sys.stderr.write('No license file found. Exiting...')
        exit(1)
    #print(license.format(filename = _fname, root_folder = _root_folder, year = _year, org_name = _org_name).replace('$', ''))
    sys.stdout.write(license.format(filename = _fname, root_folder = _root_folder, year = _year, org_name = _org_name).replace('$', ''));
