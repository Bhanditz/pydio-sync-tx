#! /user/bin/env python

from zope.interface import Interface, implementer


class ISynchronizable(Interface):
    """Represents one side of a synchronization equation"""

    def getChanges(idx):
        """Get changes with a higher index than `idx`"""


@implementer(ISynchronizable)
class PydioServerWorkspace:
    """An ISynchronizable interface to a remote Pydio workspace"""

    def getChanges(idx):
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

    def getChanges(idx):
        raise NotImplementedError


class IMerger(Interface):
    """A class that can perform a merge of two or more ISynchronizables"""

    def sync():
        """Synchronize"""


@implementer(IMerger)
class SQLiteMerger:
    """Synchronize two ISynchronizables using an SQLite table"""

    def __init__(self, local, remote):
        emsg = "{0} does not implement ISynchronizable"

        if not ISynchronizable.implementedBy(local):
            raise TypeError(emsg.format(type(local)))
        self.local = local

        if not ISynchronizable.implementedBy(remote):
            raise TypeError(emsg.format(type(remote)))
        self.local = local

    #@inlineCallbacks
    def sync(self):
        raise  NotImplementedError
