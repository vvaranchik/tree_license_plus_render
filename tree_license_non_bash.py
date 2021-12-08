#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
import pathlib
from argparse import ArgumentParser

FILENAME = 'tree_license'
COMMENTS_BY_EXTENSION = {
    '.sh': ('#', ''),
    '.py': ('#', ''),
    '.css': ('/*', '*/'),
    '.html': ('<!--', '-->')
}
ADDED_PATHS: list = list()


def add_license(license_template: str, path: pathlib.Path) -> None:
    try:
        comment = license_template[:2]
        with open(path, 'r', encoding='utf-8') as reader:
            content = reader.read()
        if '<!' in comment:
            if '<head' in content:
                for line in content.splitlines(True):
                    if '<head' in line:
                        content = content.replace('<head', '<head' + license_template)
                        break
        else:
            if '/*' in comment:
                content = license_template + content
            else:
                for line in content.splitlines(True):
                    if '#!/' in line:
                        content = content.replace(line, line + license_template)
                    else:
                        content = license_template + content
                    break
        with open(path, 'w', encoding='utf-8') as writer:
            writer.write(content)
        ADDED_PATHS.append(path)
        logging.getLogger(FILENAME).info(f'Added license in file "{path}"')
    except PermissionError:
        logging.getLogger(FILENAME).warning(f"Can't edit file '{path}' (Permission denied)")


def get_license_template(proc: subprocess.Popen, comment_start_char='', comment_end_char='') -> str:
    std_out, std_err = proc.communicate()
    if proc.returncode != 0:
        logging.getLogger(FILENAME).error(std_err.strip().decode('utf-8'))
        sys.exit(1)
    template_lines: list[str] = std_out.strip().decode('utf-8').replace('\r', '').split('\n')
    template = ''
    if comment_start_char != '<!--':
        first_line = True
        for line in template_lines:
            if len(line) > 1:
                line += '\n'
            else:
                line = '\n'
            if first_line:
                first_line = False
                if comment_start_char == '#':
                    template += comment_start_char + ' ' + line
                else:
                    template += comment_start_char + '\n' + line
            else:
                if comment_start_char == '#':
                    if line != '\n':
                        template += '# ' + line
                    else:
                        template += '# \n'
                else:
                    template += line
        if comment_end_char != '':
            template += comment_end_char + '\n'
        else:
            template += '\n'
    else:
        template += comment_start_char + '\n'
        for line in template_lines:
            template += line + '\n'
        template += comment_end_char + '\n'
    return template


def is_file_has_license(license_template: str, path: pathlib.Path) -> bool:
    tmp = ''
    with open(path, 'r', encoding="utf-8") as reader:
        for line in reader.read().replace('\r', '').split('\n'):
            tmp += line + '\n'
    return tmp.find(license_template) != -1


def try_add_license(path: pathlib.Path, comments: tuple[str, str]) -> None:
    cmd = [sys.executable, 'renderer.py',
           f'--filename="{path}"',
           f'--root_folder="{os.path.abspath(args.project_path)}"',
           '--year="2020"', '--org_name="StackSoft"', args.license_path]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    license_template = get_license_template(proc, comments[0], comments[1])
    if not is_file_has_license(license_template, path):
        add_license(license_template, path)
    else:
        logging.getLogger(FILENAME).info(f'File "{path}" already have license. Skipping...')


def process_license(dir_path: pathlib.Path) -> None:
    """Goes through all files and directories and trying add license in specified files

    Iterate every file and directory in given path and
    trying to add license if file match specified conditions

    Args:
        dir_path: Path to project where to start iterating
    """
    for path in pathlib.Path(dir_path).glob('*'):
        if path.is_file() and COMMENTS_BY_EXTENSION.get(os.path.splitext(path.name)[1]) is not None:
            try_add_license(path, COMMENTS_BY_EXTENSION.get(os.path.splitext(path.name)[1]))
            continue
        if path.is_dir():
            process_license(path)


def init_logger(file_path: str) -> None:
    logger = logging.getLogger(FILENAME)
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(file_path, 'w', 'utf-8')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s]: %(message)s', datefmt='%I:%M:%S')
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.info(f'Log initialized at {file_path}')


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-f', dest='license_path', metavar='/path/to/license',
                        default=os.getenv('LICENSE_FILE_PATH'),
                        type=str, help='optional, if "LICENSE_FILE_PATH" is set')
    parser.add_argument('-l', dest='log_path', metavar='/path/to/log',
                        default='./license.log', type=str, help='optional')
    parser.add_argument('project_path', metavar='/path/to/project', type=str, help='required')
    args = parser.parse_args()
    with pathlib.Path(args.log_path) as log_path:
        if not log_path.exists() and not log_path.parent.exists():
            init_logger('./license.log')
        else:
            init_logger(log_path.absolute())
    if not os.path.exists(args.project_path) or not os.path.exists(args.license_path):
        logging.getLogger(FILENAME).error('Project path or license file not exist. Exiting...')
        sys.exit(1)
    process_license(pathlib.Path(args.project_path))
    logging.getLogger(FILENAME).info(f'Edited files: {len(ADDED_PATHS)}')
