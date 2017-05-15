#! /usr/bin/env python
from functools import wraps

from twisted.internet.threads import deferToThread

def threaded(fn):
    """A decorator which executes the wrapped function in twisted's default
    thread pool.
    """
    @wraps(fn)
    def defer_to_thread(*args, **kw):
        return deferToThread(fn, *args, **kw)
    return defer_to_thread
