#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from zope.interface import implementer
from zope.interface.verify import DoesNotImplement

from twisted.application.service import Service

from pydio import IMerger, ISynchronizable, merger


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
            IMerger.implementedBy(merger.SQLiteMerger),
            "SQLiteMerger does not implement IMerger"
        )


class TestEnforceISynchronizable(TestCase):

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
