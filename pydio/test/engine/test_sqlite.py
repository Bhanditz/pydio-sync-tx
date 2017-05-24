#! /usr/bin/env python
from twisted.trial.unittest import TestCase

import os.path as osp
from pickle import dumps
from shutil import rmtree
from os import stat, mkdir
from tempfile import mkdtemp

from twisted.internet import defer
from twisted.enterprise import adbapi

from zope.interface.verify import verifyClass

from pydio.engine import sqlite, IDiffEngine, IStateManager, IDiffStream


def mk_dummy_inode(path, isdir=False):
    return {
        "node_path": path,
        "bytesize": osp.getsize(path),
        "mtime": osp.getmtime(path),
        "stat_result": dumps(stat(path), protocol=4),
        "md5": "directory" if isdir else "d41d8cd98f00b204e9800998ecf8427e",
    }


class TestEngine(TestCase):
    def test_IDiffEngine(self):
        verifyClass(IDiffEngine, sqlite.Engine)


class TestStateManager(TestCase):
    def test_IStateManager(self):
        verifyClass(IStateManager, sqlite.StateManager)


class TestDiffStream(TestCase):
    def test_IDIffStream(self):
        verifyClass(IDiffStream, sqlite.DiffStream)


class TestStateManagement(TestCase):
    """Test state management"""

    def setUp(self):
        self.meta = mkdtemp()
        self.ws = mkdtemp()

        self.db = adbapi.ConnectionPool(
            "sqlite3", osp.join(self.meta, "db.sqlite"), check_same_thread=False,
        )
        self.stateman = sqlite.StateManager(self.db)

        # Initialize db, returning deferred
        # If this doesn't work, confirm that deferred chaining out of
        # t.t.unittest.TestCase.setUp works as expected

        # Yeah, yeah... it blocks... deal with it. </sunglasses>
        with open(sqlite.SQL_INIT_FILE) as f:
            script = f.read()

        return self.db.runInteraction(lambda c, s: c.executescript(s), script)

    def tearDown(self):
        self.db.close()
        del self.db
        del self.stateman

        rmtree(self.meta)
        rmtree(self.ws)

    @defer.inlineCallbacks
    def test_db_clean(self):
        """Canary test to ensure that the db is initialized in a blank state"""

        res = yield self.db.runQuery("SELECT * FROM ajxp_index LIMIT 1")
        self.assertFalse(res, "dirty test:  table `ajxp_index` is not empty")

        res = yield self.db.runQuery("SELECT * FROM ajxp_changes LIMIT 1")
        self.assertFalse(res, "dirty test:  table `ajxp_changes` is not empty")

    @defer.inlineCallbacks
    def test_inode_create_file(self):
        path = osp.join(self.ws, "test.txt")
        with open(path, "wt") as f:
            pass

        inode = mk_dummy_inode(path)
        yield self.stateman.create(inode, directory=False)

        entry = yield self.db.runQuery("SELECT * FROM ajxp_index")
        emsg = "got {0} results, expected 1.  Are canary tests failing?"
        lentry = len(entry)
        self.assertTrue(lentry == 1, emsg.format(lentry))

    @defer.inlineCallbacks
    def test_inode_create_dir(self):
        path = osp.join(self.ws, "tests")
        mkdir(path)

        inode = mk_dummy_inode(path, isdir=True)
        yield self.stateman.create(inode, directory=True)

        entry = yield self.db.runQuery("SELECT * FROM ajxp_index")
        emsg = "got {0} results, expected 1.  Are canary tests failing?"
        lentry = len(entry)
        self.assertTrue(lentry == 1, emsg.format(lentry))


class TestDiffStreaming(TestCase):
    """Test diff streaming"""
