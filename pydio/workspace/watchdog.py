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
class LocalDirectoryWatcher(Service, Observer):

    log = Logger()

    def __init__(self):
        MultiService.__init__(self)
        Observer.__init__(self)

    def register_handler(self, path, handler, recursive=True):
        """Register an IEventHandler to the directory observer, and register the
        former as a service to IWatcher.
        """
        verifyObject(IDiffHandler, handler)
        self.schedule(handler, path, recursive=recursive)

    def startService(self):
        self.start()

    def stopService(self):
        self.stop()
        return deferToThread(self.join)


@implementer(IDiffHandler, ISelectiveEventHandler)
class SQLiteEventHandler(Service, FileSystemEventHandler):

    log = Logger()

    def __init__(self, dbpath, filters):
        Service.__init__(self)
        FileSystemEventHandler.__init__(self)
        self._filt = filters

    @property
    def include(self):
        return tuple(self._filt["includes"])

    @property
    def exclude(self):
        return tuple(self._filt["excludes"])

    @staticmethod
    def match_any(globlist, path):
        """Returns true if the path is matched by at least one of the UNIX wildcard
        expressions in `globlist`.
        """
        return any(map(lambda glb: fnmatch(path, glb), globlist))

    @filter_events
    def dispatch(self, ev):
        # Filtering events at the IEventHandler.dispatch level ensures that
        # on_* methods will only be called with events of interest.
        # (See watchdog.events.FileSystemEventHandler for details)
        FileSystemEventHandler.dispatch(self, ev)

    def on_created(self, ev):
        """Called when an inode is created"""
        self.log.debug("{e.event_type} {e.src_path}", e=ev)

    def on_deleted(self, ev):
        """Called when an inode is deleted"""
        self.log.debug("{e.event_type} {e.src_path}", e=ev)

    def on_modified(self, ev):
        """Called when an existing inode is modified"""
        self.log.debug("{e.event_type} {e.src_path}", e=ev)

    def on_moved(self, ev):
        """Called when an existing inode is moved"""
        self.log.debug("{e.event_type} {e.src_path}", e=ev)
