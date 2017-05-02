#! /usr/bin/env python
from zope.interface import Interface


class IJob(Interface):
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
    """A class that can perform a merge of two or more ISynchronizables"""

    def sync():
        """Synchronize"""
