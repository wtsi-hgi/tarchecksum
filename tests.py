__author__ = 'ic4'

import unittest
import tarcheck
import os

TEST_FILES_BASE_PATH = 'test-cases'


class SameContentTestCase(unittest.TestCase):
    def test_checksum_and_compare(self):
        archive_path = 'test-cases/test-same-content/test-data.tar.bz2'
        dir_path = 'test-cases/test-same-content/test-data'
        total_files, errors = tarcheck.compare_checksum_of_all_archived_files_with_raw_files(archive_path, dir_path)
        self.assertEqual(total_files, 5)
        self.assertEqual(len(errors), 0)


class DiffContentTestCase(unittest.TestCase):
    def test_checksum_and_compare(self):
        """
        In this testcase the archive contains 2 files and 2 directories,
        while the actual directory contains 5 files and 2 directories.
        The test should fail because
        """
        archive_path = 'test-cases/test-diff-content/test-data.tar.bz2'
        dir_path = 'test-cases/test-diff-content/test-data'
        total_files, errors = tarcheck.compare_checksum_of_all_archived_files_with_raw_files(archive_path, dir_path)
        self.assertEqual(total_files, 5)
        self.assertEqual(len(errors), 1)


class FileMissingFromDirTestCase(unittest.TestCase):
    def test_checksum_and_compare(self):
        """
        In this test case I removed a file from the raw directory,
        but the files appears in the tar archive. We expect in this case
        that the function throws an exception because it has been asked to
        compare 2 different things - as in the directory contains less files
        than the archive.
        """
        archive_path = 'test-cases/test-files-missing/test-data.tar.bz2'
        dir_path = 'test-cases/test-files-missing/test-data'
        self.assertRaises(ValueError, tarcheck.compare_checksum_of_all_archived_files_with_raw_files, archive_path, dir_path)



class DereferencedSymlinksTestCase(unittest.TestCase):
    def test_checksum_and_compare(self):
        """
        In this test case I've created a tar from a directory that contained 1 symlink.
        I tared it up using -h option for dereferencing soft and hard links when archiving.
        It should be the same as without symlinks there, as according to the documentation
        of the tarfile symlinks are treated as regular files.
        """
        archive_path = 'test-cases/test-deref-links/test-data.tar.bz2'
        dir_path = 'test-cases/test-deref-links/test-data'
        total_files, errors = tarcheck.compare_checksum_of_all_archived_files_with_raw_files(archive_path, dir_path)
        self.assertEqual(total_files, 3)
        self.assertEqual(len(errors), 0)


@unittest.skip
class CompareLargeFilesTestCase(unittest.TestCase):
    def test_checksum_and_compare(self):
        """
        This test compares the contents of a tar containing a large file.
        It is mostly meant for checking on the memory consumption when the files are large.
        Otherwise should return everything ok - identical files in the tar and in the initial dir.
        """
        archive_path = 'test-cases/test-largebams/exp.tar.bz2'
        dir_path = 'test-cases/test-largebams/exp'
        total_files, errors = tarcheck.compare_checksum_of_all_archived_files_with_raw_files(archive_path, dir_path)
        self.assertEqual(total_files, 1)
        self.assertEqual(len(errors), 0)


class DirContentsArchivedWithoutParentDir(unittest.TestCase):

    def test_checksum_and_compare(self):
        """
        This test case compares the contents of an archive with the contents of a directory,
        without having the actual directory name in the relative paths of the files in the archive.
        """
        archive_path = 'test-cases/test-only-contents-archived/test-data.tar.bz2'
        dir_path = 'test-cases/test-only-contents-archived/test-data'
        total_files, errors = tarcheck.compare_checksum_of_all_archived_files_with_raw_files(archive_path, dir_path)
        self.assertEqual(total_files, 4)
        self.assertEqual(len(errors), 0)


class DirContentPermissionDenied(unittest.TestCase):

    def test_checksum_and_compare(self):
        archive_path = 'test-cases/test-no-permission/test-data.tar.bz2'
        dir_path = 'test-cases/test-no-permission/test-data'
        self.assertRaises(ValueError, tarcheck.compare_checksum_of_all_archived_files_with_raw_files, archive_path, dir_path)



