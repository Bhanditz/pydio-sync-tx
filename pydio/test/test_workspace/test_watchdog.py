#! /usr/bin/env python
from twisted.trial.unittest import TestCase

import os.path as osp
from shutil import rmtree
from functools import reduce
from tempfile import mkdtemp, TemporaryDirectory

from zope.interface import implementer
from zope.interface.verify import DoesNotImplement

from twisted.enterprise import adbapi
from twisted.application.service import Service

from watchdog import events

from pydio.workspace.local import (
    IDiffHandler,
    ISelectiveEventHandler,
    IWatcher,
    watchdog,
)

from pydio.workspace.local import IStateManager


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


@implementer(IStateManager)
class DummyStateManager:

    class _MethodCalled(RuntimeError):
        """Indicates a method was called"""

    class OnCreate(_MethodCalled):
        pass

    class OnDelete(_MethodCalled):
        pass

    class OnModify(_MethodCalled):
        pass

    class OnMove(_MethodCalled):
        pass

    def create(self, inode, directory=False):
        raise self.OnCreate

    def delete(self, inode, directory=False):
        raise self.OnDelete

    def modify(self, inode, directory=False):
        raise self.OnModify

    def move(self, inode, directory=False):
        raise self.OnMove


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

class TestEventHandler(TestCase):

    filters = dict(include=["*"], exclude=["*.exclude"])

    def setUp(self):
        self.dir = mkdtemp()
        self.handler = watchdog.EventHandler(
            DummyStateManager(),
            self.dir,
            filters=self.filters
        )

    def tearDown(self):
        rmtree(self.dir)

    def test_event_filter_include(self):
        ev = events.FileCreatedEvent(osp.join(self.dir, "test"))
        self.assertTrue(
            self.handler._filter_event(ev),
            "relevant event {0} was ignored".format(ev),
        )

    def test_event_filter_exclude(self):
        ev = events.FileCreatedEvent(osp.join(self.dir, "test.exclude"))
        self.assertFalse(
            self.handler._filter_event(ev),
            "irrelevant event {0} was processed".format(ev),
        )

    def test_event_filter_root(self):
        ev = events.DirModifiedEvent(self.dir)
        self.assertFalse(
            self.handler._filter_event(ev),
            "root directory {0} was processed".format(ev.src_path),
        )
