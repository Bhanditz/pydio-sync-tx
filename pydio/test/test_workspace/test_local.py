#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from shutil import rmtree
from tempfile import mkdtemp

from pydio import ISynchronizable
from pydio.workspace import local


class TestISynchronizable(TestCase):
    def test_Directory(self):
        self.assertTrue(
            ISynchronizable.implementedBy(local.Directory),
            "Directory does not implement ISynchronizable",
        )


class TestDirectory(TestCase):
    def setUp(self):
        self.path = mkdtemp(prefix="pydio_test")
        self.ws = local.Directory(target_dir=self.path)

    def tearDown(self):
        self.ws = None
        rmtree(self.path)

    def test_dir(self):
        self.assertEqual(self.ws.dir, self.path, "path improperly set/reported")

    def test_assert_ready(self):
        return self.ws.assert_ready()

    def test_assert_ready_fail(self):
        self.ws._dir = "/does/not/exist"
        self.assertFailure(self.ws.assert_ready())
