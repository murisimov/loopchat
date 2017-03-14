import logging

from tormysql import ConnectionPool
from tornado.gen import coroutine, Return


class CRUD(object):
    def __init__(self, schema, host="127.0.0.1", user="root", passwd="", db="users"):
        self.db = ConnectionPool(
            max_connections = 1000,       # max open connections
            idle_seconds = 7200,          # conntion idle timeout time, 0 is not timeout
            wait_connection_timeout = 3,  # wait connection timeout
            host    = "127.0.0.1",
            user    = "root",
            passwd  = "",
            db      = "users",
            charset = "utf8"
        )
        self.schema = schema

    @coroutine
    def get_user(self, name):
        with (yield self.db.Connection()) as conn:
            with conn.cursor() as cursor:
                yield cursor.execute("SELECT * FROM users WHERE user = '%s'" % name)
                user = cursor.fetchone()
        if user:
            response = dict(zip(self.schema, user))
            raise Return(response)
        raise Return(None)

    @coroutine
    def switch_ban_user(self, name, ban, until='', comment=''):
        temp = "UPDATE users SET isban=%s, banuntil='%s', bancomment='%s' WHERE user='%s'"
        query = temp % (ban, until, comment, name)
        with (yield self.db.Connection()) as conn:
            try:
                with conn.cursor() as cursor:
                    yield cursor.execute(query)
            except Exception as e:
                logging.error("Something went wrong on mysql operation!")
                logging.error(str(e))
                yield conn.rollback()
            else:
                yield conn.commit()
