#! /usr/bin/env/python
from os import stat
import os.path as osp
from hashlib import md5
from fnmatch import fnmatch
from functools import wraps

from zope.interface import implementer
from zope.interface.verify import verifyObject

from twisted.logger import Logger
from twisted.internet import defer
from twisted.internet.threads import deferToThread
from twisted.application.service import Service, MultiService

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from pydio.util.blocking import threaded
from . import IStateManager, IDiffHandler, IWatcher
from pydio.workspace.local import ISelectiveEventHandler


def log_event(lvl="info"):
    def decorator(fn):
        @wraps(fn)
        def event_handler(self, ev):
            log = getattr(self.log, lvl)
            log("{e.event_type} {e.src_path}", e=ev)
            return fn(self, ev)
        return event_handler
    return decorator


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
class EventHandler(Service, FileSystemEventHandler):

    log = Logger()

    def __init__(self, state_manager, base_path, filters=None):
        Service.__init__(self)
        FileSystemEventHandler.__init__(self)

        self._filt = filters or {}

        self._base_path = base_path

        verifyObject(IStateManager, state_manager)
        self._state_manager = state_manager

    @property
    def include(self):
        return tuple(self._filt.get("include", []))

    @property
    def exclude(self):
        return tuple(self._filt.get("exclude", []))

    @staticmethod
    def match_any(globlist, path):
        """Returns true if the path is matched by at least one of the UNIX wildcard
        expressions in `globlist`.
        """
        return any(map(lambda glb: fnmatch(path, glb), globlist))

    def base_path(self, path):
        return path.replace(self._base_path, "")

    def _filter_event(self, ev):
        included = self.match_any(self.include, ev.src_path)
        excluded = self.match_any(self.exclude, ev.src_path)
        non_root = bool(self.base_path(ev.src_path))
        return all((included, not excluded, non_root))

    def dispatch(self, ev):
        # Filter out irrelevant envents
        # No need to test this function.  It's covered by watchdog's unit tests.
        if self._filter_event(ev):
            FileSystemEventHandler.dispatch(self, ev)

    @threaded
    def compute_file_hash(self, path):
        with open(path) as f:
            return md5(f.read().encode("utf-8")).hexdigest()

    @threaded
    def fs_stats(self, path):
        return dict(
            bytesize=osp.getsize(path),
            mtime=osp.getmtime(path),
            stat_result=stat(path)
        )

    @log_event()
    @defer.inlineCallbacks
    def on_created(self, ev):
        """Called when an inode is created"""

        inode = {"node_path": ev.src_path}
        if not ev.is_directory:
            stats = yield self.fs_stats(ev.src_path)
            inode.update(stats)
            inode["md5"] = yield self.compute_file_hash(ev.src_path)
        else:
            inode["md5"] = "directory"

        self._state_manager.create(inode, directory=ev.is_directory)

    @log_event()
    def on_deleted(self, ev):
        """Called when an inode is deleted"""
        # self.mk_inode(ev).addCallback(self._state_manager.delete,
        #                               directory=ev.is_directory)

    @log_event()
    def on_modified(self, ev):
        """Called when an existing inode is modified"""
        # self.mk_inode(ev).addCallback(self._state_manager.modify,
        #                               directory=ev.is_directory)

    @log_event()
    def on_moved(self, ev):
        """Called when an existing inode is moved"""
        # self.mk_inode(ev).addCallback(self._state_manager.move,
        #                               directory=ev.is_directory)
