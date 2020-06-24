release: python manage.py migrate --run-syncdb --settings=project.settings.production
web: gunicorn project.wsgi --log-file -