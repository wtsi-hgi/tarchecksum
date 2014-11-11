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
"""


import hashlib
import tarfile
import os
import argparse
import sys
import hashlib


def calculate_md5(file_obj, block_size=2 ** 20):
    #file_obj = open(file_path, 'rb')
    md5 = hashlib.md5()
    while True:
        data = file_obj.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()



def checksum_and_compare(archive_path, raw_dir_path):
    chunk_size = 100 * 1024
    files_md5_dict = {}
    tar = tarfile.open(name=archive_path, mode="r|*")
    for tar_info in tar:
        if not tar_info.isfile():
            continue
        extr_file = tar.extractfile(tar_info)

        # Checksum the tared up file:
        arch_file_md5 = calculate_md5(extr_file)

        # Checksum the raw file
        raw_file = open(os.path.join(raw_dir_path, tar_info.path))
        raw_file_md5 = calculate_md5(raw_file)

        # Compare md5s:
        if raw_file_md5 != arch_file_md5:
            print "ERROR -- md5s don't match! File="+tar_info.path+ " md5_raw_file="+raw_file_md5+" and md5_archived_file="+arch_file_md5
        tar.members = []


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tar_path', required=False, type=file, help='Path to the tar archive')
    parser.add_argument('--dir', required=False, type=file, help='Path to the directory that has been archived')

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

# args.dir = "/home/ic4/Work/Projects/tar_and_check/"
# args.tar_path = '/home/ic4/Work/Projects/tar_and_check/test-data.tar.bz2'

checksum_and_compare(args.tar_path, args.dir)




