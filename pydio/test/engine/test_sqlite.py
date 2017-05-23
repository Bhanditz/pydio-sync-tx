#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from shutil import rmtree
from tempfile import mkdtemp

from zope.interface.verify import verifyClass

from pydio.engine import sqlite, IDiffEngine, IStateManager, IDiffStream


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
        self.ws_local = mkdtemp()
        self.ws_remote = mkdtemp()

    def tearDown(self):
        rmtree(self.ws_local)
        rmtree(self.ws_remote)

    def test_inode_create(self):
        pass


class TestDiffStreaming(TestCase):
    """Test diff streaming"""

    def setUp(self):
        self.ws_local = mkdtemp()
        self.ws_remote = mkdtemp()

    def tearDown(self):
        rmtree(self.ws_local)
        rmtree(self.ws_remote)
