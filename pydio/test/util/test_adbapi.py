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
        self.assertEquals(
            self.cm.min, 1,
            "expected min connections == 1, set to {0}".format(self.cm.min),
        )

    def test_max_connections(self):
        self.assertEquals(
            self.cm.max, 1,
            "expected min connections == 1, set to {0}".format(self.cm.max),
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

        self.assertEquals(
            len(rows), n_inserts,
            "expected {0} rows, got {1}".format(n_inserts, len(rows)),
        )

    @defer.inlineCallbacks
    def test_max_conn_enforcement(self):
        """Initially intended as an exploratory test, but there's no reason to
        remove it now that it's written.  Ensures that cp_max is enforced in
        t.e.adbapi.ConnectionPool (as opposed to, say, a soft limit or an
        exception being thrown).
        """

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
