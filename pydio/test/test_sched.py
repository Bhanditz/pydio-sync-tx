#! /usr/bin/env python

from twisted.trial.unittest import TestCase

from pydio import ILooper
from pydio import sched


class TestILooper(TestCase):
    def test_ClockLoop(self):
        self.assertTrue(
            ILooper.implementedBy(sched.ClockLoop),
            "ClockLoop does not implement ILooper",
        )

    def test_PeriodicLoop(self):
        self.assertTrue(
            ILooper.implementedBy(sched.PeriodicLoop),
            "PeriodicLoop does not implement ILooper",
        )


class TestILooperConfig(TestCase):
    def test_from_int(self):
        looper = sched.looper_from_config({"frequency": 1})
        self.assertIsInstance(
            looper,
            sched.PeriodicLoop,
            "Expected PeriodicLoop from int, got {0}".format(type(looper))
        )

    def test_from_float(self):
        looper = sched.looper_from_config({"frequency": 1.0})
        self.assertIsInstance(
            looper,
            sched.PeriodicLoop,
            "Expected PeriodicLoopfrom float, got {0}".format(type(looper))
        )

    def test_from_time(self):
        from datetime import datetime, time
        looper = sched.looper_from_config({"frequency": datetime.now().time()})
        self.assertIsInstance(
            looper,
            sched.ClockLoop,
            "Expected PeriodicLoop from datetime.time, got {0}".format(type(looper))
        )


class TestIService(TestCase):
    def test_Scheduler_IService(self):
        from twisted.application.service import IService
        self.assertTrue(
            IService.implementedBy(sched.Scheduler),
            "Scheduler does not implement IService"
        )

    def test_Scheduler_IServiceCollection(self):
        from twisted.application.service import IServiceCollection
        self.assertTrue(
            IServiceCollection.implementedBy(sched.Scheduler),
            "Scheduler does not implement IServiceCollection"
        )
