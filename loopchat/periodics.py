#!/usr/bin/python

"""
This file stands for collecting application/system stats
"""

import logging
from sys import exit

import tornadis

from tornado.escape import json_encode
from tornado.gen import coroutine, Task
from tornado.ioloop import IOLoop, PeriodicCallback

from loopchat.monitoring import GetStats


redis_main = tornadis.Client()
redis_main.connect()

@coroutine
def users():
    user_count = yield redis_main.call("GET", 'users')
    yield redis_main.call("PUBLISH", 'users', user_count)

@coroutine
def stats():
    stats = yield GetStats().stats()
    yield redis_main.call("PUBLISH", "stats", json_encode(stats))
    #logging.warning(stats)

def main():
    # Collect and sent data every second
    PeriodicCallback(users, 1000).start()
    PeriodicCallback(stats, 1000).start()
    try:
        IOLoop.current().start()
    except (SystemExit, KeyboardInterrupt):
        IOLoop.current().stop()
        exit(0)
    except Exception as e:
        logging.error(e)
        IOLoop.current().stop()
        exit(1)

if __name__ == '__main__':
    main()
