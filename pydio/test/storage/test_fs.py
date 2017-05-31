#! /usr/bin/env python
from twisted.trial.unittest import TestCase

import os.path as osp
from tempfile import TemporaryDirectory, TemporaryFile

from zope.interface import implementer
from zope.interface.verify import verifyClass, DoesNotImplement

from pydio.engine import IStateManager
from pydio.storage import fs, IStorage, IDiffHandler, ISelectiveEventHandler


@implementer(IStateManager)
class DummyStateManager:
    def create(self, inode, directory=False):
        raise NotImplementedError("dummy create")

    def delete(self, inode, directory=False):
        raise NotImplementedError("dummy delete")

    def modify(self, inode, directory=False):
        raise NotImplementedError("dummy modify")

    def move(self, inode, directory=False):
        raise NotImplementedError("dummy move")


class TestDummyStateManager(TestCase):
    """Canary test that ensures DummyStateManager satsifies IStateManager"""

    def test_IStateManager(self):
        verifyClass(IStateManager, DummyStateManager)


class TestLocalDirectory(TestCase):
    def test_IStorage(self):
        verifyClass(IStorage, fs.LocalDirectory)

    def test_connection_enforces_IStateManager(self):
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

    def test_handler_scheduling(self):
        stateman = DummyStateManager()
        with TemporaryDirectory() as path:
            localdir = fs.LocalDirectory(path)

            self.assertFalse(localdir._obs.emitters, "dirty observer")
            localdir.connect_state_manager(stateman)
            self.assertEqual(len(localdir._obs.emitters), 1,
                             "watch job not registerd")


class TestEventHandlerState(TestCase):
    def test_IDiffHandler(self):
        verifyClass(IDiffHandler, fs.EventHandler)

    def test_ISelectiveEventHandler(self):
        verifyClass(ISelectiveEventHandler, fs.EventHandler)

    def test_enforce_IStateManager(self):
        self.assertRaises(
            DoesNotImplement,
            fs.EventHandler,
            None,
            "/foo/bar/",
        )

    def test_default_filter_param(self):
        self.assertIsInstance(
            fs.EventHandler(DummyStateManager(), "")._filt, dict,
            "default parameter (None) does not initialize an empty dict",
        )

        self.assertNot(
            fs.EventHandler(DummyStateManager(), "")._filt,
            "default filter is not empty",
        )

    def test_custom_filter_param(self):
        f = dict(include=["*"], exclude=[".*"])
        self.assertEquals(
            fs.EventHandler(DummyStateManager(), "", filters=f)._filt, f,
            "LocalDirectory's filters do not match input dict",
        )

    def test_include_emtpy(self):
        include = fs.EventHandler(DummyStateManager(), "").include
        self.assertIsInstance(include, tuple,
                              "expected tuple, got {0}".format(type(include)))

        self.assertNot(include, "default include is not empty")

    def test_include_nonempty(self):
        h = fs.EventHandler(DummyStateManager(), "", filters=dict(include=["*"]))
        self.assertIn("*", h.include, "include wildcard not found")

    def test_include_nonempty(self):
        h = fs.EventHandler(DummyStateManager(), "", filters=dict(exclude=["*"]))
        self.assertIn("*", h.exclude, "exclude wildcard not found")

    def test_exclude_emtpy(self):
        exclude = fs.EventHandler(DummyStateManager(), "").exclude
        self.assertIsInstance(exclude, tuple,
                              "expected tuple, got {0}".format(type(exclude)))
        self.assertNot(exclude, "default exclude is not empty")


class TestEventHandlerPath(TestCase):
    def test_base_path_clean(self):
        p = "/foo/bar/"
        self.assertEquals(
            p, fs.EventHandler(DummyStateManager(), p)._base_path,
            "error normalizing non-trailing slash",
        )

    def test_base_path_no_trailing_slash(self):
        self.assertEquals(
            "/foo/bar/",
            fs.EventHandler(DummyStateManager(), "/foo/bar")._base_path,
            "error normalizing non-trailing slash",
        )

    def test_base_path_redundant_slash(self):
        self.assertEquals(
            "/foo/bar/",
            fs.EventHandler(DummyStateManager(), "/foo//bar/")._base_path,
            "error normalizing redundant slash",
        )

    def test_base_path_indirect_path(self):
        indirect_path = "/foo/.././foo/bar/"
        self.assertEquals(
            "/foo/bar/",
            fs.EventHandler(DummyStateManager(), indirect_path)._base_path,
            "error normalizing indirect path",
        )

    def test_relative_path_clean(self):
        base_path = "/foo/bar"
        full_path = "/foo/bar/baz.qux"
        expected = "baz.qux"

        h = fs.EventHandler(DummyStateManager(), base_path)
        self.assertEquals(h.relative_path(full_path), expected)

    def test_relative_path_redundant_slash(self):
        base_path = "/foo/bar"
        full_path = "/foo///bar//baz.qux"
        expected = "baz.qux"

        h = fs.EventHandler(DummyStateManager(), base_path)
        self.assertEquals(h.relative_path(full_path), expected)

    def test_relative_path_indirect_path(self):
        base_path = "/foo/bar"
        full_path = "/foo/../foo/bar/./baz.qux"
        expected = "baz.qux"

        h = fs.EventHandler(DummyStateManager(), base_path)
        self.assertEquals(h.relative_path(full_path), expected)


class TestEventHandlerInodeGeneration(TestCase):
    pass


class TestEventhandlerEventDispatch(TestCase):
    pass
