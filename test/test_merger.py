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
