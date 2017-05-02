#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from zope.interface import implementer

from pydio import job, ILooper, IMerger


@implementer(ILooper)
class DummyLooper:
    def start_loop(self, fn):
        pass

    def stop_loop(self):
        pass


@implementer(IMerger)
class DummyMerger:
    def __init__(self, fn):
        self.fn = fn

    def sync():
        self.fn()


class TestIJob(TestCase):
    def test_DirSync(self):
        self.assertTrue(
            job.IJob.implementedBy(job.DirSync),
            "DirSync does not implement IJob",
        )


# class TestDirSync(TestCase):
#     def test_
