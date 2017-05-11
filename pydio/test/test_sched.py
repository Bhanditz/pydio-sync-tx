#! /usr/bin/env python
from twisted.trial.unittest import TestCase

from twisted.application.service import IService, IServiceCollection

from pydio import sched


class TestIService(TestCase):
    def test_Scheduler_IService(self):
        self.assertTrue(
            IService.implementedBy(sched.Scheduler),
            "Scheduler does not implement IService"
        )

    def test_Scheduler_IServiceCollection(self):
        self.assertTrue(
            IServiceCollection.implementedBy(sched.Scheduler),
            "Scheduler does not implement IServiceCollection"
        )

    def test_Job_IService(self):
        self.assertTrue(
            IService.implementedBy(sched.Job),
            "Job does not implement IService"
        )
