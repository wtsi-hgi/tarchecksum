#! /usr/bin/env python

import argparse
import sys
import hashlib
import tarfile
import os

__author__ = 'ic4'



def calculate_md5(file_path, block_size=2 ** 20):
    file_obj = open(file_path, 'rb')
    md5 = hashlib.md5()
    while True:
        data = file_obj.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()


def checksum_in_archive(input_file):
    """
    input_file  - A FILE object to read the tar file from.
    hash - The name of the hash to use. Must be supported by hashlib.
    output_file - A FILE to write the computed signatures to.
    """
    if not input_file:
        raise ValueError("No input file given!")
    tar = tarfile.open(mode="r|*", name=input_file)

    print "WHat type is this? ", type(tar)
    chunk_size = 100 * 1024
    files_md5_dict = {}
    for member in tar:
        if not member.isfile():
            continue
        print "Type of file is: ", type(member)
        f = tar.extractfile(member)
        #h = hashlib.new('md5')
        h = hashlib.md5()
        data = f.read(chunk_size)
        while data:
            h.update(data)
            data = f.read(chunk_size)
        #output_file.write("%s  %s\n" % (h.hexdigest(), member.name))
        files_md5_dict[member.path] = h.hexdigest()
    print "In TARSUM - printing the returned dict: " + str(files_md5_dict)
    return files_md5_dict


def checksum_archive(archive_path):
    chunk_size = 100 * 1024
    files_md5_dict = {}
    tar = tarfile.open(name=archive_path, mode="r|*")
    for tar_info in tar:
        if not tar_info.isfile():
            continue
        extr_file = tar.extractfile(tar_info)
        print "TAR info:", str(tar_info.path)
        h = hashlib.md5()
        data = extr_file.read(chunk_size)
        while data:
            h.update(data)
            data = extr_file.read(chunk_size)
        print "EXTRACTED file: "+str(extr_file)
        files_md5_dict[tar_info.path] = h.hexdigest()
        tar.members = []
    return files_md5_dict

def print_fpaths(archive_path):
    tar = tarfile.open(name=archive_path, mode="r|*")
    for tar_info in tar:
        print "TAR info:", str(tar_info.path)



def checksum_all(file_paths):
    files_md5_dict = {}
    for f in file_paths:
        if os.path.isfile(f):
            files_md5_dict[f] = calculate_md5(f)
    return files_md5_dict

def compare_md5s(md5_dict1, md5_dict2):
    for fpath, md5 in md5_dict1:
        if md5_dict2[fpath] != md5:
            print "ERROR -- md5s differ: fpath="+fpath+" and md5="+md5



def get_list_of_files_in_archive(archive_path):
    tar = tarfile.open(archive_path)
    files = [f.path for f in tar.getmembers()]
    return files



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


# INPUT: archive, directory archived/list of files/...
#archive = '/home/ic4/Work/Projects/tar_and_check/test_archive.tar.bz2'


#archive = '/home/ic4/Work/Projects/tar_and_check/test-data.tar.bz2'
#unarchived_dir = "/home/ic4/Work/Projects/tar_and_check/"

args.dir = "/home/ic4/Work/Projects/tar_and_check/"
args.tar_path = '/home/ic4/Work/Projects/tar_and_check/test-data.tar.bz2'


files = get_list_of_files_in_archive(args.tar_path)
files = [os.path.join(args.dir, f) for f in files]

archived_files_md5s = checksum_archive(args.tar_path)
archived_files_md5_full_path = {os.path.join(args.dir, f) : md5 for f, md5 in archived_files_md5s.iteritems()}
non_archived_files_md5s = checksum_all(files)

print "ARCHIVED FILES:"
for f, md5 in archived_files_md5_full_path.iteritems():
    print "File: "+ f+" -- md5="+md5

print "NON ARCHIVED FILES: "
for f, md5 in non_archived_files_md5s.iteritems():
    print "File: "+ f+" -- md5="+md5






