#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from zope.interface import implementer
from zope.interface.verify import DoesNotImplement

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

    def sync(self):
        self.fn()


class TestIJob(TestCase):
    def test_DirSync(self):
        self.assertTrue(
            job.IJob.implementedBy(job.SyncJob),
            "SyncJob does not implement IJob",
        )


class TestDirSyncIfaceEnforcement(TestCase):

    looper = DummyLooper()
    merger = DummyMerger(None)

    def test_enforce_IMerger(self):
        self.assertRaises(
            DoesNotImplement,
            job.SyncJob,
            "test",
            self.looper,
            None,
        )

    def test_enforce_ILooper(self):
        self.assertRaises(
            DoesNotImplement,
            job.SyncJob,
            "test",
            None,
            self.merger,
        )


class TestJobExecution(TestCase):
    def test_do_job(self):
        class JobExecuted(RuntimeError):
            pass

        def _run():
            raise JobExecuted

        ds = job.SyncJob("test", DummyLooper(), DummyMerger(_run))
        self.assertRaises(JobExecuted, ds.do_job)
