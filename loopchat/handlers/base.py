from tornado.web import RequestHandler

class BaseHandler(RequestHandler):
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
