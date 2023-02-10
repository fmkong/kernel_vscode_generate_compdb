#!/usr/bin/env python3

from __future__ import print_function, division

import argparse
import fnmatch
import functools
import json
import math
import multiprocessing
import os
import re
import sys
import logging

__version__ = "0.1.1"

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter(
    fmt='%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

CMD_VAR_RE = re.compile(r'^\s*cmd_(\S+)\s*:=\s*(.+)\s*$', re.MULTILINE)
SOURCE_VAR_RE = re.compile(r'^\s*source_(\S+)\s*:=\s*(.+)\s*$', re.MULTILINE)


def print_progress_bar(progress):
    progress_bar = '[' + '|' * \
        int(50 * progress) + '-' * int(50 * (1.0 - progress)) + ']'
    print('\r', progress_bar, "{0:.1%}".format(progress), end='\r')


def parse_cmd_file(android_root, docker_android_root, output_dir, cmdfile_path):
    if docker_android_root:
        docker_dir_replace = os.path.abspath(docker_android_root) + "/"
    else:
        docker_dir_replace = os.path.abspath(android_root) + "/"
    with open(cmdfile_path, 'r') as cmdfile:
        cmdfile_content = cmdfile.read()

    commands = {match.group(1): match.group(2)
                for match in CMD_VAR_RE.finditer(cmdfile_content)}
    sources = {match.group(1): match.group(2)
               for match in SOURCE_VAR_RE.finditer(cmdfile_content)}

    return [{
            'directory': android_root,
            'command': commands[o_file_name].replace(docker_dir_replace, "")\
                .replace("./", output_dir)\
                .replace(o_file_name, os.path.join(output_dir, o_file_name))\
                .replace("-Wp,-MD,", "-Wp,-MD," + output_dir)\
                .replace('\\\"', '\"'),
            'file': source.replace(docker_dir_replace, ""),
            'output': os.path.join(output_dir, o_file_name)
            } for o_file_name, source in sources.items()]


def gen_compile_commands(target, android_root, docker_android_root):
    logging.info("Building *.o.cmd file list...")
    logging.info(
        "The out dir where contains the obj of target is '%s'" % (android_root))
    android_root = os.path.abspath(android_root)

    output_dir = format("out/target/product/%s/obj/KERNEL_OBJ/" % (target))
    cmd_file_search_path = [os.path.join(android_root, output_dir)]
    logging.info("Searching *.o.cmd from path %s..." % (cmd_file_search_path))
    cmd_files = []
    for search_path in cmd_file_search_path:
        if (os.path.isdir(search_path)):
            for cur_dir, subdir, files in os.walk(search_path):
                cmd_files.extend(os.path.join(cur_dir, cmdfile_name)
                                 for cmdfile_name in fnmatch.filter(files, '*.o.cmd'))
        else:
            cmd_files.extend(search_path)

    if not cmd_files:
        logging.info("No *.o.cmd files found in",
                     ", ".join(cmd_file_search_path))
        return

    logging.info("Parsing *.o.cmd files...")

    n_processed = 0
    print_progress_bar(0)

    compdb = []
    pool = multiprocessing.Pool()
    try:
        for compdb_chunk in pool.imap_unordered(functools.partial(parse_cmd_file, android_root, docker_android_root, output_dir), cmd_files, chunksize=int(math.sqrt(len(cmd_files)))):
            compdb.extend(compdb_chunk)
            n_processed += 1
            print_progress_bar(n_processed / len(cmd_files))

    finally:
        pool.terminate()
        pool.join()

    # logging.info(compdb)
    logging.info("Writing compile_commands.json...")

    with open('../compile_commands.json', 'w') as compdb_file:
        json.dump(compdb, compdb_file, indent=1)


def main():
    parser = argparse.ArgumentParser(
        description='Generate compile_commands.json for kernel')
    parser.add_argument('--version', action='version',
                        version='%(prog)s '+__version__)
    parser.add_argument('--target', help='build target')
    parser.add_argument('--android_root', help='android root dir in host PC')
    parser.add_argument('--docker_android_root',
                        help='the android root dir in docker build env')
    args = parser.parse_args()

    if not args.target:
        logging.error("no target")
        exit(-2)
    if not args.android_root:
        logging.error("no android root dir")
        exit(-3)

    gen_compile_commands(args.target, args.android_root,
                         args.docker_android_root)


if __name__ == '__main__':
    ret = 0
    try:
        ret = main()
    except Exception as e:
        logging.error('Unexpected error:' + str(sys.exc_info()[0]))
        logging.exception(e)
    sys.exit(ret)
