#! /usr/bin/env python

from zope.interface import implementer

from twisted.logger import Logger
from twisted.internet import defer
from twisted.application.service import Service

from pydio import ISynchronizable

@implementer(ISynchronizable)
class PydioServer(Service):
    """An ISynchronizable interface to a remote Pydio workspace"""

    log = Logger()

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

    # def __str__(self):
    #     return "`{0}`".format(self.addr)

    @classmethod
    def from_config(cls, cfg):
        return cls()  # TODO : consume config

    @defer.inlineCallbacks
    def get_changes(self):
        raise NotImplementedError

    def assert_ready(self):
        #
        # NOTE:  YOU ARE HERE
        # TODO:  implement based on remote SDK
        #
        raise  NotImplementedError
