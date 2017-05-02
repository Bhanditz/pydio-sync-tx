#! /usr/bin/env/python
import os.path as osp

from zope.interface import implementer
from zope.interface.verify import verifyObject

from twisted.application.service import Service, MultiService
from twisted.internet.threads import deferToThread

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from pydio import IWatcher, IDiffHandler


@implementer(IWatcher)
class LocalDirectoryWatcher(MultiService):
    def __init__(self):
        super().__init__()
        self._obs = Observer()

    def register_handler(self, path, handler, recursive=True):
        """Register an IEventHandler to the directory observer, and register the
        former as a service to IWatcher.
        """

        verifyObject(IDiffHandler, handler)
        self.addService(handler)
        self._obs.schedule(handler, path, recursive=recursive)

    def startService(self):
        self._obs.start()

    def stopService(self):
        self._obs.stop()
        return deferToThread(self._obs.join)


@implementer(IDiffHandler)
class SQLiteEventHandler(Service, FileSystemEventHandler):
    def __init__(self, dbpath, filters):
        super().__init__()
        self._dbpath = dbpath
        self._filt = filters

    @property
    def include(self):
        return tuple(self._filt["includes"])

    @property
    def exclude(self):
        return tuple(self._filt["excludes"])

    @classmethod
    def from_config(cls, file, cfg):
        return cls(
            dbpath=osp.join(cfg["directory"], "pydio.sqlite"),
            filters=cfg["filters"],
        )

    def on_created(self, ev):
        """Called when an inode is created"""

    def on_deleted(self, ev):
        """Called when an inode is deleted"""

    def on_modified(self, ev):
        """Called when an existing inode is modified"""

    def on_moved(self, ev):
        """Called when an existing inode is moved"""
