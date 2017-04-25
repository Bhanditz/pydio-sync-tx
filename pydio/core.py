#! /usr/bin/env python
import json

from watchdog.observers import Observer

from twisted.logger import Logger
from twisted.internet.threads import deferToThread
from twisted.application.service import MultiService

from .job import Job


class Scheduler(MultiService):
    """Scheduler is responsible for managing the lifecycle of Job instances as
    well as managing synchronization runs.
    """
    log = Logger()

    def __init__(self, job_cfg_path):
        """job_cfg_path : str
            String containing a path to a valid job configuration file
        """
        super(Scheduler, self).__init__()

        # initialize observer
        self._observer = Observer()

        # initialize continuous diff merger

        # load jobs
        with open(job_cfg_path) as f:
            for job in map(Job, *zip(*json.load(f).iteritems())):
                self.addService(job)
                self._observer.schedule(Job, job.localdir, recursive=True)
                self.log.info("Scheduled job {job.name}", job=job)

    def __str__(self):
        return "<Scheduler with {0} jobs>".format(len(self.services))

    def startService(self):
        self.log.info("Starting scheduler")
        super(Scheduler, self).startService()
        self._observer.start()

    def stopService(self):
        self.log.warn("Stopping scheduler")
        super(Scheduler, self).stopService()
        self._observer.stop()
        return deferToThread(self._observer.join)
