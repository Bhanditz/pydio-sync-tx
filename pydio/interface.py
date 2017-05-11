#! /usr/bin/env python

from zope.interface import Interface, Attribute

from twisted.application.service import IService


class IMerger(Interface):
    """Implements merge logic for two or more ISynchronizables"""

    def sync():
        """Synchronize"""


__all__ = ["IMerger"]
