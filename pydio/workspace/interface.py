#! /usr/bin/env python

# from zope.interface import Interface, Attribute
from twisted.application.service import IService


class ISynchronizable(IService):
    """Represents one side of a synchronization equation"""

    # idx = Attribute("Synchronization sequence index")

    def get_changes():
        """Get changes since last call"""

    def assert_ready():
        """Assert that ISynchronizable is available and consistent, i.e. it is
        ready to merge.
        """


__all__ = ["ISynchronizable"]
