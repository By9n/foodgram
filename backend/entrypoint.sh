python manage.py collectstatic --noinput
cp -r /app/static/. /backend_static/
cp -r /app/media/. /backend_media/
python manage.py migrate
gunicorn foodgram.wsgi:application --bind 0:9090