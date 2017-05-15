#! /usr/bin/env python
from zope.interface import Attribute

from twisted.application.service import IService


class IStorage(IService):
    """Implements the storage layer within an ISynchronizable"""

    def connect(IDiffEngine):
        """Connect the storage to an IDiffEngine"""


class IEventHandler(IService):
    """Receive events from an IWatcher"""

    def dispatch(ev):
        """Dispatches events to the appropriate methods"""

    def on_any_event(ev):
        """Catch-all callback"""


class ISelectiveEventHandler(IEventHandler):
    include = Attribute("whitelist of UNIX glob patterns")
    exclude = Attribute("blacklist of UNIX glob patterns")

    def match_any(globlist, path):
        """Implements the matching logic using `include` and `exclude`"""


class IDiffHandler(IEventHandler):
    """Handle events pertaining to basic resource modification"""

    def on_created(ev):
        """Called when an inode is created"""

    def on_deleted(ev):
        """Called when an inode is deleted"""

    def on_modified(ev):
        """Called when an existing inode is modified"""

    def on_moved(ev):
        """Called when an existing inode is moved"""
