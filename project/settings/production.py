from .base import *
import dj_database_url
import django_heroku


django_heroku.settings(locals())

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'dj_database_url',
        'USER': '',
        'PASSWORD': '',
        'PORT': '',
    }
}

DB_FROM_ENV = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(DB_FROM_ENV)