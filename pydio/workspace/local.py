#! /usr/env/python
import os.path as osp

from zope.interface import implementer

from twisted.logger import Logger
from twisted.internet import defer
from twisted.enterprise import adbapi
from twisted.internet.threads import deferToThread
from twisted.application.service import MultiService

from pydio import ISynchronizable
from .watchdog import LocalDirectoryWatcher, SQLiteEventHandler


@implementer(ISynchronizable)
class Directory(MultiService):
    """An ISynchronizable interface to a local Pydio workspace directory"""

    name = "LocalDirectory"
    log = Logger()

    def __init__(self, target_dir, filters=None):
        super().__init__()

        self._dir = target_dir
        self._dbpool = adbapi.ConnectionPool(
            "sqlite3",
            ":memory:",
            check_same_thread=False
        )

        handler = SQLiteEventHandler(":memory:", filters)
        self.addService(handler)

        watcher = LocalDirectoryWatcher()
        watcher.register_handler(target_dir, handler)
        self.addService(watcher)

        self._change_queue = defer.DeferredQueue()

    def __str__(self):
        return "`{0}`".format(self._dir)

    @property
    def idx(self):
        return self._idx

    def startService(self):
        super().startService()

    def stopService(self):
        super().stopService()
        self._dbpool.close()

    @classmethod
    def from_config(cls, cfg):
        return cls(cfg["directory"])

    @property
    def dir(self):
        """Local directory being watched"""
        return self._dir

    @defer.inlineCallbacks
    def assert_ready(self):
        exists = yield deferToThread(osp.exists, self.dir)
        if not exists:
            raise IOError("{0} unreachable".format(self.dir))

    def get_changes(self):
        return self._change_queue.get()
