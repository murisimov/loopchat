LOOPCHAT
---
**Welcome here traveller!**

---
This is plug-in chat app that you can use with _almost_ any other Mysql-based app.

---
To be compatible, your app's users table should
have an unique username field, and that's all.

---

---
To set up loopchat, you will have to fill few variables in the `loopchat.conf`
and then place it to `/etc/loopchat.conf`. The required variables are:
- `db_db`: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`str`, name of your database
- `db_table`: &nbsp;&nbsp;&nbsp;`str`, name of your users table
- `db_schema`: `list`, where you list your users table field names
- `username`&nbsp;&nbsp;:&nbsp;&nbsp;`str`, &nbsp;&nbsp; name of your username-type unique field

---
Though, if you want to use ban features and a bit of
customization, you'll have to provide the following variables:
- `admin` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_Is user allowed to access admin interface? (bool or 1/0 integer)_
- `isbann` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_Is user banned? (bool or 1/0 integer)_
- `banuntil` &nbsp;&nbsp;&nbsp;_When does ban expire? (datetime)_
- `bancomment` _Ban comment (string)_
- `avatar` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_User avatar (string, URL)_

---

---
**Here is an example of the configuration:**
```python

"""
DATABASE CONNECTION
"""
# These are actually default values, you do not have to specify
# them unless you want to change database connection settings.
##########################
#db_host   = '127.0.0.1' #
#db_user   = 'root'      #
##########################
#db_passwd = ''          #

db_user   = 'pirojok'
db_passwd = 'smetanka28'

db_db     = 'penchekryaki'
db_table  = 'users'


"""
USERS TABLE SCHEMA
"""
# How your users table's column names may look like
db_schema = [
    'id', 'group', 'username', 'pwdhash' 'avatar', 'nickname',
    'regdate', 'is_banned', 'ban_until', 'ban_info', 'image', 'admin'
]
# NOTE that you should specify ALL field names and in the valid order!

"""
REQUIRED FIELDS
"""
username = 'username' # Only this one is necessary for chat to work
# ---
# Fields below are required for ban features
admin    = 'admin'
isban    = 'is_banned'
banunt   = 'ban_until'
bancom   = 'ban_info'
# ---
name     = 'nickname'
avatar   = 'image'

```


---
dependencies
---
CentOS:
- gcc
- python-devel
- tcl (for redis tests)
- [redis](https://redis.io/)

Debian:
- build-essential
- python-dev
- [redis-server](https://redis.io/)

---
