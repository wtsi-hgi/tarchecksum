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
import logging


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
        # No exclusion criteria, therefore not excluded
        return False
    if wildcard:
        return fnmatch.fnmatch(string, wildcard)
    if regex:
        pattern = re.compile(regex)
        if pattern.match(string) is not None:
            return True
        return False


def filter_excluded_from_list(list, exclude_wildcard=None, exclude_regex=None):
    """
    Filters excluded strings from the given list according to the given wildcard and regex exclusion rules.
    :param list: the list to filter
    :param exclude_wildcard: optional wildcard to strings from list
    :param exclude_regex: optional regex to strings from list
    :return: the filtered list
    """
    return [x for x in list if not is_excluded(x, exclude_wildcard, exclude_regex)]


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
                logging.info("This is not a file - skipping checksum for: %s" % tar_info.path)
                continue
            if tar_info.issym():
                logging.warning("This archive contains symlinks that aren't de-referenced: %s" % tar_info.path)
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
                    err_msg = "ERROR: This user can't access all the files in this directory: %s" % raw_file_path
                    raise ValueError(err_msg)
                if not os.path.isfile(raw_file_path):
                    err_msg = "ERROR: The directory given as input doesn't contain all the files in the archive: %s" % raw_file_path
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


def get_all_files_in_directory_recursively(directory_path):
    """
    Returns a list of all files (including folders) in a given directory.
    :param directory_path: the directory for which files are to be found
    :return: a list of the paths for all files in directory, where paths are relative to dir_path
    """
    relative_file_paths = []

    for root, directories, files in os.walk(directory_path):
        relative_directory = root.replace(directory_path, "")
        relative_directory = relative_directory.lstrip(os.sep)

        if root != directory_path:
            relative_file_paths.append(relative_directory)

        for file_name in files:
            relative_file_path = os.path.join(relative_directory, file_name)
            relative_file_paths.append(relative_file_path)

    return relative_file_paths


def get_all_files_in_archive(archive_path):
    """
    Returns a list of all files (including folders) in a given archive.
    :param archive_path: the path to the archive in which files are to be found
    :return: a list of the paths for all files in the archive, where paths are relative to the root of the archive
    """
    tar = tarfile.open(archive_path)
    files = [f.path.replace(archive_path, "") for f in tar.getmembers()]
    return files


def get_files_in_directory_not_in_archive(
        directory_path, archive_path, ignore_leading_directories_in_archive=0, exclude_wildcard=None, exclude_regex=None):
    """
    Gets a list of what files in a give directory are not in a given archive.
    Note: only considers the relative file paths - does not match the content of files
    :param directory_path: the directory for which files are to be found and compared to those in the archive
    :param archive_path: the path to the archive in which files are to be found and compared to those in the directory
    :param ignore_leading_directories_in_archive: ignores the leading n directories in the archive. Similar to
        --strip-components flag: http://www.gnu.org/software/tar/manual/html_section/tar_52.html#transform
    :param exclude_wildcard: optional wildcard to exclude certain files or folders
    :param exclude_regex: optional regex to exclude certain files or folders
    :return: a list of files that are in the given directory but not in the given archive. Empty list if no difference
    """
    files_in_dir = get_all_files_in_directory_recursively(directory_path)
    files_in_archive = get_all_files_in_archive(archive_path)

    # Strips n leading directories from all paths in archive, where n=archive_strip_components
    files_in_archive = [os.sep.join(x.split(os.sep)[ignore_leading_directories_in_archive:]) for x in files_in_archive]

    # Find files in directory but not in archive
    missing_files = [x for x in files_in_dir if x not in files_in_archive]

    # Apply filters
    missing_files = filter_excluded_from_list(missing_files, exclude_wildcard, exclude_regex)

    return missing_files


def memory_usage():
    """
    Memory usage of the current process in kilobytes.
    :return:
    """
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
    """
    Parses the arguments given via the command line.
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--tar_path', required=True, help='Path to the tar archive')
    parser.add_argument('--dir', required=True, help='Path to the directory that has been archived')
    parser.add_argument('--exclude', required=False, help='A shell wildcard telling which files to exclude by name')
    parser.add_argument('--exclude_regex', required=False, help='A regex telling which files to exclude by name')
    parser.add_argument('--log', required=False, help='Logging level, see: https://docs.python.org/2/howto/logging.html')

    try:
        args = parser.parse_args()
    except IOError as e:
        print "%s: %s" % (e.strerror, e.filename)
        parser.print_help()
        sys.exit(1)
    else:
        return args


def set_user_defined_logging_level(log_level):
    """
    Sets the logging level to that which the user defined in the given `log_level` argument
    :param log_level: the log level that the user defined
    """
    numeric_level = getattr(logging, log_level.upper(), None)

    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % log_level)

    logging.root.setLevel(numeric_level)


def report_files_in_directory_but_not_in_archive(
        directory_path, archive_path, exclude_wildcard=None, exclude_regex=None):
    """
    Creates a report of what files are in the given directory are not in the given archive (if any), considering any
    given exclusion criteria.
    :param directory_path: the directory for which files are to be found and compared to those in the archive
    :param archive_path: the path to the archive in which files are to be found and compared to those in the directory
    :param exclude_wildcard: optional wildcard to exclude certain files or folders
    :param exclude_regex: optional regex to exclude certain files or folders
    :return: report of what files are in the directory but not in the archive
    """
    files_in_directory = get_all_files_in_directory_recursively(directory_path)
    files_in_directory = filter_excluded_from_list(files_in_directory, exclude_wildcard=None, exclude_regex=None)

    archive_ignore_leading_directories = 0

    while archive_ignore_leading_directories <= 1:
        missing_files = get_files_in_directory_not_in_archive(
            directory_path, archive_path, archive_ignore_leading_directories, exclude_wildcard, exclude_regex)

        if len(missing_files) == 0:
            # All files in directory (minus excluded) were in archive
            return "All files in the directory are in the archive"

        elif len(missing_files) < len(files_in_directory):
            # A strict subset of the set of files in the directory are in the set of files in the archive
            return "Some files in directory are missing from the archive: %s" % missing_files

        else:
            # Maybe the tar file has more leading directories? i.e. everything parent/file, parent/folder/file
            archive_ignore_leading_directories += 1

    # All files are missing
    return "All files in the directory are missing from the archive: %s" % files_in_directory


if __name__ == '__main__':
    args = parse_args()

    if args.log:
        set_user_defined_logging_level(args.log)

    # Report files that are in the directory but are not in the archive
    print report_files_in_directory_but_not_in_archive(args.dir, args.tar_path, args.exclude, args.exclude_regex)

    try:
        total_files, errors = compare_checksum_of_all_archived_files_with_raw_files(
            args.tar_path, args.dir, args.exclude, args.exclude_regex)

        print "Total files in the archive: %s" % total_files
        print "Number of files that differ between the archive and original: %d" % len(errors)

        if errors:
            print "FILES different:"
            for err in errors:
                print str(err)

    except ValueError as e:
        print e.message



