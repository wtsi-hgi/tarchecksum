#! /usr/bin/env python
#from apport.hookutils import root_command_output

__author__ = 'ic4'

"""
#################################################################################
#
# Copyright (c) 2014 Genome Research Ltd.
#
# Author: Irina Colgiu <ic4@sanger.ac.uk>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

This module performs the checksums on all the files in a tar archive and compares them
against the checksums of the original files. In case the md5 sums don't match,
there will be an error message outputted.
The checksum on the archive members is done by streaming from the tar the list of members and their metadata,
and computing the md5 checksum on each member after extracting it.

Example:

$python tarcheck.py --tar_path /path/to/archive/archive.tar.bz2 --dir /path/to/the/archived/dir

where:
--tar_path (Required) is the path to the tar archive
--dir (Required) is the path to the directory that has been archived
It gives an error if there are files in the archive that can't be found in the directory
given as input.

It uses < 100MB memory to run.

"""


import tarfile
import os
import argparse
import sys
import hashlib
import fnmatch
import re


def calculate_md5(file_obj, block_size=2 ** 20):
    """
    :param file_obj: file - The file object to checksum
    :param block_size: int - The size of the blocks to be read and checksumed
    :return: checksum: string - The checksum as a string
    """
    if not file_obj:
        raise ValueError("Missing file argument!")
    md5 = hashlib.md5()
    while True:
        data = file_obj.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()


def is_excluded(string, wildcard=None, regex=None):
    if not wildcard and not regex:
        raise ValueError("No wildcard or regex provided => nothing to test")
    if wildcard:
        return fnmatch.fnmatch(string, wildcard)
    if regex:
        pattern = re.compile(regex)
        if pattern.match(string) is not None:
            return True
        return False


def compare_checksum_of_all_archived_files_with_raw_files(archive_path, dir_path, exclude_wildcard=None, exclude_regex=None):
    """
    :param archive_path: str - The path to the archive
    :param dir_path: str - The path to the archived directory
    :return: total_files, errors: int, list - The number of files found, a list of errors found
        in the archive and a list of files that differ from the raw version
    """
    if not archive_path:
        raise ValueError("Missing path to the tar archive to checksum.")
    if not os.path.isdir(dir_path):
        raise ValueError("The directory path to the raw data doesn't point to a directory")

    total_files = 0
    errors = []
    raw_dir_parent = os.path.abspath(os.path.join(dir_path, os.pardir))

    with tarfile.open(name=archive_path, mode="r|*") as tar:
        for tar_info in tar:
            if not tar_info.isfile():
                print "This is not a file - skipping checksum for: "+str(tar_info.path)
                continue
            if tar_info.issym():
                print "WARNING - This archive contains symlinks that aren't dereferenced!"+str(tar_info.path)
                continue

            # Exclude members
            if exclude_regex or exclude_wildcard:
                if is_excluded(tar_info.name, exclude_wildcard, exclude_regex):
                    continue

            # Pretending to extract each file - getting back a handle, but the file isn't actually extracted:
            archived_file_handle = tar.extractfile(tar_info)
            if not archived_file_handle:
                continue

            # Checksum the tared up file:
            archived_file_md5 = calculate_md5(archived_file_handle)

            # Trying to see if only the contents of the dir was archived or also the parent dir is in the archive:
            raw_file_path = os.path.abspath(os.path.join(dir_path, tar_info.path))
            if not os.path.exists(raw_file_path):
                raw_file_path = os.path.abspath(os.path.join(raw_dir_parent, tar_info.path))
                if not os.access(raw_file_path, os.R_OK):
                    err_msg = "ERROR: This user can't access all the files in this directory: "+str(raw_file_path)
                    raise ValueError(err_msg)
                if not os.path.isfile(raw_file_path):
                    err_msg = "ERROR: The directory given as input doesn't contain all the files in the archive: "+str(raw_file_path)
                    raise ValueError(err_msg)

            # Checksum the raw file
            with open(raw_file_path) as raw_file:
                raw_file_md5 = calculate_md5(raw_file)

            # Compare md5s:
            if raw_file_md5 != archived_file_md5:
                error = tar_info.path+ " "+raw_file_md5+" != "+archived_file_md5
                errors.append(error)
            tar.members = []
            total_files += 1
    return (total_files, errors)


