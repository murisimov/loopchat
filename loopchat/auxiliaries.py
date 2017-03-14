import logging
from datetime import datetime as dt
from functools import wraps
from os import urandom

from tornado.log import LogFormatter


AUTH_COOKIE = urandom(24)
ADMIN_LOG = '/var/log/loopadmin.log'

log = logging.getLogger(__name__)
adminlog_handler = logging.handlers.WatchedFileHandler(ADMIN_LOG)
adminlog_handler.setFormatter(LogFormatter(color=False))
log.addHandler(adminlog_handler)
log.propagate = False

def authenticated(func):
    @wraps(func)
    def wrapper(handler, *args, **kwargs):
        if handler.get_secure_cookie(AUTH_COOKIE):
            return func(handler, *args, **kwargs)
        return handler.redirect('/signin')
    return wrapper

def benchmark(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = dt.now()
        result = func(*args, **kwargs)
        diff = (dt.now() - start).total_seconds()
        logging.info("%s: %s" % (func.__name__, diff))
        return result
    return wrapper

def list_eval(L):
    return [ literal_eval(e) for e in L ]

def is_text(value):
    return isinstance(value, str) or isinstance(value, unicode)

class TimeTrack:
    def __init__(self):
        #self.template = "%d-%m-%Y %H:%M:%S"
        self.template = "%Y-%m-%d %H:%M:%S"

    def now_str(self):
        """
        Value to put to DB and used by now_dt method
        """
        return dt.strftime(dt.now(), self.template)

    def now_dt(self):
        """
        Value to compare with old value from DB
        """
        return dt.strptime(self.now_str(), self.template)

    def to_dt(self, time):
        """
        Get value from DB to compare
        """
        return dt.strptime(time, self.template)

    def to_str(self, time):
        """
        Convert dt object to str
        """
        return dt.strftime(time, self.template)

    def elapsed(self, time):
        """
        Compare old and now values
        """
        return (self.now_dt() - self.to_dt(time)) < timedelta(minutes=0)

    def time_left(self, time):
        return self.to_dt(time) - self.now_dt()

    def td_str(self, td):
        return str(td).split('.')[0]


t = TimeTrack()
