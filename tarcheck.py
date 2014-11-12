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

This module has been written for checksumming all the files in a tar archive and comparing
the checksums against the ones of the original files. In case the md5 sums don't match,
there will be an error message outputted. Otherwise if all goes well, there is no message.

Example:

$python tarcheck.py --tar_path /path/to/archive/archive.tar.bz2 --dir /path/to/the/archived/dir


"""


import hashlib
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
    :param archive_path: str - The full path to the archive
    :param raw_dir_path: str - The full path to the archived directory
    :return: None
    """
    if not archive_path:
        raise ValueError("Missing path to the tar archive to checksum.")
    if not os.path.isdir(raw_dir_path):
        raise ValueError("The directory path to the raw data doesn't point to a directory")
    if not os.path.isabs(raw_dir_path):
        raise ValueError("The directory path must be absolute")

    raw_dir_parent = os.path.abspath(os.path.join(raw_dir_path, os.pardir))
    with tarfile.open(name=archive_path, mode="r|*") as tar:
        for tar_info in tar:
            if not tar_info.isfile():
                continue
            extr_file = tar.extractfile(tar_info)

            # Checksum the tared up file:
            arch_file_md5 = calculate_md5(extr_file)

            # Checksum the raw file
            tared_file_path = os.path.join(raw_dir_parent, tar_info.path)
            with open(tared_file_path) as raw_file:
                raw_file_md5 = calculate_md5(raw_file)


            # Compare md5s:
            if raw_file_md5 != arch_file_md5:
                print "ERROR -- md5s don't match! File="+tar_info.path+ " md5_raw_file="+raw_file_md5+" and md5_archived_file="+arch_file_md5
            tar.members = []


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


# Get args from user:
args = parse_args()

checksum_and_compare(args.tar_path, args.dir)




