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

    log = Logger()

    def __init__(self, target_dir, filters=None):
        super().__init__()

        self._dir = target_dir
        db = adbapi.ConnectionPool(
            "sqlite3",
            ":memory:",
            check_same_thread=False
        )

        self._diff_stream = SQLiteDiffStream(db)

        handler = SQLiteEventHandler(SQLiteStateManager(db), filters)
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

    def stopService(self):
        super().stopService()
        self._diff_stream.close()

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
        return self._diff_stream.next()


def _log_state_change(verb):
    def decorator(fn):
        @wraps(fn)
        def logger(self, verb, inode, directory):
            itype = ("file", "directory")[directory]
            self.log.debug("{v} {0} `{1}`", itype, inode["src_path"], v=verb)
        return logger
    return decorator


class SQLiteDiffStream:
    self._db = db

    def next(self):
        raise NotImplementedError("I shall return a tuple of diffs")


@implementer(IStateManager)
class SQLiteStateManager:
    """Manages the SQLite database's state, ensuring that it reflects the state
    of the filesystem.
    """

    log = Logger()

    def __init__(self, db):
        self._db = db

    @_log_state_change("create")
    def create(self, inode, directory=False):
        raise NotImplementedError("I shall create a new inode in ajxp_index")

    @_log_state_change("delete")
    def delete(self, inode, directory=False):
        raise NotImplementedError("I shall delete an inode from ajxp_index")

    @_log_state_change("modify")
    def modify(self, inode, directory=False):
        raise NotImplementedError("I shall modify an inode in ajxp_index")

    @_log_state_change("move")
    def move(self, inode, directory=False):
        raise NotImplementedError("I shall move an inode in ajxp_index")
