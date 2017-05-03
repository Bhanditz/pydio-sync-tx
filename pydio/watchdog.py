#! /usr/bin/env/python
import os.path as osp
from fnmatch import fnmatch
from functools import wraps

from zope.interface import implementer
from zope.interface.verify import verifyObject

from twisted.logger import Logger
from twisted.enterprise import adbapi
from twisted.internet.threads import deferToThread
from twisted.application.service import Service, MultiService

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from pydio import IWatcher, IDiffHandler, ISelectiveEventHandler


def filter_events(method):
    """filter_events decorates EventHandler methods such that
    events that are not inclusively matched by a job's whitelist and exclusively
    matched by that same job's blacklist are ignored.
    """
    @wraps(method)
    def wrapper(self, ev):
        included = self.match_any(self.include, ev.dest_path)
        excluded = self.match_any(self.exclude, ev.dest_path)
        if included and not excluded:
            return method(self, ev)
    return wrapper


@implementer(IWatcher)
class LocalDirectoryWatcher(MultiService):

    log = Logger()

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


@implementer(IDiffHandler, ISelectiveEventHandler)
class SQLiteEventHandler(Service, FileSystemEventHandler):

    log = Logger()

    def __init__(self, dbpath, filters):
        super().__init__()
        self._dbpath = dbpath
        self._filt = filters

        self._dbpool = adbapi.ConnectionPool(
            "sqlite3", dbpath, check_same_thread=False
        )

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

    @filter_events
    def dispatch(self, ev):
        # Filtering events at the IEventHandler.dispatch level ensures that
        # on_* methods will only be called with events of interest.
        # (See watchdog.events.FileSystemEventHandler for details)
        super().dispatch(ev)

    def on_created(self, ev):
        """Called when an inode is created"""

    def on_deleted(self, ev):
        """Called when an inode is deleted"""

    def on_modified(self, ev):
        """Called when an existing inode is modified"""

    def on_moved(self, ev):
        """Called when an existing inode is moved"""

    def startService(self):
        super().startService()

    def stopService(self):
        super().stopService()
        self._dbpool.close()

    @staticmethod
    def match_any(globlist, path):
        """Returns true if the path is matched by at least one of the UNIX wildcard
        expressions in `globlist`.
        """
        return any(map(lambda glb: fnmatch(path, glb), globlist))
