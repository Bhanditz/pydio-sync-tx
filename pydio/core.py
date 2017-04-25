#! /usr/bin/env python
import json

from twisted.logger import Logger
from twisted.internet.threads import deferToThread
from twisted.application.service import MultiService

from .job import Job, PydioServerWorkspace, LocalWorkspace, SQLiteMerger


def calc_time_delta(t):
    """calc_time_delta takes a datetime.time, `t`, and returns a
    datetime.timedelta representing the interval between now and the next
    occurrence of `t` on a 24h clock.

    t : datetime.time
        The target time.

    return : datetime.timedelta
        The interval between now and the target time.
    """
    t0 = datetime.datetime.now()
    t1 = datetime.datetime(
        year=t0.year, month=t0.month, day=t0.day, hour=t.hour, minute=t.minute
    )

    dt = t1 - t0
    if dt.days < 0:
        raise NotImplementedError("need to deal with negative timedelta")

    return dt


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

        # load jobs
        with open(job_cfg_path) as f:
            for name, cfg in json.load(f).iteritems():
                self.log.info("Configuring {name}", name=name)

                # TODO : configure

                local = LocalWorkspace()
                remote = RemoteWorkspace()
                merger = SQLiteMerger(local, remote)

                s = self.build_schedule(name, cfg, merger)
                job = Job(name, merger, starter=s)

                self.log.info("Scheduling {name}", name=name)
                self.addService(job)

    def build_schedule(self, name, cfg, merger):
        freq = cfg.get("frequency", 10)  # default to auto every 10s
        if freq is None:
            return

        loop = LoopingCall(merger.sync)

        if isinstance(freq, (int, float)):
            msg = "Scheduling {name} with autosync every {freq}s"
            self.log.info(msg, name=name, freq=freq)
            return loop.start(interval)
        elif isinstance(freq, datetime.time):
            t = cfg["start_time"]
            start_time = datetime.time(hour=t["h"], minute=t["m"])

            msg = "Scheduling {name} with periodic sync at {t}"
            self.log.info(msg, name=name, t=start_time)

            from twisted.internet import reactor
            return deferLater(
                reactor,
                calc_time_delta(start_time).total_seconds(),
                merger.sync,
            ).addCallback(
                lambda _ : loop.start(86400)  # 24h
            )
        else:
            emsg = "invalid value for synch frequency parameter: {0}"
            raise ValueError(emsg.format(self._frequency))

    def __str__(self):
        return "<Scheduler with {0} jobs>".format(len(self.services))

    def startService(self):
        self.log.info("Starting scheduler")
        super(Scheduler, self).startService()

    def stopService(self):
        self.log.warn("Stopping scheduler")
        super(Scheduler, self).stopService()
