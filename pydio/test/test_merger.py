#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from zope.interface import implementer
from zope.interface.verify import DoesNotImplement, verifyClass

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


class TestDummySynchronizable(TestCase):
    """A canary test meant to ensure DummySynchronizable satisfies
    ISynchronizable
    """

    def test_ISynchronizable(self):
        verifyClass(ISynchronizable, DummySynchronizable)


class TestIMerger(TestCase):
    def test_TwoWayMerger(self):
        self.assertTrue(
            IMerger.implementedBy(merger.TwoWayMerger),
            "TwoWayMerger does not implement IMerger"
        )


class TestEnforceISynchronizable(TestCase):

    synchronizable = DummySynchronizable()

    def test_enforce_local(self):
        self.assertRaises(
            DoesNotImplement,
            merger.TwoWayMerger,
            None,
            self.synchronizable,
        )

    def test_enforce_remote(self):
        self.assertRaises(
            DoesNotImplement,
            merger.TwoWayMerger,
            self.synchronizable,
            None,
        )


class TestTwoWayMergerSync(TestCase):
    def setUp(self):
        self.local = DummySynchronizable()
        self.remote = DummySynchronizable()
        self.merger = merger.TwoWayMerger(self.local, self.remote)

    def tearDown(self):
        del self.local
        del self.remote
        del self.merger

    def test_assert_volume_ready__pass(self):
        return self.merger.assert_volumes_ready()
