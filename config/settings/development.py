"""
Django settings for config project - DEVELOPMENT SETTINGS.

These settings are intended for development environment.
"""
from .base import *
from dotenv import load_dotenv
load_dotenv()
from datetime import timedelta
SECRET_KEY = 'django-insecure-k#7)jd3^lr@fd9fz*#7*j31@b!zw@wwxdo1h49__z$jk_a+_2n'

DEBUG = True

ALLOWED_HOSTS = ['*']


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# You can also use PostgreSQL for development:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('DB_NAME', 'django_dev'),
#         'USER': os.getenv('DB_USER', 'postgres'),
#         'PASSWORD': os.getenv('DB_PASS', 'postgres'),
#         'HOST': os.getenv('DB_HOST', 'localhost'),
#         'PORT': os.getenv('DB_PORT', '5432'),
#     }
# }

# Debug logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',  
        },
    },
}

# Additional development apps
INSTALLED_APPS += [
    'django_extensions',  # Uncomment if installed
    # 'debug_toolbar',    # Uncomment if installed
]

# Debug Toolbar settings (if installed)
# if 'debug_toolbar' in INSTALLED_APPS:
#     MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
#     INTERNAL_IPS = ['127.0.0.1']

# Email settings for development (console backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # For React frontend in development
    "http://127.0.0.1:3000",
]

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),   
    'ROTATE_REFRESH_TOKENS': False,                 
    'BLACKLIST_AFTER_ROTATION': True,              
    'UPDATE_LAST_LOGIN': True,                     

    'ALGORITHM': 'HS256',                          
    'SIGNING_KEY': SECRET_KEY,                      
    'VERIFYING_KEY': None,                          
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),             \
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',     
    'USER_ID_FIELD': 'id',                        
    'USER_ID_CLAIM': 'user_id',                   

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}