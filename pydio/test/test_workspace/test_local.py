#! /usr/bin/env python
from twisted.trial.unittest import TestCase

import os.path as osp
from shutil import rmtree
from tempfile import mkdtemp

from zope.interface import implementer
from zope.interface.verify import DoesNotImplement

from twisted.application.service import Service

from pydio.workspace import ISynchronizable, local
from pydio.workspace.local.sqlite import Engine


class DummyEngine(Service):
    updater = None
    stream = None


class TestISynchronizable(TestCase):
    def test_Directory(self):
        self.assertTrue(
            ISynchronizable.implementedBy(local.Directory),
            "Directory does not implement ISynchronizable",
        )

class TestDirectoryEnforceInterfaces(TestCase):

    engine = DummyEngine()

    def test_enforce_local(self):
        self.assertRaises(
            DoesNotImplement,
            local.Directory,
            self.engine, "", {},
        )


class TestDirectory(TestCase):
    def setUp(self):
        self.path = mkdtemp(prefix="pydio_test")
        self.ws = local.Directory(Engine(), target_dir=self.path)
        return self.ws.startService()

    def tearDown(self):
        self.ws.stopService()
        self.ws = None
        rmtree(self.path)

    def test_dir(self):
        self.assertEqual(self.ws.dir, self.path, "path improperly set/reported")

    def test_assert_ready(self):
        return self.ws.assert_ready()

    def test_assert_ready_fail(self):
        self.ws._dir = "/does/not/exist"
        self.assertFailure(self.ws.assert_ready())