def get_all_files_in_dir_recursively(dir_path):
    '''
    Returns a list of all files (including folders) in a given directory.
    :param dir_path: the directory for which files are to be found
    :return: a list of the paths for all files in directory, where paths are relative to dir_path
    '''
    print "DIR PATH: "+str(dir_path)
    files_list = []
    for dir_, _, files in os.walk(dir_path):
        for fname in files:
            #rel_dir = os.path.relpath(dir_, dir_path)
            print "var dir_ = "+str(dir_)
            rel_dir = os.path.relpath(dir_, dir_path)
            print "REL_dir = "+rel_dir
            rel_file = os.path.join(rel_dir, fname)
            print "REL_FILE = "+str(rel_file)
            files_list.append(rel_file)
            print "IN dir: "+rel_file
    return files_list


def get_all_files_in_archive(archive_path):
    '''
    Returns a list of all files (including folders) in a given archive.
    :param archive_path: the path to the archive in which files are to be found
    :return: a list of the paths for all files in the archive, where paths are relative to the root of the archive
    '''
    tar = tarfile.open(archive_path)
    files = [f.path for f in tar.getmembers()]
    for f in files:
        parent_dir = os.path.abspath(os.path.join(archive_path, os.pardir))
        rel_dir = os.path.relpath(archive_path, parent_dir)
        rel_file = os.path.join(rel_dir, f)
        print "in archive: "+rel_file
    return files


def get_files_in_directory_not_in_archive(dir_path, archive_path):
    '''
    Gets a list of what files in a give directory are not in a given archive.
    :param dir_path: the directory for which files are to be found and compared to those in the archive
    :param archive_path: the path to the archive in which files are to be found and compared to those in the directory
    :return: a list of files that are in the given directory but not in the given archive. Empty list if no difference
    '''
    files_in_dir = get_all_files_in_dir_recursively(dir_path)
    files_in_archive = get_all_files_in_archive(archive_path)
    return [x for x in files_in_dir if x not in files_in_archive]



# def get_all_files_in_dir_recursively(dir_path):
#     files_list = []
#     for (dir_name, _, files) in os.walk(dir_path):
#         for f in files:
#             path = os.path.join(dir, f)
#             files_list.append(path)


# for root, dirs, files in os.walk('/home/ic4/Downloads/'):
#     print "ROOT: " + str(root)
#     print "DIRS: " + str(dirs)
#     print "FILES: " + str(files)
#
# for (dir_name, _, files) in os.walk('/home/ic4/Downloads/'):
#     for f in files:
#         print os.path.join(dir_name, f)
#         # path = os.path.join(dir_name, f)
#         # print path
#         #path = os.path.join(dir, f)
#         #files_list.append(path)


def memory_usage():
    """Memory usage of the current process in kilobytes."""
    status = None
    result = {'peak': 0, 'rss': 0}
    try:
        # This will only work on systems with a /proc file system
        # (like Linux).
        status = open('/proc/self/status')
        for line in status:
            parts = line.split()
            key = parts[0][2:-1].lower()
            if key in result:
                result[key] = int(parts[1])
    finally:
        if status is not None:
            status.close()
    return result

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tar_path', required=True, help='Path to the tar archive')
    parser.add_argument('--dir', required=True, help='Path to the directory that has been archived')
    parser.add_argument('--exclude', required=False, help='A shell wildcard telling which files to exclude by name')
    parser.add_argument('--exclude_regex', required=False, help='A regex telling which files to exclude by name')


    try:
        args = parser.parse_args()
    except IOError as e:
        print e.strerror + ": " + e.filename
        parser.print_help()
        sys.exit(1)
    else:
        return args


if __name__ == '__main__':
    args = parse_args()
    try:
        total_files, errors = compare_checksum_of_all_archived_files_with_raw_files(args.tar_path, args.dir, args.exclude, args.exclude_regex)
        print "Total files in the archive: "+str(total_files)
        print "Number of files that differ between the archive and original: "+str(len(errors))
        if errors:
            print "FILES different:"
            for err in errors:
                print str(err)
    except ValueError as e:
        print e.message


