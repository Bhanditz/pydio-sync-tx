#! /usr/bin/env python
from twisted.trial.unittest import TestCase

import os
import os.path as osp
from hashlib import md5
from shutil import rmtree
from tempfile import TemporaryDirectory, mkdtemp

from zope.interface import implementer
from zope.interface.verify import verifyClass, DoesNotImplement

from twisted.internet import defer

from watchdog import events

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

    def test_include_empty(self):
        include = fs.EventHandler(DummyStateManager(), "").include
        self.assertIsInstance(include, tuple,
                              "expected tuple, got {0}".format(type(include)))

        self.assertNot(include, "default include is not empty")

    def test_include_nonempty(self):
        h = fs.EventHandler(DummyStateManager(), "", filters=dict(include=["*"]))
        self.assertIn("*", h.include, "include wildcard not found")

    def test_exclude_nonempty(self):
        h = fs.EventHandler(DummyStateManager(), "", filters=dict(exclude=["*"]))
        self.assertIn("*", h.exclude, "exclude wildcard not found")

    def test_exclude_empty(self):
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


class TestEventHandlerInodeChecksum(TestCase):
    def setUp(self):
        self.ws = mkdtemp()
        self.h = fs.EventHandler(DummyStateManager(), self.ws)

    def tearDown(self):
        rmtree(self.ws)
        del self.ws, self.h

    @defer.inlineCallbacks
    def test_dir_on_create(self):
        p = osp.join(self.ws, "foo")
        ev = events.DirCreatedEvent(p)
        inode = dict(node_path=p)
        yield self.h._add_hash_to_inode(ev, inode)
        self.assertEquals(inode["md5"], fs.MD5_DIRECTORY)

    @defer.inlineCallbacks
    def test_file_on_create(self):
        content = b"now is the winter of our discontent"
        checksum = md5(content).hexdigest()

        p = osp.join(self.ws, "foo.txt")
        with open(p, "wb") as f:
            f.write(content)

        ev = events.FileCreatedEvent(p)
        inode = dict(node_path=p)
        yield self.h._add_hash_to_inode(ev, inode)
        self.assertIn("md5", inode, "checksum was not added to inode")
        self.assertEquals(checksum, inode["md5"])

    @defer.inlineCallbacks
    def test_dir_on_delete(self):
        inode = {}
        ev = events.DirDeletedEvent(osp.join(self.ws, "foo"))
        yield self.h._add_hash_to_inode(ev, inode)
        self.assertEquals(inode["md5"], fs.MD5_DIRECTORY)

    def test_file_on_delete(self):
        ev = events.FileDeletedEvent(osp.join(self.ws, "foo.txt"))
        return self.assertFailure(
            self.h._add_hash_to_inode(ev, {}),
            RuntimeError,
        )

    @defer.inlineCallbacks
    def test_dir_on_modify(self):
        p = osp.join(self.ws, "foo")
        ev = events.DirModifiedEvent(p)
        inode = dict(node_path=p)
        yield self.h._add_hash_to_inode(ev, inode)
        self.assertEquals(inode["md5"], fs.MD5_DIRECTORY)

    @defer.inlineCallbacks
    def test_file_on_modify(self):
        content = b"now is the winter of our discontent"
        checksum = md5(content).hexdigest()

        p = osp.join(self.ws, "foo.txt")
        with open(p, "wb") as f:
            f.write(content)

        ev = events.FileModifiedEvent(p)
        inode = dict(node_path=p)
        yield self.h._add_hash_to_inode(ev, inode)
        self.assertIn("md5", inode, "checksum was not added to inode")
        self.assertEquals(checksum, inode["md5"])

    @defer.inlineCallbacks
    def test_dir_on_move(self):
        p0 = osp.join(self.ws, "foo")
        p1 = osp.join(self.ws, "foo/bar")

        ev = events.DirMovedEvent(p0, p1)
        inode = dict(node_path=p1)
        yield self.h._add_hash_to_inode(ev, inode)
        self.assertEquals(inode["md5"], fs.MD5_DIRECTORY)

    @defer.inlineCallbacks
    def test_file_on_move(self):
        content = b"now is the winter of our discontent"
        checksum = md5(content).hexdigest()

        p0 = osp.join(self.ws, "foo.txt")
        p1 = osp.join(self.ws, "bar/foo.txt")

        path, _ = osp.split(p1)
        os.mkdir(path)
        with open(p1, "wb") as f:
            f.write(content)

        ev = events.FileMovedEvent(p0, p1)
        inode = dict(node_path=p1)
        yield self.h._add_hash_to_inode(ev, inode)
        self.assertIn("md5", inode, "checksum was not added to inode")
        self.assertEquals(checksum, inode["md5"])


