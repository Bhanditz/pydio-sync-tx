#! /usr/bin/env python
from os import stat
import os.path as osp
from hashlib import md5
from pickle import dumps
from fnmatch import fnmatch
from functools import wraps

from zope.interface import implementer
from zope.interface.verify import verifyObject

from twisted.logger import Logger
from twisted.internet import defer
from twisted.internet.threads import deferToThread
from twisted.application.service import Service, MultiService

from watchdog import events
from watchdog.observers import Observer

from pydio.util.blocking import threaded
from . import IDiffHandler, ISelectiveEventHandler
from pydio.storage import IStorage
from pydio.engine import IStateManager

MD5_DIRECTORY = "directory"

FILE_EVENTS = {events.FileCreatedEvent, events.FileDeletedEvent,
               events.FileModifiedEvent, events.FileMovedEvent}
DIR_EVENTS = {events.DirCreatedEvent, events.DirDeletedEvent,
              events.DirModifiedEvent, events.DirMovedEvent}

CREATE_EVENTS = {events.FileCreatedEvent, events.DirCreatedEvent}
DELETE_EVENTS = {events.FileDeletedEvent, events.DirDeletedEvent}
MODIFY_EVENTS = {events.FileModifiedEvent, events.DirModifiedEvent}
MOVE_EVENTS = {events.FileMovedEvent, events.DirMovedEvent}

ALL_EVENTS = FILE_EVENTS.union(DIR_EVENTS)


def log_event(lvl="info"):
    def decorator(fn):
        @wraps(fn)
        def event_handler(self, ev):
            log = getattr(self.log, lvl)
            log("{e.event_type} {e.src_path}", e=ev)
            return fn(self, ev)
        return event_handler
    return decorator


@implementer(IStorage)
class LocalDirectory(MultiService):
    def __init__(self, path, recursive=True, filters=None):
        super().__init__()

        self._path = path
        self._recursive = recursive
        self._filt = filters or {}
        self._obs = Observer()

    def connect_state_manager(self, istateman):
        verifyObject(IStateManager, istateman)
        h = EventHandler(istateman, self._path, self._filt)
        self.addService(h)
        self._obs.schedule(h, self._path, recursive=self._recursive)

    def startService(self):
        super().startService()
        self._obs.start()

    def stopService(self):
        super().stopService()
        self._obs.stop()
        return deferToThread(self._obs.join)

    def available(self):
        osp.exists(self._path)


@implementer(IDiffHandler, ISelectiveEventHandler)
class EventHandler(Service, events.FileSystemEventHandler):

    log = Logger()

    def __init__(self, state_manager, base_path, filters=None):
        Service.__init__(self)
        events.FileSystemEventHandler.__init__(self)

        self._filt = filters or {}

        # add a trailing slash if it's not already there
        self._base_path = osp.join(osp.normpath(base_path), "")

        verifyObject(IStateManager, state_manager)
        self._state_manager = state_manager

    @property
    def include(self):
        return tuple(self._filt.get("include", tuple()))

    @property
    def exclude(self):
        return tuple(self._filt.get("exclude", tuple()))

    def match_any(self, globlist, path):
        """Returns true if the path is matched by at least one of the UNIX wildcard
        expressions in `globlist`.
        """
        return any(map(lambda glb: fnmatch(path, glb), globlist))

    def relative_path(self, path):
        return osp.normpath(path).replace(self._base_path, "")

    def _filter_event(self, ev):
        included = self.match_any(self.include, ev.src_path)
        excluded = self.match_any(self.exclude, ev.src_path)
        non_root = bool(self.relative_path(ev.src_path))
        return all((included, not excluded, non_root))

    def dispatch(self, ev):
        # Filter out irrelevant envents
        # No need to test this function.  It's covered by watchdog's unit tests.
        if self._filter_event(ev):
            events.FileSystemEventHandler.dispatch(self, ev)
        else:
            self.log.debug("ignoring {ev}", ev=ev)

    @threaded
    def compute_file_hash(self, path):
        with open(path, "rb") as f:
            return md5(f.read()).hexdigest()

    @defer.inlineCallbacks
    def _add_hash_to_inode(self, ev, inode):
        if ev.is_directory:
            inode["md5"] = MD5_DIRECTORY
        elif isinstance(ev, tuple(CREATE_EVENTS.union(MODIFY_EVENTS))):
            inode["md5"] = yield self.compute_file_hash(ev.src_path)
        elif isinstance(ev, tuple(MOVE_EVENTS)):
            inode["md5"] = yield self.compute_file_hash(ev.dest_path)
        else:
            emsg = "mishandled {0}.  This should never happen"
            raise RuntimeError(emsg.format(type(ev)))

    @defer.inlineCallbacks
    def _add_stat_to_inode(self, ev, inode):
        if isinstance(ev, tuple(MOVE_EVENTS)):
            stats = yield self.fs_stats(ev.dest_path)
        elif isinstance(ev, tuple(CREATE_EVENTS.union(MODIFY_EVENTS))):
            stats = yield self.fs_stats(ev.src_path)

        inode.update(stats)

    @threaded
    def fs_stats(self, path):
        return dict(
            bytesize=osp.getsize(path),
            mtime=osp.getmtime(path),
            stat_result=dumps(stat(path), protocol=4),
        )

    @defer.inlineCallbacks
    def new_node(self, ev):
        """Create a new dict representing an inode."""
        if isinstance(ev, tuple(MOVE_EVENTS)):
            inode = dict(node_path=ev.dest_path)
        else:
            inode = dict(node_path=ev.src_path)

        if isinstance(ev, tuple(ALL_EVENTS.difference(DELETE_EVENTS))):
            yield defer.gatherResults((
                self._add_hash_to_inode(ev, inode),
                self._add_stat_to_inode(ev, inode),
            ))
        defer.returnValue(inode)

    @log_event()
    def on_created(self, ev):
        """Called when an inode is created"""
        return self.new_node(ev).addCallback(
            self._state_manager.create,
            directory=ev.is_directory
        )

    @log_event()
    def on_deleted(self, ev):
        """Called when an inode is deleted"""
        return self.new_node(ev).addCallback(
            self._state_manager.delete,
            directory=ev.is_directory
        )

    @log_event()
    def on_modified(self, ev):
        """Called when an existing inode is modified"""

        import ipdb; ipdb.set_trace()

        # is it a directory?
        #   if so, are their files contained within?
        #       if so get a handle on the most recently updated file
        #   else, return
        #
        #   is that file actually a file (as opposed to a subdir)?
        #      if so, update the db.  (what about the others?)
        #   else, return
        #
        # if it's not a directory:
        #   check if the file still exists, if not, return, else update

        # tl;dr:  (1) if it's a dir, act on sub-inodes (2) update the db

        # self.mk_inode(ev).addCallback(self._state_manager.modify,
        #                               directory=ev.is_directory)

    @log_event()
    def on_moved(self, ev):
        """Called when an existing inode is moved"""
        # self.mk_inode(ev).addCallback(self._state_manager.move,
        #                               directory=ev.is_directory)
