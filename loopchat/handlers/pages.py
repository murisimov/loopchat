import logging
from hashlib import md5

from tornado.escape import utf8
from tornado.gen import coroutine, Return

from loopchat.auxiliaries import AUTH_COOKIE, authenticated, benchmark, log, t
from loopchat.handlers.base import BaseHandler


class SigninHandler(BaseHandler):
    @coroutine
    def get(self, *args, **kwargs):
        self.render('signin.html', error=None)

    @coroutine
    def post(self):
        # Do checks for inappropriate symbols:
        for key, argument in self.request.arguments.items():
            if argument == ['']:
                error = "Argument '%s' is missing." % key
                self.render('signin.html', error=error)
                break
            if "'" in argument[0] or '"' in argument[0]:
                error = "Sorry but quotes is not allowed!"
                self.render('signin.html', error=error)
                break
            if not key == '_xsrf' and len(argument[0]) > 16:
                error = "Argument '%s' is too long" % key
                self.render('signin.html', error=error)
                break
            try:
                argument[0].decode('ascii')
            except UnicodeDecodeError, UnicodeEncodeError:
                error = "Did you write something in cyrillic?"
                self.render('signin.html', error=error)
                break

        else:
            username = self.get_argument("name")
            password = self.get_argument("password")

            #query = "SELECT pass FROM users WHERE user='%s'" % username
            #yield self.subtask(amysql_db.query, query)

            user = yield self.crud.get_user(username)
            if user:
                hashed_password = yield self.subtask(md5, utf8(password))
                hashed_password = hashed_password.hexdigest()
                if hashed_password == user['pass']:
                    self.set_secure_cookie(AUTH_COOKIE, username)
                    self.redirect('/admin')
                else:
                    error = 'Incorrect password'
                    self.render('signin.html', error=error)
            else:
                error = "User haven't found"
                self.render('signin.html', error=error)


class MainHandler(BaseHandler):
    @coroutine
    def get(self):
        self.render('chat.html')


class AdminHandler(BaseHandler):
    #@benchmark
    @authenticated
    @coroutine
    def get(self, **kwargs):
        username = self.get_secure_cookie(AUTH_COOKIE)
        logging.warning(username)
        user = yield self.crud.get_user(username)
        logging.warning(user)
        kwargs = {
            'user': user
        }
        self.render('admin.html', **kwargs)


class SignoutHandler(BaseHandler):

    @coroutine
    def get(self, *args, **kwargs):
        self.clear_cookie(AUTH_COOKIE)
        self.redirect('/admin')
