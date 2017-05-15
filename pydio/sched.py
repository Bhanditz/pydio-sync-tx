#! /usr/bin/env python
from twisted.logger import Logger
from twisted.application.service import MultiService
from twisted.application.internet import TimerService

from .engine import sqlite
from .merger import SQLiteMerger
from .synchronizable import Workspace
from .storage.fs import LocalDirectory


class Job(MultiService):

    log = Logger()

    def __init__(self, name, merger, trigger):
        super().__init__()
        self.name = name
        self.addService(merger)  # don't verify; we only need it as an IService
        self.addService(trigger)

    def startService(self):
        self.log.info("starting {job.name}", job=self)
        super().startService()

    def stopService(self):
        self.log.info("stopping {job.name}", job=self)


class Scheduler(MultiService):
    """Scheduler is responsible for managing the lifecycle of Job instances as
    well as managing synchronization runs.
    """
    log = Logger()

    def __init__(self, jobs):
        """
        jobs : dict
            {job name : configuration options}

        """
        super().__init__()

        # For each job configuration, instantiate the requisite components
        # and string everything together using (multi)service(s).
        for name, cfg in jobs.items():
            self.log.info("Configuring {name}", name=name)

            lw = Workspace(
                sqlite.Engine(),
                LocalDirectory(path=cfg["directory"], filters=cfg["filters"]),
            )

            merger = SQLiteMerger(lw, rw)
            trigger = TimerService(cfg.pop("frequency", .025), merger.sync)

            self.addService(Job(name, merger, trigger))

    def __str__(self):
        return "<Scheduler with {0} jobs>".format(len(self.services))

    def startService(self):
        self.log.info("starting scheduler service")
        super().startService()

    def stopService(self):
        self.log.warn("stopping scheduler service")
        super().stopService()
