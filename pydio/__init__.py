#! /usr/bin/env python
from zope.interface import Interface


class IJob(Interface):
    """A pre-configured task that can be called repeatedly.
    IJobs are scheduled for execution by pydio.sched.Scheduler.
    """

    def do_job():
        """Perform one iteration of the job at hand"""


class ILooper(Interface):
    """Provides fine-grained control over periodic, deferred actions."""

    def start_loop(fn):
        """Enter the loop, calling `fn` at each iteration"""

    def stop_loop():
        """Exit the loop"""


class ISynchronizable(Interface):
    """Represents one side of a synchronization equation"""

    def get_changes(idx):
        """Get changes with a higher index than `idx`"""

    def assert_ready():
        """Assert that ISynchronizable is available and consistent, i.e. it is
        ready to merge.
        """


class IMerger(Interface):
    """IMplements merge logic for two or more ISynchronizables"""

    def sync():
        """Synchronize"""
