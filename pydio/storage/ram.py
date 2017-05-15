#! /usr/bin/env python
from zope.interface import implementer
from zope.interface.verify import verifyObject

from pydio.storage import IStorage

from twisted.application.service import Service

from pydio.util.sqlite import SQLiteService
from pydio.engine import IStateManager


# TODO : implement SQL-FS here.
#        SQL-FS should probably use triggers to populate a `changes` table,
#        whose lines can then be read and fed into the IStateManager.


@implementer(IStorage)
class Volatile(Service):

    def __init__(self):
        super().__init__()

    def connect(self, istateman):
        verifyObject(IStateManager, istateman)
        raise NotImplementedError(
            "p.s.r.Volatile must do something with IStateManager"
        )
