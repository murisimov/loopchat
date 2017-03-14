import logging

from tormysql import ConnectionPool
from tornado.gen import coroutine, Return


class CRUD(object):
    def __init__(self, app, db, schema, table, colnames, host="127.0.0.1",
                                                 user="root", passwd="",):
        self.db = ConnectionPool(
            max_connections = 1000,       # Max open connections
            idle_seconds = 7200,          # Conntion idle timeout time, 0 is not timeout
            wait_connection_timeout = 3,  # Wait connection timeout
            host    = host,
            user    = user,
            passwd  = passwd,
            db      = db,
            charset = "utf8"
        )
        self.app      = app
        self.schema   = schema
        self.table    = table
        self.colnames = colnames

    @coroutine
    def get_user(self, name):
        with (yield self.db.Connection()) as conn:
            with conn.cursor() as cursor:
                yield cursor.execute(
                    "SELECT * FROM %s WHERE %s = '%s'" % (
                         self.table, self.colnames['username'], name
                    )
                )
                user = cursor.fetchone()
        if user:
            response = dict(zip(self.schema, user))
            raise Return(response)
        raise Return(None)

    @coroutine
    def switch_ban_user(self, name, ban, until='', comment=''):
        if not self.app.moderation:
            raise Return()
        temp = "UPDATE %s SET %s=%s, %s='%s', %s='%s' WHERE %s='%s'"
        query = temp % (
            self.table
            self.app.fields['isban'],    ban,
            self.app.fields['banunt'],   until,
            self.app.fields['bancom'],   comment,
            self.app.fields['username'], name
        )
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
