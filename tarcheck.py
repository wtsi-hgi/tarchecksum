#! /usr/bin/env python

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



def checksum_and_compare(archive_path, raw_dir_path):
    """
    :param archive_path: str - The path to the archive
    :param raw_dir_path: str - The path to the archived directory
    :return: None
    """
    if not archive_path:
        raise ValueError("Missing path to the tar archive to checksum.")
    if not os.path.isdir(raw_dir_path):
        raise ValueError("The directory path to the raw data doesn't point to a directory")

    total_files = 0
    errors_list = []
    raw_dir_parent = os.path.abspath(os.path.join(raw_dir_path, os.pardir))
    with tarfile.open(name=archive_path, mode="r|*") as tar:
        for tar_info in tar:
            if not tar_info.isfile():
                continue

            # Extracting each file:
            extr_file = tar.extractfile(tar_info)
            if not extr_file:
                continue

            # Checksum the tared up file:
            arch_file_md5 = calculate_md5(extr_file)

            # Checksum the raw file
            raw_file_path = os.path.join(raw_dir_parent, tar_info.path)
            if not os.path.isfile(raw_file_path):
                err_msg = "The directory given as input doesn't contain all the files in the archive: "+str(raw_file_path)
                raise ValueError(err_msg)
            with open(raw_file_path) as raw_file:
                raw_file_md5 = calculate_md5(raw_file)

            # Compare md5s:
            if raw_file_md5 != arch_file_md5:
                error = "ERROR file="+tar_info.path+ " "+raw_file_md5+" != "+arch_file_md5
                errors_list.append(error)
            tar.members = []
            total_files += 1
    return (total_files, errors_list)

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
        total_files, errors = checksum_and_compare(args.tar_path, args.dir)
        print "Total files in the archive: "+str(total_files)
        print "Number of files that differ between the archive and original: "+str(len(errors))
        print "FILES different:"
        if errors:
            for err in errors:
                print str(err)
    except ValueError as e:
        print e.message
    print memory_usage()
    import resource
    print resource.getrusage(resource.RUSAGE_SELF).ru_maxrss





