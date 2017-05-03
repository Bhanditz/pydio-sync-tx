#! /usr/bin/env python
import yaml
import datetime
import os.path as osp

from zope.interface import implementer

from twisted.logger import Logger
from twisted.application.service import MultiService
from twisted.internet.task import LoopingCall, deferLater

from . import ILooper, IMerger
from .job import DirSync
from .merger import LocalWorkspace, PydioServerWorkspace, SQLiteMerger
from .watchdog import LocalDirectoryWatcher, SQLiteEventHandler


@implementer(ILooper)
class ClockLoop:
    def __init__(self, t):
        self._looping_call = None
        if not isinstance(t, datetime.time):
            raise TypeError(
                "expected datetime.datetime, got {0}".format(type(t))
            )
        self.scheduled_time = t

    @property
    def next_run(self):
        """Returns a datetime.datetime with the next scheduled run"""
        return datetime.datetime(
            year=t0.year,
            month=t0.month,
            day=t0.day,
            hour=self.scheduled_time.hour,
            minute=self.scheduled_time.minute,
        )

    def _calc_time_delta(self):
        """calc_time_delta takes a datetime.time, `t`, and returns a
        datetime.timedelta representing the interval between now and the next
        occurrence of `t` on a 24h clock.

        t : datetime.time
            The target time.

        return : datetime.timedelta
            The interval between now and the target time.
        """
        raise NotImplementedError

    def start_loop(self, fn):
        if self._looping_call is not None:
            raise RuntimeError("Loop already running")

        raise NotImplementedError

    def stop_loop(self):
        raise NotImplementedError


@implementer(ILooper)
class PeriodicLoop:
    def __init__(self, interval):
        self.interval = interval
        self._looping_call = None

    def start_loop(self, fn):
        if self._looping_call is not None:
            raise RuntimeError("Loop already started")

        self._looping_call = LoopingCall(fn)
        return self._looping_call.start(self.interval)

    def stop_loop(self):
        return self._looping_call.stop()


def looper_from_config(cfg):
    """`looper_from_config` type-checks the `freq` parameter to construct an
    appropriate ILooper.

    If `freq` is a numeric type, a configured `PeriodicLoop` will be returned.
    If `freq` is a `datetime.time`, a `ClockLoop` will be returned.

    freq : int, float or datetime.time
        Frequency parameter for the ILooper instance

    return : ILooper
    """

    freq = cfg.pop("frequency", 10)
    if isinstance(freq, (int, float)):  # freq represents seconds
        return PeriodicLoop(freq)
    elif isinstance(freq, datetime.time):  # schedule for specific time
        return ClockLoop(freq)
    raise TypeError("cannot build ILooper from {0}".format(type(freq)))


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
            self.addService(self.assemble_job_from_config(name, cfg))

    def __str__(self):
        return "<Scheduler with {0} jobs>".format(len(self.services))

    @staticmethod
    def assemble_job_from_config(name, cfg):
        """Convenience method to instantiate IJob components, string them
        together, and return an IJob that is ready to be passed to
        `IService.addService`.

        You probably shouldn't be calling this directly.
        """
        local = LocalWorkspace.from_config(cfg)
        remote = PydioServerWorkspace.from_config(cfg)

        merger = SQLiteMerger(local, remote)
        looper = looper_from_config(cfg)

        job = DirSync(name, looper, merger)

        handler = SQLiteEventHandler.from_config("pydio.sqlite", cfg)

        watcher = LocalDirectoryWatcher()
        watcher.register_handler(cfg["directory"], handler)

        job.addService(watcher)
        return job

    def startService(self):
        self.log.info("Starting scheduler")
        super().startService()

    def stopService(self):
        self.log.warn("Stopping scheduler")
        super().stopService()
