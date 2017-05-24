"""
Django settings for offenesparlament project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/

Managed using django-configurations
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import logging
from sys import path
from configurations import Configuration

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
logging.basicConfig(
    level=logging.INFO,
)


class BaseConfig(Configuration):
    STATICFILES_DIRS = (os.path.join(PROJECT_PATH, 'static'), )
    DEBUG_SUBSCRIPTIONS = True

    SECRET_KEY = 'tk5l_92mqo3406we8^s*x%%=*7*m*!ce0^o^s7_t9lrg@f46_n'
    DEBUG = False
    TEMPLATE_DEBUG = False
    ALLOWED_HOSTS = []

    INSTALLED_APPS = (
        'grappelli.dashboard',
        'grappelli',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'haystack',
        'op_scraper',
        'annoying',
        'django_extensions',
        'django_bootstrap_breadcrumbs',
        'import_export',
        'jsonify',
        'djcelery',
        'django_inlinecss',
    )

    MIDDLEWARE_CLASSES = (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    )

    # Grappelli Configuration

    GRAPPELLI_INDEX_DASHBOARD = 'op_scraper.op_scraper_dashboard.CustomIndexDashboard'

    # Haystack Configuration
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'offenesparlament.search_backend.FuzzyElasticsearchSearchEngine',
            'URL': 'http://localhost:9200/',
            'INDEX_NAME': 'haystack',
            'TIMEOUT': 120,
            'BATCH_SIZE': 50,
            'EXCLUDED_INDEXES': [
                'op_scraper.search_indexes.PersonIndexArchive',
                'op_scraper.search_indexes.LawIndexArchive',
                'op_scraper.search_indexes.DebateIndexArchive'
            ]
        },
        'archive': {
            'ENGINE': 'offenesparlament.search_backend.FuzzyElasticsearchSearchEngine',
            'URL': 'http://localhost:9200/',
            'INDEX_NAME': 'archive',
            'TIMEOUT': 120,
            'BATCH_SIZE': 50,
            'EXCLUDED_INDEXES': [
                'op_scraper.search_indexes.PersonIndex',
                'op_scraper.search_indexes.LawIndex',
                'op_scraper.search_indexes.DebateIndex'
            ]
        },
    }

    ROOT_URLCONF = 'offenesparlament.urls'

    WSGI_APPLICATION = 'offenesparlament.wsgi.application'

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(PROJECT_PATH, 'templates')],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': (
                    'django.contrib.auth.context_processors.auth',
                    'django.core.context_processors.debug',
                    'django.core.context_processors.i18n',
                    'django.core.context_processors.media',
                    'django.core.context_processors.static',
                    'django.core.context_processors.tz',
                    'django.contrib.messages.context_processors.messages',
                    'django.core.context_processors.request'
                )
            },
        },
    ]

    # Database
    # https://docs.djangoproject.com/en/1.7/ref/settings/#databases

    # DATABASES = {
    #     'default': {
    #         'ENGINE': 'django.db.backends.sqlite3',
    #         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    #     }
    # }

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'op',
            'USER': 'op',
            'PASSWORD': 'secret',
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }

    # Internationalization
    # https://docs.djangoproject.com/en/1.7/topics/i18n/

    LANGUAGE_CODE = 'en-us'

    TIME_ZONE = 'UTC'

    USE_I18N = True

    USE_L10N = False

    USE_TZ = True

    DATE_FORMAT = "j.n.Y"

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/1.7/howto/static-files/

    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(PROJECT_PATH)

    # Django Celery
    CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
    CELERY_REDIRECT_STDOUTS_LEVEL = 'INFO'
    CELERYD_HIJACK_ROOT_LOGGER = False

    # CELERYBEAT_SCHEDULE = {
    #     'update_elastic_index': {
    #         'task': 'tasks.update_elastic',
    #         'schedule': crontab(minute='0', hour='6')
    #     },
    # }

    # CELERY_TIMEZONE = 'UTC'


class Dev(BaseConfig):
    DEBUG = True
    TEMPLATE_DEBUG = True
    BROKER_URL = 'amqp://offenesparlament:op_dev_qwerty@offenesparlament.vm:5672//'
    #CELERY_RESULT_BACKEND = 'amqp'

    ALLOWED_HOSTS = ['offenesparlament.vm','testserver']

    # EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = '/vagrant/ignore/log/mails' # change this to a proper location


    # Workaround for the ReactorNotRestartable issue described here:
    # http://stackoverflow.com/questions/22116493/run-a-scrapy-spider-in-a-celery-task
    CELERYD_MAX_TASKS_PER_CHILD = 1

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
            'null': {
                'level': 'INFO',
                'class': 'django.utils.log.NullHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            },
            'op_scraper.subscriptions.diff': {
                'handlers': ['console'],
                'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            },
            'django.db.backends': {
                'handlers': ['null'],  # Quiet by default!
                'propagate': False,
                'level': 'INFO',
            },
        },
    }

    INSTALLED_APPS = BaseConfig.INSTALLED_APPS + (
        'debug_toolbar',
        'template_timings_panel'
    )

    # configure debug toolbar explicitly
    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    MIDDLEWARE_CLASSES = BaseConfig.MIDDLEWARE_CLASSES + \
        ('debug_toolbar.middleware.DebugToolbarMiddleware', )

    INTERNAL_IPS = ('127.0.0.1', '10.0.2.2', '192.168.47.1')

    DEBUG_TOOLBAR_PANELS = [
        # 'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        # 'debug_toolbar.panels.settings.SettingsPanel',
        # 'debug_toolbar.panels.headers.HeadersPanel',
        # 'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        # 'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        # 'debug_toolbar.panels.signals.SignalsPanel',
        # 'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'template_timings_panel.panels.TemplateTimings.TemplateTimings',
    ]

class UnitTest(Dev):
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    STATIC_ROOT = os.path.join(PROJECT_PATH, 'static')

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
            'null': {
                'level': 'INFO',
                'class': 'django.utils.log.NullHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            },
            'django.db.backends': {
                'handlers': ['null'],  # Quiet by default!
                'propagate': False,
                'level': 'INFO',
            },
            'elasticsearch': {
                'handlers': ['null'],  # Quiet by default!
                'propagate': False,
                'level': 'INFO',
            },
            'elasticsearch.trace': {
                'handlers': ['null'],  # Quiet by default!
                'propagate': False,
                'level': 'INFO',
            },
            'offenesparlament': {
                'handlers': ['null'],  # Quiet by default!
                'propagate': False,
                'level': 'INFO',
            },
            'op_scraper.subscriptions.diff': {
                'handlers': ['null'],
                'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            },
            
        },
    }

    # Haystack Configuration
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'offenesparlament.search_backend.FuzzyElasticsearchSearchEngine',
            'URL': 'http://localhost:9200/',
            'INDEX_NAME': 'haystacktest',
            'TIMEOUT': 120,
            'BATCH_SIZE': 50,
            'EXCLUDED_INDEXES': [
                'op_scraper.search_indexes.PersonIndexArchive',
                'op_scraper.search_indexes.LawIndexArchive',
                'op_scraper.search_indexes.DebateIndexArchive'
            ]
        },
        'archive': {
            'ENGINE': 'offenesparlament.search_backend.FuzzyElasticsearchSearchEngine',
            'URL': 'http://localhost:9200/',
            'INDEX_NAME': 'archivetest',
            'TIMEOUT': 120,
            'BATCH_SIZE': 50,
            'EXCLUDED_INDEXES': [
                'op_scraper.search_indexes.PersonIndex',
                'op_scraper.search_indexes.LawIndex',
                'op_scraper.search_indexes.DebateIndex'
            ]
        },
    }

class ProductionBase(BaseConfig):
    DEBUG = False
    SECRET_KEY = None
    ALLOWED_HOSTS = ['*']
    BROKER_URL = 'amqp://production_user_rabbitmq:supersecretpw@rabbitmq_vhost:5672//'
    DEBUG_SUBSCRIPTIONS = False

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
                'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            },
        },
        'op_scraper.subscriptions.diff': {
                'handlers': ['console'],
                'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
            
    }

    INSTALLED_APPS = BaseConfig.INSTALLED_APPS + ('raven.contrib.django.raven_compat',)


class StagingBase(ProductionBase):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Import scrapy settings

c = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
old_cd = os.getcwd()
os.chdir(str(c) + '/op_scraper/scraper')
d = os.getcwd()
path.append(d)
os.chdir(old_cd)
d = os.getcwd()
os.environ['SCRAPY_SETTINGS_MODULE'] = 'parlament.settings'


# ignore the following error when using ipython:
#/django/db/backends/sqlite3/base.py:50: RuntimeWarning:
# SQLite received a naive datetime [...] while time zone support is active.

import warnings
import exceptions
warnings.filterwarnings("ignore", category=exceptions.RuntimeWarning,
                        module='django.db.backends.sqlite3.base', lineno=53)
