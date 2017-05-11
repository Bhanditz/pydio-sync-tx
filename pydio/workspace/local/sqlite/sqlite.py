#! /usr/bin/env python
import os.path as osp
from functools import wraps

from zope.interface import implementer

from twisted.logger import Logger
from twisted.application.service import Service
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread
from twisted.enterprise.adbapi import ConnectionPool

from pydio.workspace.local import IDiffEngine, IStateManager, IDiffStream

SQL_INIT_FILE = osp.join(osp.dirname(__file__), "pydio.sql")


@implementer(IDiffEngine)
class Engine(Service):

    log = Logger

    def __init__(self, path=":memory:"):
        super().__init__()

        self.log.debug("opening database in {path}", path=path)
        self._db = ConnectionPool("sqlite3", path, check_same_thread=False)

    @inlineCallbacks
    def _start(self):
        f = yield deferToThread(open, SQL_INIT_FILE)
        try:
            for line in f.readlines():
                yield self._db.runOperation(line)
        finally:
            f.close()

    def _stop(self):
        self._db.close()

    def startService(self):
        self.log.debug("initializing database from {path}", path=SQL_INIT_FILE)
        super().startService()
        return self._start()

    def stopService(self):
        self.log.debug("halting")
        super().stopService()
        return self._stop()

    @property
    def updater(self):
        return StateManager(self._db)

    @property
    def stream(self):
        return DiffStream(self._db)


@implementer(IDiffStream)
class DiffStream:

    log = Logger()

    def __init__(self, db):
        self._db = db

    def next(self):
        raise NotImplementedError("I shall return a tuple of diffs")


def _log_state_change(verb):
    def decorator(fn):
        @wraps(fn)
        def logger(self, inode, directory=False):
            itype = ("file", "directory")[directory]
            self.log.debug("{v} {0} `{1}`", itype, inode["src_path"], v=verb)
            fn(self, inode, directory)
        return logger
    return decorator


@implementer(IStateManager)
class StateManager:
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

__all__ = ["Engine", "DiffStream", "StateManager"]
