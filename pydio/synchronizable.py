#! /usr/bin/env python
from zope.interface import implementer
from zope.interface.verify import verifyObject

from twisted.application.service import MultiService

from . import ISynchronizable
from .storage import IStorage
from .engine import IDiffEngine


@implementer(ISynchronizable)
class Workspace(MultiService):
    def __init__(self, iengine, istorage):
        super().__init__()
        verifyObject(IDiffEngine, iengine)
        self.iengine = iengine
        self.addService(iengine)

        verifyObject(IStorage, istorage)
        self.istorage = istorage
        self.addService(istorage)

        istorage.connect_state_manager(iengine.updater)

    def assert_ready(self):
        if not self.istorage.available:
            raise AssertionError("{0} is not available", self.istorage)

    def get_changes(self):
        self.iengine.stream.next()
