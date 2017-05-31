#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from zope.interface.verify import verifyClass, DoesNotImplement

from pydio.storage import fs, IStorage, IDiffHandler, ISelectiveEventHandler


class TestLocalDirectory(TestCase):
    def test_IStorage(self):
        verifyClass(IStorage, fs.LocalDirectory)

    def test_enforce_IStateManager(self):
        self.assertRaises(
            DoesNotImplement,
            fs.LocalDirectory("/foo/bar/").connect_state_manager,
            None,
        )

    def test_default_filter_param(self):
        self.assertIsInstance(
            fs.LocalDirectory("")._filt, dict,
            "default parameter (None) does not initialize an empty dict",
        )

        self.assertNot(
            fs.LocalDirectory("")._filt,
            "default filter is not empty",
        )

    def test_custom_filter_param(self):
        f = dict(include=["*"], exclude=[".*"])
        self.assertEquals(
            fs.LocalDirectory("", filters=f)._filt, f,
            "LocalDirectory's filters do not match input dict",
        )


class TestEventHandler(TestCase):
    def test_IDiffHandler(self):
        verifyClass(IDiffHandler, fs.EventHandler)

    def test_ISelectiveEventHandler(self):
        verifyClass(ISelectiveEventHandler, fs.EventHandler)
