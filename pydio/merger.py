#! /user/bin/env python
from contextlib import contextmanager

from zope.interface import Interface, implementer
from zope.interface.verify import verifyObject

from twisted.logger import Logger
from twisted.internet import defer


class ISynchronizable(Interface):
    """Represents one side of a synchronization equation"""

    def get_changes(idx):
        """Get changes with a higher index than `idx`"""


@implementer(ISynchronizable)
class PydioServerWorkspace:
    """An ISynchronizable interface to a remote Pydio workspace"""

    # PydioSdk(
    #         job_config["server"],
    #         ws_id=self.ws_id,
    #         remote_folder=job_config["remote_folder"],
    #         user_id=job_config["user_id"],
    #         device_id=ConfigManager().device_id,
    #         skip_ssl_verify=job_config["trust_ssl"],
    #         proxies=ConfigManager().defined_proxies,
    #         timeout=job_config["timeout"]
    #     )

    # def __init__(self):
    #     pass

    @defer.inlineCallbacks
    def get_changes(self, idx):
        raise NotImplementedError


@implementer(ISynchronizable)
class LocalWorkspace:
    """An ISynchronizable interface to a local Pydio workspace directory"""

    def __init__(self, dir):
        self._dir = dir

    @property
    def dir(self):
        """Local directory being watched"""
        return self._dir

    @defer.inlineCallbacks
    def get_changes(self, idx):
        raise NotImplementedError


class IMerger(Interface):
    """A class that can perform a merge of two or more ISynchronizables"""

    def sync():
        """Synchronize"""


class ConcurrentMerge(RuntimeError):
    """Signals that a new merge was attempted before the previous one finished
    """


@implementer(IMerger)
class SQLiteMerger:
    """Synchronize two ISynchronizables using an SQLite table"""

    log = Logger()

    def __init__(self, local, remote, direction=None):
        verifyObject(ISynchronizable, local)
        self.local = local

        verifyObject(ISynchronizable, remote)
        self.remote = remote

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
            self.log.info("Merging {m.local} {arrow} {m.remote}", m=self, arrow=d)

            # self._merge handles locking and returns a Deferred
            return self._merge()

        except ConcurrentMerge:
            self.log.warn("Previous merge not terminated.  Skipping.")

    @defer.inlineCallbacks
    def _merge(self):
        with self._lock_for_sync_run():
            # TODO init_global_progress()

            # self._check_target_volumes()
            # self._load_directory_snapshots()
            # self._wait_db_lock()

            yield self._fetch_changes()
            # merge()
