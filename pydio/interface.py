#! /usr/bin/env python
from zope.interface import Interface

from twisted.application.service import IService


class IMerger(Interface):
    """Implements merge logic for two or more ISynchronizables"""

    def sync():
        """Synchronize"""


class IMergeStrategy(Interface):
    """Responsible for implementing a merge algorithm that consumes a n streams
    of changes.
    """


class ISynchronizable(IService):
    """Represents one side of a synchronization equation"""


    def get_changes():
        """Get changes since last call"""

    def assert_ready():
        """Assert that ISynchronizable is available and consistent, i.e. it is
        ready to merge.
        """
