#!/usr/bin/python

import logging
import sys

from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from time import time as tm

import tornadis
from redis import Redis, StrictRedis
from tormysql import ConnectionPool
from tornado.escape import json_decode, json_encode
from tornado.gen import coroutine, Return, Task
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.log import LogFormatter
from tornado.options import define, options, parse_command_line, parse_config_file
from tornado.web import Application

from loopchat.auxiliaries import is_text
from loopchat.db import CRUD
from loopchat.routes import routes
from loopchat.settings import settings


define('port', 8443, int)
define('secret')
if not options.log_file_prefix:
    options.log_file_prefix = '/var/log/loopchat.log'

define('db_host',   default='127.0.0.1')
define('db_user',   default='root')
define('db_passwd', default='')
define('db_db',     default='users')
define('db_schema', default=[])

define('username',   default='')
define('admin',      default='')
define('isban',      default='')
define('banunt',   default='')
define('bancom', default='')
define('avatar',     default='')

class Loopchat(Application):
    def __init__(self):
        super(Loopchat, self).__init__(routes, **settings)

    @coroutine
    def reset_user_count(self):
        #yield Task(redis_main.set, 'users', 0)
        yield self.subtask(self.redis_main.set, 'users', 0)


def main():
    app = Loopchat()
    http_server = HTTPServer(app)
    http_server.bind(8181)
    http_server.start(0) # Spread IOLoops over all the available CPU cores!
    ioloop = IOLoop.current()
    try:
        app.pubsub = tornadis.Client()
        app.pubsub.connect

        app.subtask = ThreadPoolExecutor(cpu_count()).submit
        # Connection with main redis instance on default port, 6379
        app.redis_main = Redis()
        # Connection with twemproxy which holds the whole Redis cluster
        app.redis_cluster = Redis()

        try:
            parse_config_file('/etc/loopchat.conf')
        except Exception as e:
            print "Please provide valid configuration in the /etc/loopchat.conf"
            print 'Check out REEDME.md for the details'
            sys.exit(1)

        # Prepare secondary log handler
        log_handler = logging.handlers.WatchedFileHandler(options.log_file_prefix)
        # Set tornado-style log formatting
        log_handler.setFormatter(LogFormatter(color=False))
        # Get main logger
        logger = logging.getLogger()
        # Remove all handlers (RotatingFileHandler in our case)
        logger.handlers = []
        # Set handler that we really need
        logger.addHandler(log_handler)
        # Prevent duplicate logging
        logger.propagate = False

        # Provide the Application with CRUD instance
        app.crud = CRUD(
            host   = options.db_host,
            passwd = options.db_passwd,
            user   = options.db_user,
            db     = options.db_db
        )

        # Check if username field is present since it is required
        if not options.username:
            logging.error(
                'Please provide "username" option in the /etc/loopchat.conf\n'
                'Check out REEDME.md for the details'
            )
            sus.exit(1)
        # Provide the Application with dict of the required fieldnames
        app.fields = {}
        for f in ['username', 'admin', 'isban', 'banunt', 'bancom', 'avatar']:
            value = options.get(f, '')
            if is_text(value):
                app.fields[f] = value
            else:
                app.fields[f] = ''
        # Set flag if we can ban users or not
        if (app.fields['admin'] and app.fields['isban'] and app.fields['banunt']
                                                      and app.fields['bancom']):
            app.moderation = True
        else:
            app.moderation = False

        ioloop.add_callback(app.reset_user_count)
        logging.info('starting')
        ioloop.start()
    except (SystemExit, KeyboardInterrupt):
        logging.info('shutting down')
        ioloop.add_callback(app.crud.db.close)
        ioloop.stop()
        sys.exit()
    except Exception as e:
        logging.error(e)
        ioloop.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
