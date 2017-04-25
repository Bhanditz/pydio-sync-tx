#! /usr/bin/env python
from unittest import TestCase

from watchdog.events import FileSystemMovedEvent

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
            self.assertFalse(
                job.match_any(job.DEFAULT_BLACKLIST, path),
                "False positive for `{0}`".format(path),
            )

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
            self.assertTrue(
                job.match_any(job.DEFAULT_BLACKLIST, path),
                "False negative for `{0}`".format(path)
            )


class TestJobWithoutObserver(TestCase):
    """Effectuate tests for pydio.job.Job where an Observer instance (or stub)
    is not required.
    """
    def setUp(self):
        cfg = {"workspace": "", "directory": "", "server": ""}
        self.job = job.Job(None, "TestJob", cfg)

    def tearDown(self):
        del self.job

    def test_consider_event(self):
        path = "file.txt"
        ev = FileSystemMovedEvent("", path, is_directory=False)
        self.assertTrue(
            self.job.attend_to_event(ev),
            "Path `{0}` should have been considered.".format(path),
        )

    def test_ignor_event(self):
        path = ".DS_Store"
        ev = FileSystemMovedEvent("", path, is_directory=False)
        self.assertFalse(
            self.job.attend_to_event(ev),
            "Path `{0}` should have been ignored.".format(path),
        )
