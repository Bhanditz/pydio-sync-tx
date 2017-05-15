#! /usr/bin/env python
import sqlite3

from twisted.logger import Logger
from twisted.internet import defer
from twisted.application.service import Service
from twisted.internet.threads import deferToThread


class SQLiteService(Service):

    log = Logger()
    init_script = None  # path to .sql script

    def __init__(self, db_file=":memory:"):
        self._db_file = db_file
        self._running = False
        self._exec_done = None  # Deferred set by startService

        self._sql_q = defer.DeferredQueue()
        self._conn = sqlite3.connect(db_file)

    @defer.inlineCallbacks
    def _init(self):
        if self.init_script is not None:
            f = yield deferToThread(open, self.init_script)
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
        return self._init()



    def stopService(self):
        self.log.warn("stopping sqlite service")
        super().stopService()
        self._running = False
        self._conn.close()
        return self._exec_done
