#! /usr/bin/env python
from unittest import TestCase
from pydio import job

class TestMatchAny(TestCase):
    """Test UNIX wildcard matching for include/exclude filters using
    job.DEFAULT_BLACKLIST as a test case.
    """

    def test_expect_include(self):
        expect_include = (
            "file",
            "file.txt",
            "/path/to/some/file",
            "/path/to/somefile.txt",
            "relative/path/to/some/file.txt"
        )
        for path in expect_include:
            if job.match_any(job.DEFAULT_BLACKLIST, path):
                raise ValueError("False positive for `{0}`".format(path))

    def test_expect_exclude(self):
        expect_exclude = (
            ".DS_Store",
            "/path/to/.DS_Store",
            "/path/to/some/hidden/.file",
            "relative/path/to/hidden/.file",
            "/path/to/.pydio_dl",
            "relative/path/to.pydio_dl",
            "something.DS_Store",
            "file.tmp",
            "/path/to/file.tmp",
            "relative/path/to/file.tmp"
        )
        for path in expect_exclude:
            if not job.match_any(job.DEFAULT_BLACKLIST, path):
                raise ValueError("False negative for `{0}`".format(path))
