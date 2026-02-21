# until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
#   >&2 echo "Postgres is unavailable - sleeping"
#   sleep 1
# done

#python manage.py makemigrations tables --noinput #--merge
python manage.py makemigrations
python manage.py migrate
#python manage.py migrate tables

# Collect static files for production serving (admin CSS/JS, etc.)
python manage.py collectstatic --noinput

# start redis server
# redis-server ./conf/redis.conf --daemonize yes

# Start Django server (ASGI)
UVICORN_HOST=${UNICORN_HOST:-0.0.0.0}
UVICORN_PORT=${UNICORN_PORT:-8000}
UVICORN_WORKERS=${UNICORN_WORKERS:-4}

exec python -m uvicorn config.asgi:application \
  --host "$UVICORN_HOST" \
  --port "$UVICORN_PORT" \
  --workers "$UVICORN_WORKERS"