class TestEventHandlerInodeStat(TestCase):
    def setUp(self):
        self.ws = mkdtemp()
        self.h = fs.EventHandler(DummyStateManager(), self.ws)

    def tearDown(self):
        rmtree(self.ws)
        del self.ws, self.h

    # @defer.inlineCallbacks
    # def test_dir_on_create(self):
    #     pass

    # @defer.inlineCallbacks
    # def test_file_on_create(self):
    #     pass
    #
    # @defer.inlineCallbacks
    # def test_dir_on_delete(self):
    #     pass
    #
    # def test_file_on_delete(self):
    #     pass
    #
    # @defer.inlineCallbacks
    # def test_dir_on_modify(self):
    #     pass
    #
    # @defer.inlineCallbacks
    # def test_file_on_modify(self):
    #     pass
    #
    # @defer.inlineCallbacks
    # def test_dir_on_move(self):
    #     pass
    #
    # @defer.inlineCallbacks
    # def test_file_on_move(self):
    #     pass


class TestEventHandlerNewInode(TestCase):
    def setUp(self):
        self.ws = mkdtemp()
        self.wd = mkdtemp()
        self.h = fs.EventHandler(DummyStateManager(), self.ws)

    def tearDown(self):
        rmtree(self.ws)
        del self.ws, self.h

    @defer.inlineCallbacks
    def test_dir_on_create(self):
        p = osp.join(self.ws)

        # test delete events logic
        ev = events.DirCreatedEvent(p)
        d = yield self.h.new_node(ev)
        self.assertEquals(d['node_path'], p)
        self.assertIn('md5', d)
        self.assertIn('stat_result', d)

    # @defer.inlineCallbacks
    # def test_file_on_create(self):
    #     pass
    #
    @defer.inlineCallbacks
    def test_dir_on_delete(self):
        p = osp.join(self.ws)

        # test delete events logic
        ev = events.DirDeletedEvent(p)
        d = yield self.h.new_node(ev)
        self.assertEquals(d['node_path'], p)
        self.assertNotIn('md5', d)
        self.assertNotIn('stat_result', d)

    # def test_file_on_delete(self):
    #     pass
    #
    # @defer.inlineCallbacks
    # def test_dir_on_modify(self):
    #     pass
    #
    # @defer.inlineCallbacks
    # def test_file_on_modify(self):
    #     pass
    #
    @defer.inlineCallbacks
    def test_dir_on_move(self):
        sp = osp.join(self.ws)
        dp = osp.join(self.wd)

        # test move events logic
        ev = events.DirMovedEvent(sp, dp)
        d = yield self.h.new_node(ev)
        self.assertEquals(d['node_path'], dp)
        self.assertIn('md5', d)
        self.assertIn('stat_result', d)

    # @defer.inlineCallbacks
    # def test_file_on_move(self):
    #     pass


class TestEventhandlerEventDispatch(TestCase):
    def setUp(self):
        self.ws = mkdtemp()
        self.h = fs.EventHandler(DummyStateManager(), self.ws)

    def tearDown(self):
        rmtree(self.ws)
        del self.ws, self.h

    # def test_filter_event(self):
    #     pass

    # @defer.inlineCallbacks
    # def test_dir_on_created(self):
    #     pass

    # @defer.inlineCallbacks
    # def test_file_on_created(self):
    #     pass
    #
    # @defer.inlineCallbacks
    # def test_dir_on_deleted(self):
    #     pass
    #
    # def test_file_on_deleted(self):
    #     pass
    #
    # @defer.inlineCallbacks
    # def test_dir_on_modified(self):
    #     pass
    #
    # @defer.inlineCallbacks
    # def test_file_on_modified(self):
    #     pass
    #
    # @defer.inlineCallbacks
    # def test_dir_on_moved(self):
    #     pass
    #
    # @defer.inlineCallbacks
    # def test_file_on_moved(self):
    #     pass
