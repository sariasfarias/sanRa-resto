from .base import *
import dj_database_url


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'dj_database_url',
        'USER': '',
        'PASSWORD': '',
        'PORT': '',
    }
}

DB_FROM_ENV = dj_database_url.config()
DATABASES['default'].update(DB_FROM_ENV)
