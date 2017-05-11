#! /usr/bin/env python
from twisted.trial.unittest import TestCase

import os.path as osp
from shutil import rmtree
from tempfile import mkdtemp

from pydio.workspace import ISynchronizable, local
from pydio.workspace.local.sqlite import SQLiteEngine

ENGINE_SQL_INIT_FILE = osp.join(
    osp.dirname(osp.dirname(osp.dirname(__file__))),
    "rsc/sql/create_pydio.sql"
)


class TestResources(TestCase):
    def test_sql_init_file_exists(self):
        self.assertTrue(osp.exists(ENGINE_SQL_INIT_FILE),
                        "could not fine create_pydio.sql")


class TestISynchronizable(TestCase):
    def test_Directory(self):
        self.assertTrue(
            ISynchronizable.implementedBy(local.Directory),
            "Directory does not implement ISynchronizable",
        )


class TestDirectory(TestCase):
    def setUp(self):
        self.path = mkdtemp(prefix="pydio_test")
        self.ws = local.Directory(
            SQLiteEngine(ENGINE_SQL_INIT_FILE),
            target_dir=self.path
        )
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
