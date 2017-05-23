#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from shutil import rmtree
from tempfile import mkdtemp

from zope.interface.verify import verifyClass

from pydio.engine import sqlite, IDiffEngine


class TestEngine(TestCase):
    def test_IDiffEngine(self):
        verifyClass(IDiffEngine, sqlite.Engine)


class TestEngineState(TestCase):
    """Test state management"""

    def setUp(self):
        self.ws_local = mkdtemp()
        self.ws_remote = mkdtemp()

    def tearDown(self):
        rmtree(self.ws_local)
        rmtree(self.ws_remote)


class TestEngineDiff(TestCase):
    """Test diff generation"""

    def setUp(self):
        self.ws_local = mkdtemp()
        self.ws_remote = mkdtemp()

    def tearDown(self):
        rmtree(self.ws_local)
        rmtree(self.ws_remote)
