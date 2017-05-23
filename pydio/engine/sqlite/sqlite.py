#! /usr/bin/env python
from os import makedirs
import os.path as osp
from functools import wraps

from zope.interface import implementer

from twisted.logger import Logger
from twisted.internet import defer
from twisted.internet.threads import deferToThread
from twisted.enterprise import adbapi
from twisted.application.service import Service

from pydio.engine import IDiffEngine, IStateManager, IDiffStream

SQL_INIT_FILE = osp.join(osp.dirname(__file__), "pydio.sql")


@implementer(IDiffEngine)
class Engine(Service):

    log = Logger()

    def __init__(self, db_file):
        super().__init__()

        self.log.debug("opening database in {path}", path=db_file.strip(":"))
        self._db_file = db_file
        self._db = adbapi.ConnectionPool(
            "sqlite3", db_file, check_same_thread=False,
        )

    @defer.inlineCallbacks
    def _init_db(self):
        from sqlite3 import OperationalError

        root_path, _ = osp.split(self._db_file)
        if not osp.exists(root_path):
            makedirs(root_path)

        def run_startup_script():
            with open(SQL_INIT_FILE) as f:
                run_script = lambda c, s: c.executescript(s)
                self._db.runInteraction(run_script, f.read())
                self.log.debug("database initialized")

        try:
            yield self._db.runQuery("SELECT * FROM ajxp_index LIMIT 1;")
            self.log.debug("resuming with existing database")
        except OperationalError:
            self.log.info("initializing db from `{p}`", p=SQL_INIT_FILE)
            yield deferToThread(run_startup_script)

    def startService(self):
        self.log.debug("starting diff engine")
        super().startService()
        return self._init_db()

    def stopService(self):
        self.log.debug("halting")
        super().stopService()
        return self._db.close()

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


def values_as_tuple(d, *param):
    return tuple(map(d.get, param))


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
        params = values_as_tuple(
            inode, "node_path", "bytesize", "md5", "mtime", "stat_result"
        )

        directive = (
            "INSERT INTO ajxp_index (node_path,bytesize,md5,mtime,stat_result) "
            "VALUES (?,?,?,?,?);"
        )

        return self._db.runOperation(directive, params)

    @_log_state_change("delete")
    def delete(self, inode, directory=False):
        self._db.runOperation(
            "DELETE FROM ajxp_index WHERE node_path LIKE ?%", inode["node_path"]
        )

    @_log_state_change("modify")
    def modify(self, inode, directory=False):
        pass
        # params = ("bytesize", "md5", "mtime", "stat_result", "node_path")
        # directive = ("UPDATE ajxp_index "
        #              "SET bytesize=?, md5=?, mtime=?, stat_result=? "
        #              "WHERE node_path=?")
        # self._db.runQuery(directive, map(inode.get, params))

    @_log_state_change("move")
    def move(self, inode, directory=False):
        pass  # DEBUG
        # raise NotImplementedError("I shall move an inode in ajxp_index")
