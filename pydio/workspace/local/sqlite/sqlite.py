#! /usr/bin/env python
import sqlite3
import os.path as osp
from functools import wraps

from zope.interface import implementer

from twisted.logger import Logger
from twisted.internet import defer
from twisted.application.service import Service
from twisted.internet.threads import deferToThread

from pydio.util.blocking import threaded
from pydio.workspace.local import IDiffEngine, IStateManager, IDiffStream

SQL_INIT_FILE = osp.join(osp.dirname(__file__), "pydio.sql")


class SQLite(Service):

    log = Logger()

    def __init__(self, db_file=":memory:", init_script=None):
        self._db_file = db_file
        self._running = False
        self._exec_done = None  # Deferred set by startService

        self._sql_q = defer.DeferredQueue()
        self._conn = sqlite3.connect(db_file)
        if init_script is not None:
            self.log.info("Running `{script}`", script=init_script)
            self._init(init_script)

    @defer.inlineCallbacks
    def _init(self, path):
        def _start(self):
            f = yield deferToThread(open, SQL_INIT_FILE)
            try:
                yield deferToThread(self._conn.executescript, f.read())
            finally:
                f.close()

    def execute(self, statement, *param):
        d = defer.Deferred()
        self._sql_q.put((d, statement, param))
        return d

    @defer.inlineCallbacks
    def _exec(self):
        while (self._running or len(self._sql_q)):
            d, statement, param = yield self._sql_q.get()
            c = self._conn.cursor()
            yield deferToThread(c.execute, statement, *param)
            d.callback(c)
            c.close()

    def startService(self):
        self.log.info("starting sqlite service")
        super().startService()
        self._running = True
        self._exec_done = self._exec()

    def stopService(self):
        self.log.warn("stopping sqlite service")
        super().stopService()
        self._running = False
        self._conn.close()
        return self._exec_done


@implementer(IDiffEngine)
class Engine(Service):

    log = Logger()

    def __init__(self, db_file=":memory:"):
        super().__init__()

        self.log.debug("opening database in {path}", path=db_file.strip(":"))
        self._db = SQLite(db_file)

    def startService(self):
        self.log.info("initializing database from {path}", path=SQL_INIT_FILE)
        super().startService()
        return self._db.startService()

    def stopService(self):
        self.log.warn("halting")
        super().stopService()
        return self._db.stopService()

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
            self.log.debug("{verb} {itype} `{ipath}`",
                           verb=verb, itype=itype, ipath=inode["node_path"])
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
        directive = ("INSERT INTO ajxp_index "
                     "(node_path,bytesize,md5,mtime,stat_result) VALUES "
                     "(?,?,?,?,?);")
        return self._db.execute(directive, *map(inode.get, params))

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
