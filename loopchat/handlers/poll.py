import logging
from ast import literal_eval
from datetime import datetime as dt, timedelta

from tornadis import PubSubClient, TornadisException
from tornado.escape import json_decode, json_encode
from tornado.gen import coroutine, Return
from tornado.websocket import WebSocketHandler

from loopchat.auxiliaries import benchmark, log, t


class PollingHandler(WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(PollingHandler, self).__init__(*args, **kwargs)
        self.channels = [
            'common', 'delete', 'edit', 'info', 'system', 'ban'
        ]
        self.listen()

    def check_origin(self, origin):
        return True

    @property
    def pubsub(self):
        return self.application.pubsub

    @property
    def db(self):
        return self.application.db

    @property
    def subtask(self):
        return self.application.subtask

    @property
    def redis_main(self):
        return self.application.redis_main

    @property
    def redis_cluster(self):
        return self.application.redis_cluster

    @property
    def crud(self):
        return self.application.crud

    @coroutine
    def listen(self):
        """
        This method runs on PollingHandler instance initiation
        (when a user connects via websocket).
        It connects to main redis instance with tornadis client
        (since twemproxy doesn't support pub/sub commands),
        subscribes on necessary channels, listens them and handles
        messages when any pops out.
        """
        self.client = PubSubClient(autoconnect=False)
        yield self.client.connect()
        yield self.client.pubsub_subscribe(*self.channels)
        while True:
            msg = yield self.client.pubsub_pop_message()
            if isinstance(msg, TornadisException):
                logging.error(str(msg))
                break
            elif self.ws_connection is None:
                yield self.client.pubsub_unsubscribe(*self.channels)
                logging.warning("tornadis_listen: ws connection is gone, unsubscribing")
                break
            else:
                #logging.info(msg)
                kind, channel, body = msg
                if kind == 'message':
                    """
                    Sends a message to a user if any shows up.
                    """
                    message = literal_eval(body)
                    if channel == 'ban' and message['user'] == self.username:
                        yield self.ban(message)
                    else:
                        self.safe_write([channel, message])
                elif kind == 'disconnect':
                    logging.warning("Disconnected from Redis server.")
                    break
        self.client.disconnect()

    @coroutine
    def ban(self, details):
        self.isban = True
        self.ban_expires = t.to_dt(details['until']) - dt.now()
        if int(details['time']) > 48:
            info = "You've been banned forever. Reason:\n%s"
            info = {'msg': info % details['reason']}
        else:
            info = "You've been banned for %s hours. Reason:\n%s"
            info = {'msg': info % (details['time'], details['reason'])}
        self.safe_write(['info', info])

    @coroutine
    def safe_write(self, message):
        if self.ws_connection is None:
            logging.error('Connection is already closed.')
            yield self.client.pubsub_unsubscribe('users', *self.channels)
            logging.warning("safe_write: ws connection is gone, unsubscribing")
            #self.close()
        else:
            self.write_message(json_encode(message))
            #IOLoop.current().add_callback(partial(self.write_message,
            #                                   json_encode(message)))

    @coroutine
    def open(self, *args):
        try:
            #yield Task(self.redis_main.incr, 'users')
            yield self.subtask(self.redis_main.incr, 'users')
        except Exception as error:
            log.error(str(error))
        log.info("Connection established with %s.", self.request.remote_ip)
        #logging.info("Full url: %s\n" % str(self.request.full_url()))
        #logging.info("Headers: %s\n" % str(dict(self.request.headers.get_all())))
        #logging.info("Path: %s\n" % str(self.request.path))
        #logging.info("Uri: %s\n" % str(self.request.uri))
        #logging.info("Protocol: %s\n" % str(self.request.protocol))
        #logging.info("Request time: %s\n" % str(self.request.request_time()))
        #logging.info("Version: %s\n" % str(self.request.version))
        self.username = self.request.uri.split('/')[-1]
        user = yield self.crud.get_user(self.username)
        if not user:
            logging.error("User %s does not exist." % self.username)
            self.close()
        else:
            self.nickname, self.avatar = user['name'], user['avatar']

            # Ban checks
            self.isban = True if int(user['isban']) else False
            self.ban_expires = user['banuntil'] - dt.now() if self.isban else None
            if self.isban:
                log.info(user['bancomment'].decode('string_escape'))

            # Admin checks
            self.admin = True if user['groupid'] == 1 else False
            if self.admin: yield self.client.pubsub_subscribe('users')

            # Send last messages
            idle = True
            while idle:
                try:
                    #msg_id = yield Task(self.redis_main.get, 'msg_id')
                    msg_id = yield self.subtask(self.redis_main.get, 'msg_id')
                    msg_id = int(msg_id)
                except Exception as error:
                    logging.error('msg id get error')
                    logging.error(str(error))
                else:
                    idle = False
            query = [ 'msg:'+ str(i) for i in range(msg_id - 9, msg_id + 1) ]
            idle = True
            while idle:
                try:
                    #last_ten = yield Task(self.redis_cluster.mget, query)
                    last_ten = yield self.subtask(self.redis_cluster.mget, query)
                except Exception as error:
                    logging.error(str(error))
                    logging.error('last messages error')
                else:
                    idle = False
            if last_ten:
                try:
                    last_ten = [ literal_eval(e) for e in last_ten ]
                except Exception:
                    log.warning("No messages to load for " + self.username)
                else:
                    last_ten.reverse()
                    self.safe_write(['open', last_ten])
            else:
                log.warning("No messages to load for " + self.username)

    @coroutine
    def on_message(self, message):
        #users = yield Task(self.redis_main.get, 'users')
        #log.warning(users)
        channel, data = json_decode(message)
        log.info(data)
        forbidden = self.username + ' is trying to act as admin!'
        if self.isban:
            # Free from ban if bantime is up
            if self.ban_expires <= timedelta(minutes=0):
                yield self.crud.switch_ban_user(self.username, 0)
                self.isban = False
            else:
                info = "Your ban expires in %s." % t.td_str(self.ban_expires)
                self.safe_write(['system', {'msg': info}])
                raise Return()

        if channel == 'common':
            #msg_id = yield Task(self.redis_main.incr, 'msg_id')
            msg_id = yield self.subtask(self.redis_main.incr, 'msg_id')
            msg_id = str(msg_id)
            key = 'msg:%s' % msg_id
            value = {
                'id': msg_id,
                'user': self.username,
                'nick': self.nickname,
                'avatar': self.avatar,
                'message': data,
                'type': 'msg-admin' if self.admin else 'msg-user',
                'datetime': dt.strftime(dt.now(), "%H:%M:%S %d-%m-%Y"),
            }
            # PUBLISH message to the common channel
            yield self.pubsub.call("PUBLISH", channel, str(value))
            cluster_pipe = self.redis_cluster.pipeline()
            # SET and EXPIRE message
            # NOTE: switched value and time for pyredis
            cluster_pipe.setex(key, str(value), 6000)
            # RPUSH it to user associated history array
            cluster_pipe.rpush('hist:' + self.username, value)
            #yield Task(cluster_pipe.execute)
            yield self.subtask(cluster_pipe.execute)

        elif channel == 'delete':
            if self.admin:
                try:
                    #yield Task(self.redis_cluster.delete, 'msg:'+ data)
                    yield self.subtask(self.redis_cluster.delete, 'msg:'+ data)
                except Exception as error:
                    logging.error('delete error')
                    logging.error(str(error))
                yield self.pubsub.call("PUBLISH", channel, str({'id': data}))
            else:
                log.warning(forbidden)

        elif channel == 'edit':
            if not self.admin:
                log.warning(forbidden)
                raise Return()
            msg_id, msg = data
            #to_edit = yield Task(self.redis_cluster.get, 'msg:'+ msg_id)
            to_edit = yield self.subtask(self.redis_cluster.get, 'msg:'+ msg_id)
            if not to_edit:
                log.warning("Message %s does not exist." % msg_id)
                raise Return()
            try:
                to_edit = literal_eval(to_edit)
            except Exception:
                logging.error("Edit failed, try again")
            else:
                to_edit['message'] = msg
                #yield Task(self.redis_cluster.setex, 600, 'msg:'+ msg_id,str(edited))
                # NOTE: switched value and time for pyredis
                yield self.subtask(self.redis_cluster.setex, 'msg:'+ msg_id,
                                                        str(to_edit), 600)
                yield self.pubsub.call("PUBLISH", channel, str({'id':msg_id,
                                                           'message': msg}))

        elif channel == 'info' or channel == 'system':
            if not self.admin:
                log.warning(forbidden)
                raise Return()
            value = {
                'msg': data,
                'datetime': dt.strftime(dt.now(), "%H:%M:%S %d-%m-%Y"),
            }
            yield self.pubsub.call("PUBLISH", channel, str(value))

        elif channel == 'ban':
            if not self.admin:
                log.warning(forbidden)
                raise Return()
            name, ban_time, ban_reason = data
            if ban_time.isdigit():
                ban_time = int(ban_time)
            else:
                ban_time = 99999

            logging.warning(name)
            row = yield self.crud.get_user(name)
            # Return if user has been already banned
            if int(row['isban']):
                log.warning('User %s is already banned until %s for:\n"%s"' %
                           (row['user'], row['banuntil'], row['bancomment']))
                raise Return()

            ban_until = t.to_str(t.now_dt() + timedelta(hours=ban_time))
            yield self.crud.switch_ban_user(name, 1, until=ban_until,
                                          comment=escape(ban_reason))
            log.info('ban done')

            # Modify user's websocket object
            yield self.pubsub.call("PUBLISH", channel, str({'user': row['user'],
                                                             'until': ban_until,
                                                               'time': ban_time,
                                                         'reason': ban_reason}))

        elif channel == 'load':
            log.info('load more!')

            msg_id = int(data)
            query = [ 'msg:' + str(i) for i in range(msg_id - 10, msg_id) ]
            #last_ten = yield Task(self.redis_cluster.mget, query)
            last_ten = yield self.subtask(self.redis_cluster.mget, query)
            last_ten.reverse()
            try:
                last_ten = [ literal_eval(msg) for msg in last_ten ]
            except ValueError:
                log.warning('No more messages left for ' + self.username)
            else:
                self.safe_write(['load', last_ten])

        else:
            log.info('No case involved!')

    @coroutine
    def on_close(self):
        log.info("Connection closed, %s.", self.request.remote_ip)
        try:
            #yield Task(self.redis_main.decr, 'users')
            yield self.subtask(self.redis_main.decr, 'users')
        except Exception as error:
            log.error(str(error))
        yield self.client.pubsub_unsubscribe('users', *self.channels)
        self.client.disconnect()
