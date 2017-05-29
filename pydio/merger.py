#! /user/bin/env python
from zope.interface import implementer
from zope.interface.verify import verifyObject

from twisted.logger import Logger
from twisted.internet import defer
from twisted.application.service import MultiService

from . import IMerger, IMergeStrategy
from .synchronizable import ISynchronizable


@implementer(IMerger)
class TwoWayMerger(MultiService):
    """Synchronize two ISynchronizables using an SQLite table"""

    log = Logger()

    def __init__(self, local, remote, direction=None):
        super().__init__()

        verifyObject(ISynchronizable, local)
        self.local = local
        self.addService(local)

        verifyObject(ISynchronizable, remote)
        self.remote = remote
        self.addService(remote)

        self.direction = direction

    def _fetch_changes(self):
        """Get local and remote changes"""
        # equivalent to _compute_changes
        return defer.gatherResults([
            self.local.get_changes(),
            self.remote.get_changes(),
        ])

    @defer.inlineCallbacks
    def sync(self):
        d = dict(up=":==>", down="<==:").get(self.direction, "<==>")
        self.log.info("Merging {m.local} {dir} {m.remote}", m=self, dir=d)

        yield self.assert_volumes_ready()
        yield self._fetch_changes()

        # NOTE : Consider creating an interface, IMergeStrategy, that
        #        abstracts away the details of the merge algoritm.

        # merge()  # TODO

    def assert_volumes_ready(self):  # exported because it's a pure function
        """Verify that local and remote sync targets are present, accessible and
        in consistent states (i.e.:  ready to merge).
        """
        return defer.gatherResults(map(defer.maybeDeferred, [
            self.local.assert_ready,
            self.remote.assert_ready,
        ])).addErrback(lambda f: f.value.subFailure.raiseException())
