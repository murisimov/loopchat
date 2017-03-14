from loopchat.handlers.pages import SigninHandler, MainHandler, AdminHandler, SignoutHandler
from loopchat.handlers.poll import PollingHandler

routes = [
    (r'/', MainHandler),
    (r'/loopchat-admin', AdminHandler),
    (r'/signin', SigninHandler),
    (r'/signout', SignoutHandler),
    (r'/common_channel/([\w\d]+)', PollingHandler),
    #(r'/common_channel', PollingHandler),
]
