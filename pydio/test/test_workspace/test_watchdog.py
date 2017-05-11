#! /usr/bin/env python
from functools import reduce
from tempfile import TemporaryDirectory
from twisted.trial.unittest import TestCase

from zope.interface import implementer
from zope.interface.verify import DoesNotImplement

from twisted.enterprise import adbapi
from twisted.application.service import Service

from pydio import IWatcher, IDiffHandler, ISelectiveEventHandler
from pydio.workspace import watchdog
from pydio.workspace.local import SQLiteStateManager


@implementer(IDiffHandler)
class DummyHandler(Service):
    def dispatch(self, ev):
        raise NotImplementedError

    def on_any_event(self, ev):
        raise NotImplementedError

    def on_created(self, ev):
        raise NotImplementedError

    def on_deleted(self, ev):
        raise NotImplementedError

    def on_modified(self, ev):
        raise NotImplementedError

    def on_moved(self, ev):
        raise NotImplementedError


class TestIWatcher(TestCase):
    def test_LocalDirectoryWatcher(self):
        self.assertTrue(
            IWatcher.implementedBy(watchdog.LocalDirectoryWatcher),
            "LocalDirectoryWatcher does not implement IWatcher",
        )


class TestIDiffHandler(TestCase):
    def test_SQLiteEventHandler(self):
        self.assertTrue(
            IDiffHandler.implementedBy(watchdog.EventHandler),
            "EventHandler does not implement IDiffHandler",
        )


class TestISelectiveEventHandler(TestCase):
    def test_SQLiteEventHandler(self):
        self.assertTrue(
            ISelectiveEventHandler.implementedBy(watchdog.EventHandler),
            "EventHandler does not implement ISelectiveEventHandler",
        )


class TestLocalDirectoryWatcher(TestCase):

    handler = DummyHandler()

    def setUp(self):
        self.watcher = watchdog.LocalDirectoryWatcher()

    def tearDown(self):
        del self.watcher

    def test_registration_enforces_IDiffHandler(self):
        self.assertRaises(
            DoesNotImplement,
            self.watcher.register_handler,
            "",
            None,
        )

    def test_handler_registration(self):
        self.assertNotIn(
            self.handler,
            self.watcher.services,
            "Leaky test fixtures"
        )

        with TemporaryDirectory() as path:
            self.watcher.register_handler(path, self.handler)

            self.assertIn(
                self.handler,
                reduce(lambda s0, s1: s0.union(s1),
                       self.watcher._handlers.values()),
                "handler not registered to observer",
            )


class TestSQLiteEventHandler(TestCase):

    filt = dict(includes=["*.in"], excludes=["*exclude*"])

    def setUp(self):
        self.db = adbapi.ConnectionPool(
            "sqlite3",
            ":memory:",
            check_same_thread=False
        )

        self.stateman = SQLiteStateManager(self.db)
        self.handler = watchdog.EventHandler(self.stateman, self.filt)

    def tearDown(self):
        self.db.close()

    def test_service_start_stop_logic(self):
        """test if an open/close cycle works"""
