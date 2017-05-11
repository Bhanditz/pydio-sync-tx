#! /usr/bin/env python

from zope.interface import Interface, Attribute

from twisted.application.service import IService


class IDiffEngine(IService):
    """IDiffEngine provides a layer of abstraction around the computation of
    file and directory diffs based on changes to some underlying state (e.g. to
    the filesystem)
    """

    updater = Attribute("IStateManager")
    stream = Attribute("IDiffStream")

    def _start():
        """Start the engine.  May return a deferred
        Intended to facilitate testing.
        """

    def _stop():
        """Stop tracking state and producing diffs.
        Note that it is acceptable for an implementation to store diffs in a
        buffer, so there may be changes to process after calling `shutdown`.

        Intended to facilitate testing.
        """


class IStateManager(Interface):
    """IStateManager receives changes to inodes and updates the state of an
    ISynchronizable, usually triggering the creation of a diff as a side-effect.
    """

    def create(inode, directory=False):
        """create an inode"""

    def delete(inode, directory=False):
        """delete an inode"""

    def modify(inode, directory=False):
        """modify an inode"""

    def move(inode, directory=False):
        """move an inode"""


class IDiffStream(Interface):
    """Produces batches of diffs"""

    def next():
        """Produce next batch of diffs"""
