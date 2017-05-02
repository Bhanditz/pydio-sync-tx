#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from shutil import rmtree
from tempfile import mkdtemp

from zope.interface import implementer
from zope.interface.verify import DoesNotImplement

from pydio import merger, ISynchronizable


@implementer(ISynchronizable)
class DummySynchronizable:
    """A null-op class that satisfies ISynchronizable for testing
    purposes
    """
    def get_changes(self, idx):
        pass

    def assert_ready(self):
        pass


class TestISynchronizable(TestCase):
    def test_PydioServerWorkspace(self):
        self.assertTrue(
            ISynchronizable.implementedBy(merger.PydioServerWorkspace),
            "PydioServerWorkspace does not implement ISynchronizable",
        )

    def test_LocalWorkspace(self):
        self.assertTrue(
            ISynchronizable.implementedBy(merger.LocalWorkspace),
            "LocalWorkspace does not implement ISynchronizable",
        )


class TestIMerger(TestCase):
    def test_SQLiteMerger(self):
        self.assertTrue(
            merger.IMerger.implementedBy(merger.SQLiteMerger),
            "SQLiteMerger does not implement IMerger"
        )


class TestSQLiteMergerIfaceEnforcement(TestCase):

    synchronizable = DummySynchronizable()

    def test_enforce_local(self):
        self.assertRaises(
            DoesNotImplement,
            merger.SQLiteMerger,
            None,
            self.synchronizable,
        )

    def test_enforce_remote(self):
        self.assertRaises(
            DoesNotImplement,
            merger.SQLiteMerger,
            self.synchronizable,
            None,
        )


class TestSQLiteMergerLocking(TestCase):
    def setUp(self):
        dummy = DummySynchronizable()
        self.m = merger.SQLiteMerger(dummy, dummy)

    def tearDown(self):
        self.m = None

    def test_prop_merging_default(self):
        self.assertFalse(
            self.m.merging,
            "SQLiteMerger.merging should default to False",
        )

        self.assertEquals(
            self.m.merging, self.m._locked,
            "SQLiteMerger.merging should reflect lock state (err:  bad init)",
        )

    def test_prop_merging_update(self):
        self.m._locked = True

        self.assertTrue(
            self.m.merging,
            "SQLiteMerger.merging should reflect lock state",
        )

        self.assertEquals(
            self.m.merging, self.m._locked,
            "SQLiteMerger.merging should reflect lock state",
        )

    def test_contextual_lockeding(self):
        with self.m._lock_for_sync_run():
            self.assertTrue(
                self.m.merging,
                "Context manager failed to set lock",
            )

    def test_detect_concurrent_merge(self):
        self.m._locked = True
        def concurrent_merge():
            with self.m._lock_for_sync_run():
                pass

        self.assertRaises(merger.ConcurrentMerge, concurrent_merge)


class TestLocalWorkspace(TestCase):
    def setUp(self):
        self.path = mkdtemp(prefix="pydio_test")
        self.ws = merger.LocalWorkspace(dir=self.path)

    def tearDown(self):
        self.ws = None
        rmtree(self.path)

    def test_dir(self):
        self.assertEqual(self.ws.dir, self.path, "path improperly set/reported")

    def test_assert_ready(self):
        return self.ws.assert_ready()

    def test_assert_ready_fail(self):
        self.ws._dir = "/does/not/exist"
        self.assertFailure(self.ws.assert_ready())
