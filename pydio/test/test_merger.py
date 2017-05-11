#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from zope.interface import implementer
from zope.interface.verify import DoesNotImplement

from twisted.application.service import Service

from pydio import merger, ISynchronizable


@implementer(ISynchronizable)
class DummySynchronizable(Service):
    """A null-op class that satisfies ISynchronizable for testing
    purposes
    """
    idx = None

    def __init__(self, fail_assertion=False):
        super().__init__()
        self.fail_assertion = fail_assertion

    def get_changes(self):
        raise NotImplementedError

    def assert_ready(self):
        if self.fail_assertion:
            raise AssertionError("testing failure case")


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


class TestSQLiteMergerSync(TestCase):
    def setUp(self):
        self.local = DummySynchronizable()
        self.remote = DummySynchronizable()
        self.merger = merger.SQLiteMerger(self.local, self.remote)

    def tearDown(self):
        del self.local
        del self.remote
        del self.merger

    def test_assert_volume_ready__pass(self):
        return self.merger.assert_volumes_ready()

    # def test_assert_volume_ready__fail_local(self):
    #     self.local.fail_assertion = True
    #     return self.assertFailure(
    #         self.merger.assert_volumes_ready(),
    #         AssertionError,
    #     )

    # def test_assert_volume_ready__fail_remote(self):
    #     self.remote.fail_assertion = True
    #     return self.assertFailure(
    #         self.merger.assert_volumes_ready(),
    #         AssertionError,
    #     )
