#! /usr/bin/env python
from functools import wraps
from fnmatch import fnmatch  # unix filename pattern matching

from twisted.application.service import Service

from watchdog.events import FileSystemEventHandler

DEFAULT_WHITELIST = ("*",)
DEFAULT_BLACKLIST = (
    ".*",
    "*/.*",
    "/recycle_bin*",
    "*.pydio_dl",
    "*.DS_Store",
    ".~lock.*",
    "~*",
    "*.xlk",
    "*.tmp"
)


def filter_events(method):
    """filter_events decorates watchdog.events.EventHandler methods such that
    events that are not inclusively matched by a job's whitelist and exclusively
    matched by that same job's blacklist are ignored.
    """
    @wraps(method)
    def wrapper(self, event):
        included = match_any(self.includes, event.dest_path)
        excluded = match_any(self.excludes, event.dest_path)
        if included and not excluded:
            return method(self, event)
    return wrapper


def match_any(globlist, path):
    """Returns true if the path is matched by at least one of the UNIX wildcard
    expressions in `globlist`.
    """
    return any(map(lambda glb: fnmatch(path, glb), globlist))


class Job(Service, FileSystemEventHandler):
    """Implements watchdog.events.EventHandler.  When a relevant event is
    received, a sync run is scheduled on the reactor.
    """
    def __init__(self, obs, name, cfg):
        self._observer = obs

        self.name = name  # enforce named services

        self.schedule = cfg.pop("frequency", "auto")
        self.direction = cfg.pop("direction", "bi")
        self.solve = cfg.pop("solve", "both")

        self.workspace = cfg.pop("workspace")
        self.localdir = cfg.pop("directory")
        self.server = cfg.pop("server")

        self.includes = cfg.pop("includes", DEFAULT_WHITELIST)
        self.excludes = cfg.pop("excludes", DEFAULT_BLACKLIST)

        self.trust_ssl = cfg.pop("trust_ssl", False)

        self.timeout = cfg.pop("timeout", 20)
        self._running = cfg.pop("active", True)

        # create contdiffmerger

    def startService(self):
        super(Job, self).startService()
        raise NotImplementedError

    def stopService(self):
        super(Job, self).stopService()
        raise NotImplementedError

    @filter_events
    def on_moved(self, event):
        """Called when a file or a directory is moved or renamed.

        :param event:
            Event representing file/directory movement.
        :type event:
            :class:`DirMovedEvent` or :class:`FileMovedEvent`
        """

    @filter_events
    def on_created(self, event):
        """Called when a file or directory is created.

        :param event:
            Event representing file/directory creation.
        :type event:
            :class:`DirCreatedEvent` or :class:`FileCreatedEvent`
        """

    @filter_events
    def on_deleted(self, event):
        """Called when a file or directory is deleted.

        :param event:
            Event representing file/directory deletion.
        :type event:
            :class:`DirDeletedEvent` or :class:`FileDeletedEvent`
        """

    @filter_events
    def on_modified(self, event):
        """Called when a file or directory is modified.

        :param event:
            Event representing file/directory modification.
        :type event:
            :class:`DirModifiedEvent` or :class:`FileModifiedEvent`
        """
