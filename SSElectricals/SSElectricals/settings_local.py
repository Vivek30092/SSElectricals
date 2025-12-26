# Local development settings - Overrides settings.py for local development
# Usage: python manage.py runserver --settings=SSElectricals.settings_local

from .settings import *

# Override database to use SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Debug mode for local development
DEBUG = True

# Simpler email backend for testing (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

print("🔧 Using LOCAL DEVELOPMENT settings (SQLite database)")
