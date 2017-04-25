#! /usr/bin/env python
from unittest import TestCase

from watchdog.events import FileSystemMovedEvent

from pydio import job


# class TestFilters(TestCase):
#     """Test UNIX wildcard matching for include/exclude filters using
#     job.DEFAULT_BLACKLIST as a test case.
#     """
#
#     class MockHandler(object):
#         includes = job.DEFAULT_WHITELIST
#         excludes = job.DEFAULT_BLACKLIST
#
#         @job.filter_events
#         def mock_method(self, event):
#             return True
#
#     def test_expect_include(self):
#         expect_include = (
#             "file",
#             "file.txt",
#             "/path/to/some/file",
#             "/path/to/somefile.txt",
#             "relative/path/to/some/file.txt"
#         )
#         for path in expect_include:
#             self.assertFalse(
#                 job.match_any(job.DEFAULT_BLACKLIST, path),
#                 "False positive for `{0}`".format(path),
#             )
#
#     def test_expect_exclude(self):
#         expect_exclude = (
#             ".DS_Store",
#             "/path/to/.DS_Store",
#             "/path/to/some/hidden/.file",
#             "relative/path/to/hidden/.file",
#             "/path/to/.pydio_dl",
#             "relative/path/to.pydio_dl",
#             "something.DS_Store",
#             "file.tmp",
#             "/path/to/file.tmp",
#             "relative/path/to/file.tmp"
#         )
#         for path in expect_exclude:
#             self.assertTrue(
#                 job.match_any(job.DEFAULT_BLACKLIST, path),
#                 "False negative for `{0}`".format(path)
#             )
#
#     def test_filter_evets_pass(self):
#         m = self.MockHandler()
#         path = "file.txt"
#         ev = FileSystemMovedEvent("", path, is_directory=False)
#         self.assertTrue(
#             m.mock_method(ev),
#             "Path `{0}` should have been considered.".format(path),
#         )
#
#     def test_filter_events_fail(self):
#         m = self.MockHandler()
#         path = ".DS_Store"
#         ev = FileSystemMovedEvent("", path, is_directory=False)
#         self.assertIsNone(
#             m.mock_method(ev),
#             "Path `{0}` should have been ignored.".format(path),
#         )
