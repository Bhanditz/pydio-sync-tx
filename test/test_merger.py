#! /usr/bin/env python
from unittest import TestCase

from zope.interface import implementer
from zope.interface.verify import DoesNotImplement

from pydio import merger


@implementer(merger.ISynchronizable)
class DummySynchronizable:
    """A null-op class that satisfies merger.ISynchronizable for testing
    purposes
    """
    def get_changes(self, idx):
        pass


class TestISynchronizable(TestCase):
    def test_PydioServerWorkspace(self):
        self.assertTrue(
            merger.ISynchronizable.implementedBy(merger.PydioServerWorkspace),
            "PydioServerWorkspace does not implement ISynchronizable",
        )

    def test_LocalWorkspace(self):
        self.assertTrue(
            merger.ISynchronizable.implementedBy(merger.LocalWorkspace),
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
