#! /usr/bin/env python
"""Wrapper around twisted.enterprise.adbapi for use with sqlite3"""

from twisted.enterprise.adbapi import ConnectionPool


class ConnectionManager(ConnectionPool):
    """A subclass of t.e.adbapi.ConnectionPool that uses pydio.util.sqlite3 and
    enforces correct concurrency constraints.
    """

    def __init__(self, path):
        super().__init__(
            "sqlite3",
            path,
            check_same_thread=False,
            cp_max=1,
            cp_min=1,
        )

__all__ = ["ConnectionManager"]
