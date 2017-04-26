#! /user/bin/env python

from zope.interface.verify import verifyObject
from zope.interface import Interface, implementer


class ISynchronizable(Interface):
    """Represents one side of a synchronization equation"""

    def getChanges(idx):
        """Get changes with a higher index than `idx`"""


@implementer(ISynchronizable)
class PydioServerWorkspace:
    """An ISynchronizable interface to a remote Pydio workspace"""

    # PydioSdk(
    #         job_config["server"],
    #         ws_id=self.ws_id,
    #         remote_folder=job_config["remote_folder"],
    #         user_id=job_config["user_id"],
    #         device_id=ConfigManager().device_id,
    #         skip_ssl_verify=job_config["trust_ssl"],
    #         proxies=ConfigManager().defined_proxies,
    #         timeout=job_config["timeout"]
    #     )

    # def __init__(self):
    #     pass

    def getChanges(idx):
        raise NotImplementedError


@implementer(ISynchronizable)
class LocalWorkspace:
    """An ISynchronizable interface to a local Pydio workspace directory"""

    def __init__(self, dir):
        self._dir = dir

    @property
    def dir(self):
        """Local directory being watched"""
        return self._dir

    def getChanges(idx):
        raise NotImplementedError


class IMerger(Interface):
    """A class that can perform a merge of two or more ISynchronizables"""

    def sync():
        """Synchronize"""


@implementer(IMerger)
class SQLiteMerger:
    """Synchronize two ISynchronizables using an SQLite table"""

    def __init__(self, local, remote):
        emsg = "{0} does not implement ISynchronizable"

        if not verifyObject(ISynchronizable, local):
            raise TypeError(emsg.format(type(local)))
        self.local = local

        if not verifyObject(ISynchronizable, remote):
            raise TypeError(emsg.format(type(remote)))
        self.local = local

    #@inlineCallbacks
    def sync(self):
        raise  NotImplementedError
