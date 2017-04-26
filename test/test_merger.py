#! /usr/bin/env python

from unittest import TestCase

from pydio import merger


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
