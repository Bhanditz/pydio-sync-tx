#! /usr/bin/env python
from twisted.trial.unittest import TestCase

import os.path as osp
from pickle import dumps
from shutil import rmtree
from os import stat, mkdir
from tempfile import mkdtemp

from twisted.internet import defer
from twisted.enterprise import adbapi
from twisted.internet import task, reactor

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
            "sqlite3",
            osp.join(self.meta, "db.sqlite"),
            check_same_thread=False,
            cp_min=1,
            cp_max=1,
        )
        self.stateman = sqlite.StateManager(self.db)

        with open(sqlite.SQL_INIT_FILE) as f:
            script = f.read()

        self.d = self.db.runInteraction(lambda c, s: c.executescript(s), script)

    def tearDown(self):
        self.db.close()
        del self.db
        del self.stateman

        rmtree(self.meta)
        rmtree(self.ws)

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

        path = osp.join(self.ws, "test.txt")
        with open(path, "wt") as f:
            pass  # touch file

        inode = mk_dummy_inode(path)
        yield self.stateman.create(inode, directory=False)

        entry = yield self.db.runQuery("SELECT * FROM ajxp_index")
        emsg = "got {0} results, expected 1.  Are canary tests failing?"
        lentry = len(entry)
        self.assertTrue(lentry == 1, emsg.format(lentry))

    @defer.inlineCallbacks
    def test_inode_create_dir(self):
        yield self.d

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
