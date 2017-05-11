#! /user/bin/env python
import os.path as osp
from functools import partial
from contextlib import contextmanager

from zope.interface import implementer
from zope.interface.verify import verifyObject

from twisted.logger import Logger
from twisted.internet import defer
from twisted.enterprise import adbapi
from twisted.internet.threads import deferToThread
from twisted.application.service import MultiService

from . import ISynchronizable, IMerger


class ConcurrentMerge(RuntimeError):
    """Signals that a new merge was attempted before the previous one finished
    """


@implementer(IMerger)
class SQLiteMerger(MultiService):
    """Synchronize two ISynchronizables using an SQLite table"""

    log = Logger()

    def __init__(self, local, remote, direction=None):
        super().__init__()

        verifyObject(ISynchronizable, local)
        self.local = local
        self.addService(local)

        verifyObject(ISynchronizable, remote)
        self.remote = remote
        self.addService(remote)

        self.direction = direction
        self._locked = False

    @property
    def merging(self):
        return self._locked

    def _fetch_changes(self):
        """Get local and remote changes"""
        # equivalent to _compute_changes
        return defer.gatherResults([
            self.local.get_changes(),
            self.remote.get_changes(),
        ])

    @contextmanager
    def _lock_for_sync_run(self):
        """Returns a context manager that locks the SQLiteMerger instance such
        that new sync runs cannot begin until the present one terminates.
        """
        if self.merging:
            raise ConcurrentMerge

        self._locked = True
        try:
            yield
        finally:
            self._locked = False

    def sync(self):
        try:
            d = dict(up=":==>", down="<==:").get(self.direction, "<==>")
            self.log.info("Merging {m.local} {dir} {m.remote}", m=self, dir=d)

            # self._merge handles locking and returns a Deferred
            return self._merge()

        except ConcurrentMerge:
            self.log.warn("Previous merge not terminated.  Skipping.")

    @defer.inlineCallbacks
    def _merge(self):
        with self._lock_for_sync_run():
            # TODO init_global_progress() (I think this is needed for WebUI feedback)

            yield self.assert_volumes_ready()
            yield self._fetch_changes()

            # NOTE : Consider creating an interface, IMergeStrategy, that
            #        abstracts away the details of the merge algoritm.

            # merge()  # TODO

    def assert_volumes_ready(self):  # exported because it's a pure function
        """Verify that local and remote sync targets are present, accessible and
        in consistent states (i.e.:  ready to merge).
        """
        return defer.gatherResults(map(defer.maybeDeferred, [
            self.local.assert_ready,
            self.remote.assert_ready,
        ])).addErrback(lambda f: f.value.subFailure.raiseException())
