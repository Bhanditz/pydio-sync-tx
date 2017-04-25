#! /usr/bin/env python
import datetime

from zope.interface import Interface, implementer

from twisted.logger import Logger
from twisted.application.service import Service
from twisted.internet.task import LoopingCall, deferLater

from watchdog.observers import Observer


# DEFAULT_WHITELIST = ("*",)
# DEFAULT_BLACKLIST = (
#     ".*",
#     "*/.*",
#     "/recycle_bin*",
#     "*.pydio_dl",
#     "*.DS_Store",
#     ".~lock.*",
#     "~*",
#     "*.xlk",
#     "*.tmp"
# )


class ISynchronizable(Interface):
    """Represents one side of a synchronization equation"""

    def getChanges(idx):
        """Get changes with a higher index than `idx`"""


class IMerger(Interface):
    """A class that can perform a merge of two or more ISynchronizables"""

    def sync():
        """Synchronize"""


@implementer(ISynchronizable)
class PydioServerWorkspace:
    """An ISynchronizable interface to a remote Pydio workspace"""

    def getChanges(idx):
        pass


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
        pass


@implementer(IMerger)
class SQLiteMerger(Service):
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
        pass

# def filter_events(method):
#     """filter_events decorates watchdog.events.EventHandler methods such that
#     events that are not inclusively matched by a job's whitelist and exclusively
#     matched by that same job's blacklist are ignored.
#     """
#     @wraps(method)
#     def wrapper(self, event):
#         included = match_any(self.includes, event.dest_path)
#         excluded = match_any(self.excludes, event.dest_path)
#         if included and not excluded:
#             return method(self, event)
#     return wrapper
#
#
# def match_any(globlist, path):
#     """Returns true if the path is matched by at least one of the UNIX wildcard
#     expressions in `globlist`.
#     """
#     return any(map(lambda glb: fnmatch(path, glb), globlist))



class Job(Service):
    """Implements watchdog.events.EventHandler.  When a relevant event is
    received, a sync run is scheduled on the reactor.
    """
    log = Logger()

    def __init__(self, name, merger, starter=None):
        self.name = name  # enforce named services
        self._starter = starter  # if None, manual sync

        # Ensure local & remote targets are ISynchronizable
        if not IMerger.implementedBy(merger):
            raise TypeError("{0} does not implement IMerger".format(type(merger)))

        self.merger = merger

        # self.schedule = cfg.pop("frequency", "auto")
        # self.direction = cfg.pop("direction", "bi")
        # self.solve = cfg.pop("solve", "both")
        #
        # self.workspace = cfg.pop("workspace")
        # self.localdir = cfg.pop("directory")
        # self.server = cfg.pop("server")
        #
        # self.includes = cfg.pop("includes", DEFAULT_WHITELIST)
        # self.excludes = cfg.pop("excludes", DEFAULT_BLACKLIST)
        #
        # self.trust_ssl = cfg.pop("trust_ssl", False)
        #
        # self.timeout = cfg.pop("timeout", 20)
        # self._running = cfg.pop("active", True)


    def startService(self):
        super(Job, self).startService()
        if self._starter is None:
            self.log.info("{name} has not been scheduled", name=self.name)
            return

        return self._starter()

    def stopService(self):
        super(Job, self).stopService()
        if self.loop is not None:
            return loop.stop()
