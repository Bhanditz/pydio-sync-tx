from zope.interface import Interface, Attribute

from twisted.application.service import IService


class IWatcher(IService):
    """Monitors a directory for changes and notifies an EventHandler"""

    def register_handler(path, handler, recursive=True):
        """Register an IEventHandler to the watcher and receive notifications
        for events pertaining to the specified path.
        """


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


__all__ = [
    "IWatcher",
    "IDiffEngine",
    "IStateManager",
    "IDiffStream",
    "IEventHandler",
    "ISelectiveEventHandler",
    "IDiffHandler",
]
