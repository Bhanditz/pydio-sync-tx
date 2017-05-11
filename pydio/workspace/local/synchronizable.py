#! /usr/env/python
import os.path as osp

from zope.interface import implementer
from zope.interface.verify import verifyObject

from twisted.logger import Logger
from twisted.internet import defer
from twisted.enterprise import adbapi
from twisted.internet.threads import deferToThread
from twisted.application.service import MultiService

from pydio.workspace import ISynchronizable
from pydio.workspace.local import IDiffEngine
from .watchdog import LocalDirectoryWatcher, EventHandler


@implementer(ISynchronizable)
class Directory(MultiService):
    """An ISynchronizable interface to a local Pydio workspace directory"""

    log = Logger()

    def __init__(self, engine, target_dir, filters=None):
        super().__init__()

        verifyObject(IDiffEngine, engine)
        self._engine = engine
        self.addService(engine)

        self._dir = target_dir

        handler = EventHandler(self._engine.updater, filters)
        self.addService(handler)

        watcher = LocalDirectoryWatcher()
        watcher.register_handler(target_dir, handler)
        self.addService(watcher)

        self._change_queue = defer.DeferredQueue()

    @property
    def name(self):
        return "`{0}`".format(self._dir)

    def __str__(self):
        return self.name

    @property
    def idx(self):
        return self._idx

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
        return self._engine.stream.next()
