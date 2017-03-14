from os import urandom
from os.path import dirname, join
from pkg_resources import Requirement, resource_filename, resource_string


settings = {
    'static_path': resource_filename('loopchat', 'static'),
    'template_path': resource_filename('loopchat', 'templates'),
    'cookie_secret': urandom(24),
}
