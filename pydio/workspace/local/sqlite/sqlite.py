#! /usr/bin/env python
import os.path as osp
from functools import wraps

from zope.interface import implementer

from twisted.logger import Logger
from twisted.internet import defer
from twisted.application.service import Service
from twisted.internet.threads import deferToThread
from twisted.enterprise.adbapi import ConnectionPool

from pydio.workspace.local import IDiffEngine, IStateManager, IDiffStream

SQL_INIT_FILE = osp.join(osp.dirname(__file__), "pydio.sql")


@implementer(IDiffEngine)
class Engine(Service):

    log = Logger()

    def __init__(self, db_file=":memory:"):
        super().__init__()

        self.log.debug("opening database in {path}", path=db_file.strip(":"))
        self._db = ConnectionPool("sqlite3", db_file, check_same_thread=False)

    @defer.inlineCallbacks
    def _start(self):
        f = yield deferToThread(open, SQL_INIT_FILE)
        try:
            run_script = lambda c, s: c.executescript(s)
            yield self._db.runInteraction(run_script, f.read())
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
        params = ("node_path", "bytesize", "md5", "mtime", "stat_result")
        # directive = ("INSERT INTO ajxp_index "
        #              "(node_path,bytesize,md5,mtime,stat_result) VALUES "
        #              "(?,?,?,?,?)")
        # self._db.runQuery(directive, map(inode.get, parms))

    @_log_state_change("delete")
    def delete(self, inode, directory=False):
        pass  # DEBUG
        # self._db.runQuery(
        #     "DELETE FROM ajxp_index WHERE node_path LIKE ?%",
        #     inode["src_path"],
        # )

    @_log_state_change("modify")
    def modify(self, inode, directory=False):
        if directory:
            return  # we'll update the files individually, as we're notified

        # params = ("bytesize", "md5", "mtime", "stat_result", "node_path")
        # directive = ("UPDATE ajxp_index "
        #              "SET bytesize=?, md5=?, mtime=?, stat_result=? "
        #              "WHERE node_path=?")
        # self._db.runQuery(directive, map(inode.get, params))

    @_log_state_change("move")
    def move(self, inode, directory=False):
        pass  # DEBUG
        # raise NotImplementedError("I shall move an inode in ajxp_index")

__all__ = ["Engine", "DiffStream", "StateManager"]
