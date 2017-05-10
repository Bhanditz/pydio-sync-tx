#! /usr/bin/env python
from zope.interface import implementer
from zope.interface.verify import verifyObject

from twisted.logger import Logger
from twisted.application.service import MultiService

from . import IJob, IMerger, ILooper


@implementer(IJob)
class SyncJob(MultiService):
    """Implements watchdog.events.EventHandler.  When a relevant event is
    received, a sync run is scheduled on the reactor.

    name : str
        The sync job's name

    merger : IMerger

    looper : ILooper
    """
    log = Logger()

    def __init__(self, name, looper, merger):
        super().__init__()
        self.name = name  # enforce named services

        verifyObject(ILooper, looper)
        self._looper = looper

        verifyObject(IMerger, merger)
        self._merger = merger

    def do_job(self):
        """Run the sync job.

        This exported method serves as an interface from which manual sync jobs
        can be triggered by the scheduler.
        """
        self._merger.sync()

    def startService(self):
        super().startService()
        if self._looper is None:
            self.log.info("{name} synchronization set to manual", name=self.name)
            return

        return self._looper.start_loop(self.do_job)

    def stopService(self):
        super().stopService()
        if self._looper is not None:
            return self._looper.stop_loop()