class TestExcludeFiles(unittest.TestCase):

    def test_is_excluded1(self):
        wildcard = '*.jpg'
        self.assertTrue(tarcheck.is_excluded('photo.jpg', wildcard=wildcard))
        self.assertFalse(tarcheck.is_excluded('photo.txt', wildcard=wildcard))

    def test_is_excluded2(self):
        wildcard = '.snapshot'
        self.assertTrue(tarcheck.is_excluded('.snapshot', wildcard=wildcard))

    def test_is_excluded3(self):
        regex = 'sepi.[cr|b]am'
        self.assertFalse(tarcheck.is_excluded('.snapshot', regex=regex))
        self.assertFalse(tarcheck.is_excluded('*.sepi.cram', regex=regex))
        self.assertTrue(tarcheck.is_excluded('sepi.bam', regex=regex))


    def test_checksum_and_compare(self):
        archive_path = 'test-cases/test-excluded/test-data.tar.bz2'
        dir_path = 'test-cases/test-excluded/test-data2'
        total_files, errors = tarcheck.compare_checksum_of_all_archived_files_with_raw_files(archive_path, dir_path, exclude_wildcard='*.snap')
        #self.assertEqual(total_files, 4)
        self.assertEqual(len(errors), 0)


class TestGetAllFilesInDirRecursively(unittest.TestCase):
    '''
    Unit tests for `tarcheck.get_all_files_in_dir_recursively`.
    '''
    def test_with_empty_directory(self):
        self.__expect_files_in_directory([], 'empty')

    def test_with_flat_directory(self):
        self.__expect_files_in_directory(['1', '2', '3'], 'flat')

    def test_with_hierarchical_directory(self):
        self.__expect_files_in_directory(['1', 'a', 'b', 'a/2', 'a/3', 'b/4', 'a/c', 'a/c/5'], 'hierarchical')

    def __expect_files_in_directory(self, expected_files, directory_name):
        test_directory = os.path.join(TEST_FILES_BASE_PATH, 'test-get-all-files-in-dir-recursively', directory_name)
        files_list = tarcheck.get_all_files_in_dir_recursively(test_directory)
        self.assertItemsEqual(files_list, expected_files)


class TestGetAllFilesInArchive(unittest.TestCase):
    '''
    Unit tests for `tarcheck.get_all_files_in_archive`.
    '''
    def test_with_empty_archive(self):
        self.__expect_files_in_archive([], 'empty.tar.bz2')

    def test_with_flat_archive_directory(self):
        self.__expect_files_in_archive(['1', '2', '3'], 'flat.tar.bz2')

    def test_with_hierarchical_archive_directory(self):
        self.__expect_files_in_archive(['1', 'a', 'b', 'a/2', 'a/3', 'b/4', 'a/c', 'a/c/5'], 'hierarchical.tar.bz2')

    def __expect_files_in_archive(self, expected_files, archive_name):
        test_archive = os.path.join(TEST_FILES_BASE_PATH, 'test-get-all-files-in-archive', archive_name)
        files_list = tarcheck.get_all_files_in_archive(test_archive)
        self.assertItemsEqual(files_list, expected_files)


class TestGetFilesInDirectoryNotInArchive(unittest.TestCase):
    '''
    Unit tests for `tarcheck.get_files_in_directory_not_in_archive`.
    '''
    def test_with_empty_archive_no_difference(self):
        self.__expect_given_difference_between_files_in_directory_to_files_in_archive(
            'empty.tar.bz2', 'empty', [])

    def test_with_flat_archive_directory_no_difference(self):
        self.__expect_given_difference_between_files_in_directory_to_files_in_archive(
            'flat.tar.bz2', 'flat', [])

    def test_with_hierarchical_archive_directory_no_difference(self):
        self.__expect_given_difference_between_files_in_directory_to_files_in_archive(
            'hierarchical.tar.bz2', 'hierarchical', [])

    def test_with_flat_archive_directory_with_more_files_in_directory(self):
        self.__expect_given_difference_between_files_in_directory_to_files_in_archive(
            'flat.tar.bz2', 'flat-with-more', ['4', '5'])

    def test_with_hierarchical_archive_directory_with_more_files_in_directory(self):
        self.__expect_given_difference_between_files_in_directory_to_files_in_archive(
            'hierarchical.tar.bz2', 'hierarchical-with-more', ['6', 'b/7', 'a/c/d', 'a/c/d/8'])

    def __expect_given_difference_between_files_in_directory_to_files_in_archive(
            self, archive_name, directory_name, expected_difference):
        test_folder = 'test-get-files-in-directory-not-in-archive'
        test_directory = os.path.join(TEST_FILES_BASE_PATH, test_folder, directory_name)
        test_archive = os.path.join(TEST_FILES_BASE_PATH, test_folder, archive_name)
        difference = tarcheck.get_files_in_directory_not_in_archive(test_directory, test_archive)
        self.assertItemsEqual(difference, expected_difference)


if __name__ == '__main__':
    unittest.main()
