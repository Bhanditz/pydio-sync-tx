#! /usr/bin/env python
from functools import wraps

from zope.interface import implementer

from twisted.logger import Logger
from twisted.application.service import Service
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread
from twisted.enterprise.adbapi import ConnectionPool

from pydio.workspace.local import IDiffEngine, IStateManager, IDiffStream


@implementer(IDiffEngine)
class SQLiteEngine(Service):

    log = Logger

    def __init__(self, sql_file, path=":memory:"):
        super().__init__()
        self.sql_file = sql_file
        self._db =  ConnectionPool("sqlite3", path, check_same_thread=False)

    @inlineCallbacks
    def _start(self):
        f = yield deferToThread(open, self.sql_file)
        try:
            for line in f.readlines():
                yield self._db.runOperation(line)
        finally:
            f.close()

    def _stop(self):
        self._db.close()

    def startService(self):
        super().startService()
        return self._start()

    def stopService(self):
        super().stopService()
        return self._stop()

    @property
    def updater(self):
        return SQLiteStateManager(self._db)

    @property
    def stream(self):
        return SQLiteDiffStream(self._db)


@implementer(IDiffStream)
class SQLiteDiffStream:

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
