import os

from app import create_app


if os.environ.get('APP_ENV') == 'production':
    if not os.environ.get('SECRET_KEY'):
        raise RuntimeError('SECRET_KEY must be set in production.')
    if not os.environ.get('INITIAL_ADMIN_PASSWORD'):
        raise RuntimeError('INITIAL_ADMIN_PASSWORD must be set in production.')

app = create_app()
