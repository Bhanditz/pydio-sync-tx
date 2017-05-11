#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from pydio.workspace import ISynchronizable, remote


class TestISynchronizable(TestCase):
    def test_PydioServerWorkspace(self):
        self.assertTrue(
            ISynchronizable.implementedBy(remote.PydioServer),
            "PydioServer does not implement ISynchronizable",
        )
