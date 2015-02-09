__author__ = 'ic4'

import unittest
import tarcheck


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



if __name__ == '__main__':
    unittest.main()
