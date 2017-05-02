#! /usr/bin/env python
import yaml
import datetime

from zope.interface import Interface, implementer

from twisted.logger import Logger
from twisted.application.service import MultiService
from twisted.internet.task import LoopingCall, deferLater

from .job import Job
from .merger import LocalWorkspace, PydioServerWorkspace, SQLiteMerger


class ILooper(Interface):
    """Provides fine-grained control over periodic, deferred actions."""

    def start_loop(fn):
        """Enter the loop, calling `fn` at each iteration"""

    def stop_loop():
        """Exit the loop"""


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


def looper_from_config(freq):
    """`looper_from_config` type-checks the `freq` parameter to construct an
    appropriate ILooper.

    If `freq` is a numeric type, a configured `PeriodicLoop` will be returned.
    If `freq` is a `datetime.time`, a `ClockLoop` will be returned.

    freq : int, float or datetime.time
        Frequency parameter for the ILooper instance

    return : ILooper
    """
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
        super(Scheduler, self).__init__()

        # load jobs
        for name, cfg in jobs.items():
            self.log.info("Configuring {name}", name=name)

            # TODO : configure

            local = LocalWorkspace(cfg["directory"])
            remote = PydioServerWorkspace()
            merger = SQLiteMerger(local, remote)

            looper = looper_from_config(freq=cfg.pop("frequency", 10))

            self.addService(Job(name, merger, looper))

    def __str__(self):
        return "<Scheduler with {0} jobs>".format(len(self.services))

    def startService(self):
        self.log.info("Starting scheduler")
        super(Scheduler, self).startService()

    def stopService(self):
        self.log.warn("Stopping scheduler")
        super(Scheduler, self).stopService()
