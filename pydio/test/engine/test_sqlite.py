#! /usr/bin/env python
from twisted.trial.unittest import TestCase

import os.path as osp
from pickle import dumps
from os import stat, mkdir

from twisted.internet import defer
from twisted.internet import task, reactor

from zope.interface.verify import verifyClass, verifyObject

from pydio.util.adbapi import ConnectionManager
from pydio.engine import sqlite, IDiffEngine, IStateManager, IDiffStream


def mk_dummy_inode(path, isdir=False):
    return {
        "node_path": path,
        "bytesize": 1024,
        "mtime": 187923.0,
        "stat_result": b"this is binary data",
        "md5": "directory" if isdir else "d41d8cd98f00b204e9800998ecf8427e",
    }


class TestEngine(TestCase):
    def setUp(self):
        self.engine = sqlite.Engine(":memory:")

    def test_IDiffEngine(self):
        verifyClass(IDiffEngine, sqlite.Engine)

    def test_updater(self):
        verifyObject(IStateManager, self.engine.updater)

    def test_stream(self):
        verifyObject(IDiffStream, self.engine.stream)


class TestStateManager(TestCase):
    def test_IStateManager(self):
        verifyClass(IStateManager, sqlite.StateManager)


class TestDiffStream(TestCase):
    def test_IDIffStream(self):
        verifyClass(IDiffStream, sqlite.DiffStream)


class TestStateManagement(TestCase):
    """Test state management"""

    def setUp(self):
        self.db = ConnectionManager(":memory:")
        self.stateman = sqlite.StateManager(self.db)

        with open(sqlite.SQL_INIT_FILE) as f:
            script = f.read()

        self.d = self.db.runInteraction(lambda c, s: c.executescript(s), script)

    def tearDown(self):
        self.db.close()

    @defer.inlineCallbacks
    def test_db_clean(self):
        """Canary test to ensure that the db is initialized in a blank state"""

        yield self.d  # wait for the db to be initialized

        q = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        for table in ("ajxp_index", "ajxp_changes"):
            res = yield self.db.runQuery(q, (table,))
            self.assertTrue(
                len(res) == 1,
                "table {0} does not exist".format(table)
            )

    @defer.inlineCallbacks
    def test_inode_create_file(self):
        yield self.d

        inode = mk_dummy_inode("/path/to/file.txt")
        yield self.stateman.create(inode, directory=False)

        entry = yield self.db.runQuery("SELECT * FROM ajxp_index")
        emsg = "got {0} results, expected 1.  Are canary tests failing?"
        lentry = len(entry)
        self.assertTrue(lentry == 1, emsg.format(lentry))

    @defer.inlineCallbacks
    def test_inode_create_dir(self):
        yield self.d

        inode = mk_dummy_inode("/dir/", isdir=True)
        yield self.stateman.create(inode, directory=True)

        entry = yield self.db.runQuery("SELECT * FROM ajxp_index")
        emsg = "got {0} results, expected 1.  Are canary tests failing?"
        lentry = len(entry)
        self.assertTrue(lentry == 1, emsg.format(lentry))

    @defer.inlineCallbacks
    def test_inode_delete_file(self):
        yield self.d

        inode = mk_dummy_inode("/path/to/file.txt")
        yield self.stateman.create(inode, directory=False)
        yield self.stateman.delete(inode, directory=False)

        path_pattern = inode["node_path"] + "%"
        rows = yield self.db.runQuery(
            "SELECT * FROM ajxp_index WHERE node_path LIKE ?;",
            (path_pattern,),
        )

        self.assertFalse(rows, "failed or incomplete deletion")

    @defer.inlineCallbacks
    def test_inode_delete_dir(self):
        yield self.d

        inode = mk_dummy_inode("/dir/", isdir=True)
        yield self.stateman.create(inode, directory=True)
        yield self.stateman.delete(inode, directory=True)

        path_pattern = inode["node_path"] + "%"
        rows = yield self.db.runQuery(
            "SELECT * FROM ajxp_index WHERE node_path LIKE ?;",
            (path_pattern,),
        )

        self.assertFalse(rows, "failed or incomplete deletion")

    @defer.inlineCallbacks
    def test_inode_delete_subtree(self):
        yield self.d

        create_list = (
            ("/dir/", True),
            ("/dir/foo/", True),
            ("/dir/foo/bar/", True),
            ("/dir/foo/bar/baz.txt", False),
            ("/dir/foo/bar/qux.txt", False),
        )

        for path, is_dir in create_list:
            inode = mk_dummy_inode(path, isdir=is_dir)
            yield self.stateman.create(inode, directory=is_dir)

        yield self.stateman.delete(
            mk_dummy_inode("/dir/foo/", isdir=True),
            directory=True
        )

        # only /foo/ should remain

        path_pattern = "/dir%"
        rows = yield self.db.runQuery(
            "SELECT * FROM ajxp_index WHERE node_path LIKE ?;",
            (path_pattern,),
        )

        self.assertEquals(
            len(rows), 1,
            "expected 1 row, got {0}".format(len(rows))
          )

    @defer.inlineCallbacks
    def test_inode_modify_file(self):
        yield self.d

        path = "/path/to/file.txt"
        inode = mk_dummy_inode(path)
        yield self.stateman.create(inode, directory=False)

        inode["mtime"] += 1000
        inode["md5"] = "e9800998ecf8427ed41d8cd98f00b204"
        yield self.stateman.modify(inode, directory=False)

        (mtime, md5), = yield self.db.runQuery(
            "SELECT mtime, md5 FROM ajxp_index WHERE node_path=?;",
            (path,),
        )

        self.assertEqual(mtime, inode["mtime"])
        self.assertEqual(md5, inode["md5"])

    @defer.inlineCallbacks
    def test_inode_modify_dir(self):
        yield self.d


class TestDiffStreaming(TestCase):
    """Test diff streaming"""
