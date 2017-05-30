#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from twisted.internet import defer

from pydio.util.adbapi import ConnectionManager


class TestConnectionPool(TestCase):
    """Test the initial state of the ConnectionPool prior to any database IO"""

    def setUp(self):
        self.cm = ConnectionManager(":memory:")

    def tearDown(self):
        self.cm.close()

    def test_initial_connection_state(self):
        """A canary test which ensures that ConnectionManager is initialized
        with no active connections.

        A failure on the part of this test does not (necessarily) indicate a
        bug in pydio, but is likely to cause other tests to fail.
        """
        self.assertFalse(self.cm.connections, "dirty ConnectionManager")

    def test_min_connections(self):
        mc = self.cm.min
        self.assertTrue(
            mc == 1, "expected min connections == 1, set to {0}".format(mc),
        )

    def test_max_connections(self):
        mc = self.cm.max
        self.assertTrue(
            mc == 1, "expected min connections == 1, set to {0}".format(mc),
        )

    @defer.inlineCallbacks
    def test_memdb_reference(self):
        """Regression test to ensure that multiple calls to an in-memory db
        all reference the same database.
        """
        n_inserts = 10

        yield self.cm.runOperation(
            "CREATE TABLE xxx (k INTEGER PRIMARY KEY AUTOINCREMENT, v INTEGER);"
        )
        yield defer.gatherResults([self.cm.runOperation(
                "INSERT INTO xxx (v) VALUES (?)", (i,)
            ) for i in range(n_inserts)])
        rows = yield self.cm.runQuery("SELECT * FROM xxx;")

        emsg = "expected {0} rows, got {1}".format(n_inserts, len(rows))
        self.assertTrue(len(rows) == n_inserts, emsg)

    @defer.inlineCallbacks
    def test_max_conn_enforcement(self):
        yield self.cm.runOperation(
            "CREATE TABLE xxx (k INTEGER PRIMARY KEY AUTOINCREMENT, v INTEGER);"
        )

        # Don't yield from the deferred.
        # The objective is to cause a spike in resource usage and check
        # that constraints on the number of connections are enforced.
        dfl = [self.cm.runOperation(
                "INSERT INTO xxx (v) VALUES (?)", (i,)
            ) for i in range(10)]

        nc = len(self.cm.connections)
        self.assertTrue(
            nc == 1,
            "unexpected number of connections.  Expected 1, got {0}".format(nc),
        )

        yield defer.gatherResults(dfl)  # make sure everything finishes cleanly
