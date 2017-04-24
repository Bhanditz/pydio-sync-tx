#! /usr/bin/env python
from collections import namedtuple

from twisted.application.service import Service

DEFAULT_WHITELIST = ("*",)
DEFAULT_BLACKLIST = (
    ".*",
    "*/.*",
    "/recycle_bin*",
    "*.pydio_dl",
    "*.DS_Store",
    ".~lock.*",
    "~*",
    "*.xlk",
    "*.tmp"
)


class Job(Service):
    def __init__(self, name, cfg):
        self.name = name  # enforce named services

        self.schedule = cfg.pop("frequency", "auto")
        self.direction = cfg.pop("direction", "bi")
        self.solve = cfg.pop("solve", "both")

        self.workspace = cfg.pop("workspace")
        self.localdir = cfg.pop("directory")
        self.server = cfg.pop("server")

        self.excludes = cfg.pop("includes", DEFAULT_WHITELIST)
        self.excludes = cfg.pop("excludes", DEFAULT_BLACKLIST)

        self.trust_ssl = cfg.pop("trust_ssl", False)

        self.timeout = cfg.pop("timeout", 20)
        self._running = cfg.pop("active", True)

        # create watchdog
        # create contdiffmerger

    def startService(self):
        super(Job, self).startService()
        raise NotImplementedError

    def stopService(self):
        super(Job, self).stopService()
        raise NotImplementedError
