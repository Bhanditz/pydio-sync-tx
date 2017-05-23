#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from zope.interface.verify import verifyClass

from pydio.storage import fs, IStorage, IDiffHandler, ISelectiveEventHandler


class TestEventHandler(TestCase):
    def test_IDiffHandler(self):
        verifyClass(IDiffHandler, fs.EventHandler)

    def test_ISelectiveEventHandler(self):
        verifyClass(ISelectiveEventHandler, fs.EventHandler)


class TestLocalDirectory(TestCase):
    def test_IStorage(self):
        verifyClass(IStorage, fs.LocalDirectory)
