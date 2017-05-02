#! /usr/bin/env python
import datetime

from zope.interface import Interface, implementer
from zope.interface.verify import verifyObject

from twisted.logger import Logger
from twisted.application.service import Service

from watchdog.observers import Observer

from . import IJob, IMerger, ILooper

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


@implementer(IJob)
class DirSync(Service):
    """Implements watchdog.events.EventHandler.  When a relevant event is
    received, a sync run is scheduled on the reactor.

    name : str
        The sync job's name

    merger : IMerger

    looper : ILooper
    """
    log = Logger()

    def __init__(self, name, merger, looper):
        self.name = name  # enforce named services

        verifyObject(IMerger, merger)
        self._merger = merger

        verifyObject(Ilooper, looper)
        self._looper = looper

    def do_job(self):
        """Run the sync job.

        This exported method serves as an interface from which manual sync jobs
        can be triggered by the scheduler.
        """
        self._merger.sync()

    def startService(self):
        super(DirSync, self).startService()
        if self._looper is None:
            self.log.info("{name} synchronization set to manual", name=self.name)
            return

        return self._looper.start_loop(self.do_job)

    def stopService(self):
        super(DirSync, self).stopService()
        if self._looper is not None:
            return self._looper.stop_loop()
